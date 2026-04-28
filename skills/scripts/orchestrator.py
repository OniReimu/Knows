"""
Knows Orchestrator — agent-callable runtime for the v1.0 sub-skill catalog.

This module implements the dispatch + G5 transport + G7 profile filter + G2'
quality filter + G6 manifest accumulation specified in
`skills/references/dispatch-and-profile.md`. Agents (Claude Code, scripts,
notebooks) import this module instead of executing the workflow steps by hand.

Stdlib-only — no `pip install` needed. Uses `urllib` for HTTP.

Quick examples:

    from orchestrator import dispatch, run_paper_finder, run_sidecar_reader

    # 1. Routing-only — get the decision without executing
    decision = dispatch("discover", {"query_text": "diffusion + privacy"},
                        "ranked_paper_list")
    # → {"action": "route", "skill": "paper-finder", ...}

    # 2. Convenience: paper-finder end-to-end
    result = run_paper_finder("multi-path CoT", top_k=5)
    print(result["table"])           # Markdown table
    print(result["manifest"])        # G6 manifest dict

    # 3. Convenience: sidecar-reader (returns the LLM-call payload to feed your model)
    payload = run_sidecar_reader("knows:vaswani/attention/1.0.0",
                                  "what dataset?")
    # payload contains: system_message, user_message, expected_schema, manifest_seed
    # Agent runs the LLM call itself and parses per consume-prompt.md v1.1
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# ---------------- Constants -----------------

API_BASE = "https://knows.academy/api/proxy"
USER_AGENT = "knows-orchestrator/0.1 (+https://knows.academy)"

PROFILE_RE = re.compile(r"^[a-z_]+@\d+$")

VALID_SLOTS = frozenset([
    "query_text", "rid", "rid_set", "rid_pair",
    "paper_rid", "reviewer_text_or_rid",
    "comparison_axes",
    "latex_dir", "text_blob", "pdf_path",
    "field_patches", "target_rid",
    "q", "question_id",
    "local_path", "local_path_a", "local_path_b",  # v1.0.1: local sidecar files
])

OR_SLOT_PAIRS = [
    frozenset(["latex_dir", "text_blob"]),
    frozenset(["latex_dir", "pdf_path"]),
    frozenset(["text_blob", "pdf_path"]),
    frozenset(["query_text", "rid_set"]),
]

# Routing table mirrors dispatch-and-profile.md §1.5 (canonical, exhaustive).
# Row: (intent_class, required_slots, requested_artifact, skill, multi_row_skill)
ROUTING_TABLE: list[tuple[str, frozenset[str], str, str, bool]] = [
    ("discover", frozenset(["query_text"]), "ranked_paper_list", "paper-finder", True),
    ("discover", frozenset(["query_text"]), "bibtex", "paper-finder", True),
    ("extract", frozenset(["rid", "q"]), "answer_json", "sidecar-reader", True),
    ("extract", frozenset(["local_path", "q"]), "answer_json", "sidecar-reader", True),
    ("synthesize_prose", frozenset(["query_text"]), "related_work_paragraph", "survey-narrative", False),
    ("synthesize_prose", frozenset(["rid_set"]), "related_work_paragraph", "survey-narrative", False),
    ("synthesize_table", frozenset(["rid_set", "comparison_axes"]), "comparison_table", "survey-table", False),
    ("diff", frozenset(["rid_pair"]), "diff_report", "paper-compare", True),
    ("diff", frozenset(["local_path_a", "local_path_b"]), "diff_report", "paper-compare", True),
    ("diff", frozenset(["rid", "local_path_b"]), "diff_report", "paper-compare", True),
    ("critique_generate", frozenset(["paper_rid"]), "review_sidecar", "review-sidecar", False),
    ("critique_respond", frozenset(["paper_rid", "reviewer_text_or_rid"]), "rebuttal_doc", "rebuttal-builder", False),
    ("brief_next_steps", frozenset(["query_text"]), "next_step_brief", "next-step-advisor", False),
    ("contribute", frozenset(["latex_dir"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["text_blob"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["pdf_path"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["latex_dir"]), "lint_report", "sidecar-author", True),
    ("contribute", frozenset(["text_blob"]), "lint_report", "sidecar-author", True),
    ("contribute", frozenset(["pdf_path"]), "lint_report", "sidecar-author", True),
    ("inspect_lineage", frozenset(["rid"]), "version_chain_report", "version-inspector", False),
    ("revise_local", frozenset(["target_rid", "field_patches"]), "diff_and_yaml", "sidecar-reviser", False),
]

# Per-skill quality_policy defaults (matches each sub-skill SKILL.md frontmatter)
QUALITY_POLICIES: dict[str, dict[str, Any]] = {
    "paper-finder": {
        "require_lint_passed": True,
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations"],
        "min_statements": 5,
    },
    "sidecar-reader": {
        "require_lint_passed": True,
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations"],
        "min_statements": 5,
    },
    "sidecar-author": {
        "require_lint_passed": False,  # output IS the artifact
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"],
        "min_statements": 0,
    },
    "paper-compare": {
        "require_lint_passed": True,
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations"],
        "min_statements": 5,
    },
    "version-inspector": {
        "require_lint_passed": True,
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"],
        "min_statements": 0,  # lineage tracing doesn't need rich content
    },
    "sidecar-reviser": {
        "require_lint_passed": True,  # broken sidecars need fixing first, not revising
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"],
        "min_statements": 0,
    },
}

ACCEPTS_PROFILES: dict[str, list[str]] = {
    "paper-finder": ["paper@1"],
    "sidecar-reader": ["paper@1"],
    "sidecar-author": [],   # no hub consumption
    "paper-compare": ["paper@1"],
    "version-inspector": ["paper@1"],
    "sidecar-reviser": ["paper@1"],
}


# ---------------- Manifest (G6) -----------------

@dataclass
class Manifest:
    """G6 working-set provenance manifest. Accumulate fields during a run, dump as dict at end."""
    skill: str
    intent_class: str
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    ended_at: str | None = None
    queries: list[str] = field(default_factory=list)
    returned_rids: list[str] = field(default_factory=list)
    applied_profile_filters: Any = field(default_factory=list)
    applied_quality_policy: dict | None = None
    excluded_missing_profile: list[str] = field(default_factory=list)
    excluded_malformed_profile: list[dict] = field(default_factory=list)
    quality_exclusions: list[dict] = field(default_factory=list)
    fetch_mode_per_rid: dict[str, str] = field(default_factory=dict)
    cache_hits: list[str] = field(default_factory=list)
    abstained: bool = False
    abstained_reason: str | None = None
    knows_api_version: str | None = None
    dispatch_tuple: str | None = None
    model: str | None = None

    def finish(self) -> dict:
        self.ended_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {k: v for k, v in self.__dict__.items() if v not in (None, [], {})}


# ---------------- G5 Transport -----------------

class TransportError(Exception):
    """Raised when G5 transport gives up after retries."""


class NotFoundError(Exception):
    """Raised when API returns 404 — caller should map to rid_not_found.<rid> abstain."""


def _http_get(url: str, *, timeout: int = 15, max_retries: int = 3) -> tuple[bytes, str]:
    """GET with exponential backoff on 429/5xx. Returns (body_bytes, content_type)."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFoundError(f"404: {url}") from e
            if e.code in (429, 500, 502, 503, 504):
                last_err = e
                time.sleep(0.5 * (2 ** attempt))
                continue
            # 4xx other than 404 (e.g. 400 bad request, 414 URI too long, 422) — convert
            # to TransportError with status detail rather than letting urllib traceback escape
            raise TransportError(f"G5: HTTP {e.code} on {url}: {e.reason}") from e
        except urllib.error.URLError as e:
            last_err = e
            time.sleep(0.5 * (2 ** attempt))
        except Exception as e:
            # Defensive: any other transport-layer surprise (socket.timeout, ssl errors,
            # decode errors) becomes a clean TransportError instead of a bare traceback
            raise TransportError(f"G5: unexpected transport error on {url}: {type(e).__name__}: {e}") from e
    raise TransportError(f"G5: retries exhausted for {url}") from last_err


# Canonical v1 enum (spec). Hub ingest hasn't fully migrated yet — most records still
# use the transitional `published` (covers conference+journal). Accept both at the wrapper
# layer to give users access to actual hub data; warn when canonical 4 returns 0.
VENUE_TYPE_ENUM = ("conference", "journal", "preprint", "workshop", "published")


def fetch_search(query: str, *, cursor: str | None = None,
                  limit: int | None = None,
                  offset: int | None = None,
                  year_min: int | None = None,
                  year_max: int | None = None,
                  venue_type: str | None = None,
                  discipline: str | None = None,
                  sort: str | None = None) -> dict:
    """GET /api/proxy/search — returns JSON dict with results, total, next_cursor.

    Server filter support (verified per knows.academy /api/v1/search spec):
      - limit: int, default 20, MAX 100 server-side
      - offset: int, default 0 (alternative to cursor; both supported)
      - cursor: opaque pagination token (server returns next_cursor as offset string)
      - year_min / year_max: integer year range filter (inclusive)
      - venue_type: ONE of {conference, journal, preprint, workshop} per v1 spec
                    (NOT 'published' — that was an earlier alias guess; canonical enum here)
      - discipline: filter exists server-side; sparsely populated on records
      - sort: 'latest' (default per spec) | 'trending' | 'claims'

    Server search behavior (PostgreSQL tsvector with English stemming):
      - plainto_tsquery uses AND-logic across query tokens (all must match)
      - Title is Weight A (highest); venue/discipline/author Weight B; summary/keywords Weight C
      - Broad queries can return 0 hits — agent should fall back to single-token OR fan-out
    """
    if venue_type is not None and venue_type not in VENUE_TYPE_ENUM:
        raise ValueError(f"venue_type must be one of {VENUE_TYPE_ENUM}, got {venue_type!r}")
    params = {"q": query}
    if cursor:
        params["cursor"] = cursor
    if limit is not None:
        params["limit"] = str(min(int(limit), 100))  # server caps at 100
    if offset is not None:
        params["offset"] = str(max(0, int(offset)))
    if year_min is not None:
        params["year_min"] = str(year_min)
    if year_max is not None:
        params["year_max"] = str(year_max)
    if venue_type:
        params["venue_type"] = venue_type
    if discipline:
        params["discipline"] = discipline
    if sort:
        params["sort"] = sort
    url = f"{API_BASE}/search?{urllib.parse.urlencode(params)}"
    body, _ = _http_get(url)
    return json.loads(body)


def fetch_disciplines(view: str = "trending") -> dict:
    """GET /api/proxy/disciplines — browse hub by discipline.

    Returns {groups: [{name, total_papers, total_stmts, subfields: [...]}], total_papers, view}.
    `view` ∈ {'trending', 'claims', 'arxiv'}. Useful as a hub-coverage diagnostic
    before issuing a topic search ("how much is on hub in my area?")."""
    url = f"{API_BASE}/disciplines?view={urllib.parse.quote(view)}"
    body, _ = _http_get(url)
    return json.loads(body)


def run_hub_coverage_check(query: str, *, year_min: int | None = None,
                            venue_type: str | None = None) -> dict:
    """Hub coverage diagnostic.

    Combines /disciplines (hub structure) + per-subfield topic search to give the user
    expectation management BEFORE they invest in next-step-advisor / survey-narrative.

    Returns:
        {
            "query": <q>,
            "hub_total_papers": <int>,
            "topic_total_hits": <int — unfiltered topic search count>,
            "by_discipline": [{group, subfield, full_path, paper_count_subfield, topic_hits_in_subfield}],
            "verdict": "rich" | "moderate" | "thin" | "absent",
            "advice": <str>
        }
    """
    try:
        d = fetch_disciplines("trending")
    except TransportError as e:
        return {"error": "upstream_unavailable_retries_exhausted", "detail": str(e)}
    try:
        # Unfiltered topic search to know corpus-wide hits
        topic_resp = fetch_search(query, limit=1, year_min=year_min, venue_type=venue_type)
        topic_total = topic_resp.get("total", 0)
    except TransportError as e:
        return {"error": "upstream_unavailable_retries_exhausted", "detail": str(e)}

    by_discipline = []
    # For each subfield, probe how many of its papers match the topic
    for group in d.get("groups", []):
        for sub in group.get("subfields", []):
            full_path = sub.get("full_discipline") or f"{group['name']} / {sub['name']}"
            try:
                sub_resp = fetch_search(query, limit=1, discipline=full_path,
                                         year_min=year_min, venue_type=venue_type)
                topic_hits = sub_resp.get("total", 0)
            except TransportError:
                topic_hits = None
            by_discipline.append({
                "group": group["name"],
                "subfield": sub["name"],
                "full_path": full_path,
                "papers_in_subfield": sub.get("paper_count", 0),
                "topic_hits_in_subfield": topic_hits,
            })

    # Sort by topic hits descending; keep top 10 + zero-hit ones for visibility
    by_discipline.sort(key=lambda x: -(x["topic_hits_in_subfield"] or 0))
    nonzero = [b for b in by_discipline if (b["topic_hits_in_subfield"] or 0) > 0]
    top_by_discipline = nonzero[:10]

    # Verdict heuristic
    if topic_total == 0:
        verdict = "absent"; advice = ("Topic returns 0 hits hub-wide. Try broader query or check "
                                       "if it's spelled the way the corpus uses it.")
    elif topic_total < 10:
        verdict = "thin"; advice = (f"Only {topic_total} hits hub-wide for {query!r}. "
                                     "Synthesis/gap-finding will produce thin briefs. "
                                     "Consider broadening or pivoting.")
    elif topic_total < 50:
        verdict = "moderate"; advice = (f"{topic_total} hits hub-wide. Workable for survey-narrative "
                                          "but next-step-advisor will be heuristic; treat as 'starter set' "
                                          "+ supplement with manual search outside hub.")
    else:
        verdict = "rich"; advice = (f"{topic_total} hits hub-wide. Survey/gap workflows should produce "
                                     "high-confidence output; lean on `--sort claims` and `--venue-type "
                                     "published` to filter for quality.")

    return {
        "query": query,
        "hub_total_papers": d.get("total_papers"),
        "topic_total_hits": topic_total,
        "filters_applied": {"year_min": year_min, "venue_type": venue_type},
        "top_subfields_by_topic_hits": top_by_discipline,
        "verdict": verdict,
        "advice": advice,
    }


def fetch_health() -> dict:
    """GET /health — pre-flight hub availability check. Returns {status, service}.

    The /health endpoint may not be deployed on every hub instance; this function
    falls back to a /jobs/stats probe (if that returns 200, hub is operational).
    """
    # Try advertised /health first; fall back to /jobs/stats if not deployed
    try:
        body, _ = _http_get("https://knows.academy/health")
        return json.loads(body)
    except (TransportError, urllib.error.HTTPError, NotFoundError):
        pass
    # Fallback: jobs/stats is verified-live and equivalent for "is hub up?"
    try:
        body, _ = _http_get(f"{API_BASE}/jobs/stats")
        json.loads(body)  # validate parses
        return {"status": "ok", "service": "knows-academy-backend",
                "probed_via": "fallback:/jobs/stats — /health endpoint not deployed yet"}
    except Exception as e:
        return {"status": "down", "detail": str(e)[:200]}


def fetch_sidecar(rid: str) -> dict:
    """GET /api/proxy/sidecars/<rid> — returns full KnowsRecord JSON. URL-encodes rid."""
    enc = urllib.parse.quote(rid, safe='')
    url = f"{API_BASE}/sidecars/{enc}"
    body, _ = _http_get(url)
    return json.loads(body)


def cite_key(record_or_rid: str | dict) -> str:
    """Derive a BibTeX-style citation key from a hub record, search hit, or RID.

    Returns `{firstauthor_lastname}{year}` lowercased, with non-alphanumerics stripped
    (e.g. "FlashAttention-4" by Dao 2023 → "dao2023"). Falls back gracefully:

    - If a search hit dict is given (no `authors` field) and no full sidecar fetch is
      possible, derives from `venue` string (e.g. "ICLR 2025") + RID slug.
    - If a RID string is given, fetches the full sidecar (one network round-trip).
    - If first-author or year is unrecoverable, returns the RID's last slug component.

    Use this helper inside synthesis sub-skills (survey-narrative, survey-table,
    rebuttal-builder) to avoid re-implementing the same parsing per skill.
    """
    # Resolve to a dict-shaped record
    if isinstance(record_or_rid, str):
        rec = fetch_sidecar(record_or_rid)
    else:
        rec = record_or_rid

    rid = rec.get("record_id") or rec.get("rid") or ""

    def _slug_fallback() -> str:
        # last path segment minus version: knows:foo/bar-baz/1.0.0 → "bar-baz" → "barbaz"
        if not rid:
            return "anonymous"
        parts = rid.split("/")
        if len(parts) >= 2:
            slug = parts[-2]
            return re.sub(r"[^a-z0-9]", "", slug.lower()) or "anonymous"
        return "anonymous"

    # Year: try root, then artifacts[0], then parse from venue string
    year = rec.get("year")
    if not year:
        artifacts = rec.get("artifacts") or []
        if artifacts and isinstance(artifacts, list):
            year = artifacts[0].get("year")
    if not year:
        venue = rec.get("venue") or ""
        m = re.search(r"\b(19|20)\d{2}\b", venue)
        if m:
            year = int(m.group(0))
    year_str = str(year) if year else ""

    # First-author lastname: try root authors, then artifacts[0].authors
    authors = rec.get("authors") or []
    if not authors:
        artifacts = rec.get("artifacts") or []
        if artifacts and isinstance(artifacts, list):
            authors = artifacts[0].get("authors") or []
    if authors and isinstance(authors, list):
        first = authors[0]
        if isinstance(first, dict):
            name = first.get("name") or first.get("family") or ""
        else:
            name = str(first)
        # Take last whitespace-delimited token as the lastname
        lastname = name.strip().split()[-1] if name.strip() else ""
        lastname_clean = re.sub(r"[^a-z0-9]", "", lastname.lower())
        if lastname_clean and year_str:
            return f"{lastname_clean}{year_str}"
        if lastname_clean:
            return lastname_clean

    # Last-resort fallback: RID slug + optional year
    slug = _slug_fallback()
    return f"{slug}{year_str}" if year_str else slug


# Small synonym map for the topical-relevance precheck. Keep narrow — only common
# tight aliases that an agent shouldn't have to re-derive. NOT a general thesaurus.
_TOPICAL_SYNONYMS: dict[str, tuple[str, ...]] = {
    "dp": ("differential privacy", "differentially private", "dp-sgd"),
    "differential privacy": ("dp", "differentially private", "dp-sgd"),
    "llm": ("large language model", "language model"),
    "large language model": ("llm", "language model"),
    "rlhf": ("reinforcement learning from human feedback",),
    "reinforcement learning from human feedback": ("rlhf",),
    "moe": ("mixture of experts", "mixture-of-experts"),
    "mixture of experts": ("moe", "mixture-of-experts"),
    "kv cache": ("kv-cache", "key-value cache"),
}


def _expand_term(term: str) -> tuple[str, ...]:
    """Return the term plus any narrow synonyms (lowercased)."""
    t = term.lower().strip()
    return (t,) + _TOPICAL_SYNONYMS.get(t, ())


def parse_intersection_query(query: str) -> tuple[str, str] | None:
    """Detect intersection-typed queries and return (term_A, term_B) or None.

    Triggers on common conjunction patterns: "X and Y", "X & Y", "X x Y",
    "X for Y", "X in Y", "X applied to Y". Returns None for single-concept
    queries (which skip the topical-relevance precheck per §4.1).
    """
    q = query.strip().lower()
    # Connector patterns ordered most-to-least specific
    for sep in (" applied to ", " against ", " for ", " in ", " on ", " and ", " & ", " × ", " x "):
        if sep in q:
            parts = q.split(sep, 1)
            a, b = parts[0].strip(), parts[1].strip()
            if a and b and len(a) >= 2 and len(b) >= 2:
                return a, b
    return None


def topical_grounding_count(statements: list[dict], term_a: str, term_b: str) -> int:
    """Count statements whose `text` field contains lexical evidence of BOTH terms.

    Used by next-step-advisor §4.1 precheck: for an intersection query A × B,
    pre-empt cross-paper speculation by requiring at least one statement that
    actually names both sides of the intersection. Synonyms from the narrow
    `_TOPICAL_SYNONYMS` map are accepted (e.g. "DP" ↔ "differential privacy").
    """
    a_variants = _expand_term(term_a)
    b_variants = _expand_term(term_b)
    n = 0
    for stmt in statements:
        text = (stmt.get("text") or "").lower()
        if not text:
            continue
        if any(va in text for va in a_variants) and any(vb in text for vb in b_variants):
            n += 1
    return n


def fetch_partial(rid: str, section: str) -> Any:
    """GET /api/proxy/partial?record_id=<rid>&section=<name>.
    For section in {statements, evidence, relations}: returns dict {record_id, items}.
    For section == citation: returns raw BibTeX text (str)."""
    enc = urllib.parse.quote(rid, safe='')
    url = f"{API_BASE}/partial?record_id={enc}&section={section}"
    body, _ = _http_get(url)
    if section == "citation":
        return body.decode("utf-8", errors="replace")
    return json.loads(body)


# ---------------- G7 + G2' Filters -----------------

def profile_filter_reason(record: dict, allowed_profiles: set[str]) -> str | None:
    """Return None if record passes G7 filter; else reason code per §2.3."""
    prof = record.get("profile")
    if prof is None:
        return None if "unknown" in allowed_profiles else "missing"
    if not PROFILE_RE.match(prof):
        return "malformed"
    if prof not in allowed_profiles:
        return "not_in_allowed"
    return None


def quality_filter_reason(record: dict, policy: dict) -> dict | None:
    """Return None if record passes G2'; else dict {policy_field, actual} per §2.2."""
    if policy.get("require_lint_passed") and not record.get("lint_passed", False):
        return {"policy_field": "require_lint_passed", "actual": record.get("lint_passed", False)}
    cov = record.get("coverage_statements")
    if cov not in policy.get("allowed_coverage", []):
        return {"policy_field": "allowed_coverage", "actual": cov}
    stmt_count = record.get("stats", {}).get("stmt_count", 0)
    if stmt_count < policy.get("min_statements", 0):
        return {"policy_field": "min_statements", "actual": stmt_count}
    return None


def filter_records(records: list[dict], skill: str, manifest: Manifest) -> list[dict]:
    """Apply G7 + G2' filters per skill's frontmatter. Mutates manifest with exclusions."""
    allowed = set(ACCEPTS_PROFILES.get(skill, []))
    policy = QUALITY_POLICIES.get(skill, {})
    kept = []
    for r in records:
        prof_reason = profile_filter_reason(r, allowed) if allowed else None
        if prof_reason == "missing":
            manifest.excluded_missing_profile.append(r.get("record_id", "?"))
            continue
        if prof_reason == "malformed":
            manifest.excluded_malformed_profile.append(
                {"rid": r.get("record_id", "?"), "raw_value": r.get("profile")})
            continue
        if prof_reason == "not_in_allowed":
            manifest.excluded_malformed_profile.append(
                {"rid": r.get("record_id", "?"), "raw_value": r.get("profile"),
                 "reason": "not_in_allowed"})
            continue
        q_reason = quality_filter_reason(r, policy) if policy else None
        if q_reason is not None:
            manifest.quality_exclusions.append({"rid": r.get("record_id", "?"), **q_reason})
            continue
        kept.append(r)
    manifest.applied_profile_filters = list(allowed) if allowed else []
    manifest.applied_quality_policy = policy if policy else None
    return kept


# ---------------- Dispatch (§1.5) -----------------

def _match_rows(intent_class: str, slot_keys: set[str],
                requested_artifact: str | None) -> list[tuple]:
    matches = []
    for row in ROUTING_TABLE:
        ic, req_slots, art, _, _ = row
        if ic != intent_class:
            continue
        if not req_slots.issubset(slot_keys):
            continue
        if requested_artifact is not None and requested_artifact != art:
            continue
        matches.append(row)
    return matches


def dispatch(intent_class: str | None, slots: dict,
             requested_artifact: str | None) -> dict:
    """Resolve a dispatch tuple to one of: route / clarify / abstain.
    See dispatch-and-profile.md §1.5 + §4 + §5."""
    if not intent_class:
        return {"action": "abstain", "reason": "unknown_dispatch_tuple"}
    slot_keys = set(slots.keys())
    unknown = slot_keys - VALID_SLOTS
    if unknown:
        return {"action": "abstain", "reason": f"invalid_slot_type.{sorted(unknown)[0]}"}
    for pair in OR_SLOT_PAIRS:
        if pair.issubset(slot_keys):
            offender = sorted(pair)[1]
            return {"action": "abstain", "reason": f"invalid_slot_type.{offender}"}
    matches = _match_rows(intent_class, slot_keys, requested_artifact)
    if not matches:
        return {"action": "abstain", "reason": "unknown_dispatch_tuple"}
    if len(matches) == 1:
        m = matches[0]
        return {"action": "route", "skill": m[3], "row": m}
    candidates = sorted({m[3] for m in matches})
    gap = "requested_artifact" if requested_artifact is None else "intent_class"
    return {"action": "clarify", "candidates": candidates, "gap": gap}


# ---------------- Sub-skill convenience runners -----------------

def run_paper_finder(query: str, *, top_k: int = 20,
                     artifact: str = "ranked_paper_list",
                     year_min: int | None = None,
                     year_max: int | None = None,
                     venue_type: str | None = None,
                     venue: str | None = None,
                     discipline: str | None = None,
                     sort: str | None = None,
                     or_fallback: bool = True,
                     page_limit: int | None = None) -> dict:
    """End-to-end paper-finder: dispatch → fetch → filter → format. Returns {artifact, manifest}.

    Server-side filters passed through to /api/proxy/search:
      - year_min / year_max — integer range
      - venue_type — 'published' | 'preprint'
      - sort — 'latest' | 'trending' | 'claims' (claims sorts by stmt_count, proxy for richness)
    Client-side filters applied after fetch:
      - venue — substring match against `venue` field (server doesn't filter by exact name)
    Query handling:
      - or_fallback (default True): if AND-logic search returns 0 hits AND query has multi tokens,
        retry by issuing one search per token and unioning results (capped at top_k).
    """
    decision = dispatch("discover", {"query_text": query}, artifact)
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    manifest = Manifest(skill=skill, intent_class="discover", queries=[query],
                        dispatch_tuple=f"(discover,{{query_text}},{artifact})")
    # Quality default: --sort claims is already a curation-biased mode (richest sidecars),
    # so default venue_type to 'published' unless user explicitly set one. Without this,
    # claims sort gets dominated by generated arxiv autoextracts, hurting lit-map quality.
    auto_published = (sort == "claims" and venue_type is None)
    if auto_published:
        venue_type = "published"
        sys.stderr.write("(auto-applied --venue-type published because --sort claims; "
                         "pass --venue-type preprint or --venue-type conference to override)\n")
    fetch_kwargs = {"year_min": year_min, "year_max": year_max,
                    "venue_type": venue_type, "discipline": discipline, "sort": sort}
    fetch_kwargs = {k: v for k, v in fetch_kwargs.items() if v is not None}

    # Paginate via limit/offset until we have enough RAW hits to feed downstream filters.
    # Server limit max=100; over-fetch up to 5x top_k (cap 500) to give filters headroom.
    if page_limit is None:
        page_limit = min(100, max(top_k, 20))
    else:
        page_limit = min(100, max(1, page_limit))
    over_fetch_target = min(top_k * 5, 500)
    raw_hits: list[dict] = []
    seen_rids: set[str] = set()
    offset = 0
    try:
        while len(raw_hits) < over_fetch_target:
            resp = fetch_search(query, limit=page_limit, offset=offset, **fetch_kwargs)
            page = resp.get("results", [])
            if not page:
                break
            for h in page:
                rid = h.get("record_id")
                if rid and rid not in seen_rids:
                    seen_rids.add(rid)
                    raw_hits.append(h)
            if len(page) < page_limit:
                break  # last page
            offset += page_limit
    except TransportError as e:
        if not raw_hits:
            manifest.abstained = True
            manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
            return {"abstained": True, "reason": manifest.abstained_reason,
                    "detail": str(e), "manifest": manifest.finish()}
        # partial results: continue with what we have

    # OR-fallback: if AND-logic returned 0 and query is multi-token, fan out.
    # Exhaust ALL tokens before concluding empty (don't break on first hit).
    if not raw_hits and or_fallback:
        tokens = [t for t in query.split() if len(t) > 2]
        if len(tokens) > 1:
            manifest.queries.extend(tokens)
            for tok in tokens:
                try:
                    sub_resp = fetch_search(tok, limit=page_limit, **fetch_kwargs)
                except TransportError:
                    continue
                for hit in sub_resp.get("results", []):
                    rid = hit.get("record_id")
                    if rid and rid not in seen_rids:
                        seen_rids.add(rid)
                        raw_hits.append(hit)
                # Don't break early — exhaust all tokens so post-filter set has headroom

    # Client-side venue filter (substring match — server doesn't support exact venue name filter)
    venue_filter_dropped = 0
    if venue:
        venue_lower = venue.lower()
        before = len(raw_hits)
        raw_hits = [r for r in raw_hits if venue_lower in (r.get("venue") or "").lower()]
        venue_filter_dropped = before - len(raw_hits)

    # Title-rerank for canonical short-name queries.
    # Server tsvector can under-weight exact title matches vs longer papers whose
    # abstract mentions the term. Boost: exact-title > startswith > substring word-bound.
    # Narrow trigger: query is single token, alphanumeric, len ≥ 4 (e.g. "FlashAttention",
    # "PagedAttention", "H2O", "StreamingLLM"). Multi-word queries are unaffected.
    q_stripped = query.strip()
    if raw_hits and " " not in q_stripped and len(q_stripped) >= 4 and q_stripped.replace("-", "").isalnum():
        q_norm = q_stripped.lower()
        # Discriminator: rank 2 = title BEGINS with the canonical name followed by any
        # non-word char (catches "FlashAttention-4", "FlashAttention:", "FlashAttention 2").
        # rank 1 = mentioned mid-title ("survey-style"). The canonical paper near-always
        # begins its title with the name; mentions show up later.
        def _title_rank(rec: dict) -> int:
            title = (rec.get("title") or "").lower()
            if not title:
                return 0
            if title == q_norm:
                return 3
            if re.match(rf"{re.escape(q_norm)}(\W|$)", title):
                return 2
            # Word-bounded substring (avoid "FlashAttentioner" matching "FlashAttention")
            if re.search(rf"\b{re.escape(q_norm)}\b", title):
                return 1
            return 0
        # Stable sort: title-rank desc, original order preserved within ties.
        raw_hits.sort(key=_title_rank, reverse=True)

    hits = raw_hits[:top_k]
    manifest.returned_rids = [r.get("record_id", "?") for r in hits]
    # Distinguish 3 distinct empty-set causes so the abstain reason is diagnostic
    if not raw_hits:
        manifest.abstained = True
        if venue_filter_dropped > 0:
            manifest.abstained_reason = "empty_working_set_after_venue_filter"
            detail = f"client-side venue filter {venue!r} dropped all {venue_filter_dropped} server results — try a different venue substring or remove --venue"
        else:
            manifest.abstained_reason = "upstream_zero_hits"
            detail = (f"knows.academy /search returned 0 results for query={query!r}"
                      + (f" with filters year_min={year_min} year_max={year_max} venue_type={venue_type} discipline={discipline}" if any([year_min, year_max, venue_type, discipline]) else "")
                      + "; try a broader query OR loosen filters")
        return {"abstained": True, "reason": manifest.abstained_reason,
                "detail": detail, "manifest": manifest.finish()}
    kept = filter_records(hits, skill, manifest)
    if not kept:
        manifest.abstained = True
        manifest.abstained_reason = ("empty_working_set_after_quality_filter"
                                      if manifest.quality_exclusions and not manifest.excluded_missing_profile
                                      else "empty_working_set_after_profile_filter")
        return {"abstained": True, "reason": manifest.abstained_reason,
                "detail": f"knows.academy returned {len(raw_hits)} hits but all dropped by skill filter",
                "manifest": manifest.finish()}
    if artifact == "ranked_paper_list":
        # P1b: include RID column so users don't have to drop into Python to extract them
        lines = ["| # | RID | Title | Venue | Year | Stmts | Lint |",
                 "|---|---|---|---|---|---|---|"]
        kept_rids = []
        for i, r in enumerate(kept, 1):
            rid = r.get("record_id", "?")
            kept_rids.append(rid)
            title = (r.get("title") or "-")[:60]
            venue = r.get("venue") or "-"
            year = r.get("year") or "-"
            stmts = r.get("stats", {}).get("stmt_count", 0)
            lint = "✓" if r.get("lint_passed") else "✗"
            lines.append(f"| {i} | `{rid}` | {title} | {venue} | {year} | {stmts} | {lint} |")
        return {"table": "\n".join(lines), "manifest": manifest.finish(), "kept_rids": kept_rids}
    if artifact == "bibtex":
        bibs = []
        for r in kept:
            rid = r.get("record_id")
            if not rid:
                continue
            try:
                bibs.append(fetch_partial(rid, "citation"))
                manifest.fetch_mode_per_rid[rid] = "partial:citation"
            except TransportError:
                pass
        return {"bibtex": "\n\n".join(bibs), "manifest": manifest.finish()}
    return {"error": f"unsupported artifact: {artifact}", "manifest": manifest.finish()}


def run_sidecar_reader(rid: str | None = None, q: str | None = None, *,
                        local_path: str | None = None,
                        question_id: str | None = None) -> dict:
    """Prepare the consume-prompt v1.1 LLM call payload.

    Source: either `rid` (hub fetch) OR `local_path` (read local .knows.yaml file).
    Exactly one required. Local mode supports the "ask questions about a
    freshly-generated sidecar" workflow before publishing to the hub.

    Returns dict with 'sidecar', 'qid', 'user_message_data', 'manifest_seed'.
    Agent does the LLM call using consume-prompt.md verbatim and parses the JSON.
    """
    if not q:
        return {"abstained": True, "reason": "missing_required_input.q"}
    if (rid is None) == (local_path is None):
        return {"abstained": True, "reason": "invalid_slot_type.local_path",
                "detail": "exactly one of rid or local_path required"}

    if rid:
        slots = {"rid": rid, "q": q}
        source_label = rid
        dispatch_tuple = "(extract,{rid,q},answer_json)"
    else:
        slots = {"local_path": local_path, "q": q}
        source_label = local_path
        dispatch_tuple = "(extract,{local_path,q},answer_json)"

    decision = dispatch("extract", slots, "answer_json")
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    manifest = Manifest(skill=skill, intent_class="extract",
                        returned_rids=[source_label],
                        dispatch_tuple=dispatch_tuple)
    qid = question_id or hashlib.sha1(q.encode()).hexdigest()[:8]

    if local_path:
        # Local-file mode — read YAML from disk
        try:
            import yaml
            from pathlib import Path
            p = Path(local_path)
            if not p.exists():
                manifest.abstained = True
                manifest.abstained_reason = "invalid_slot_type.local_path"
                return {"abstained": True, "reason": manifest.abstained_reason,
                        "detail": f"{local_path} does not exist", "manifest": manifest.finish()}
            sidecar = yaml.safe_load(p.read_text())
        except Exception as e:
            manifest.abstained = True
            manifest.abstained_reason = "skill_runtime_exception.LocalSidecarLoadFailed"
            return {"abstained": True, "reason": manifest.abstained_reason,
                    "detail": str(e), "manifest": manifest.finish()}
        manifest.fetch_mode_per_rid[local_path] = "local_file"
    else:
        # Hub-fetch mode (original behavior)
        try:
            sidecar = fetch_sidecar(rid)
        except NotFoundError:
            manifest.abstained = True
            manifest.abstained_reason = f"rid_not_found.{rid}"
            return {"abstained": True, "reason": manifest.abstained_reason, "manifest": manifest.finish()}
        except TransportError as e:
            manifest.abstained = True
            manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
            return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}
        manifest.fetch_mode_per_rid[rid] = "full"

    kept = filter_records([{**sidecar,
                            "stats": {"stmt_count": len(sidecar.get("statements", []))},
                            "coverage_statements": sidecar.get("coverage", {}).get("statements"),
                            "lint_passed": True,  # local files trusted; hub records lint-pass by construction
                            "record_id": source_label}], skill, manifest)
    if not kept:
        manifest.abstained = True
        manifest.abstained_reason = ("empty_working_set_after_quality_filter"
                                      if manifest.quality_exclusions
                                      else "empty_working_set_after_profile_filter")
        return {"abstained": True, "reason": manifest.abstained_reason,
                "manifest": manifest.finish()}
    return {
        "qid": qid,
        "sidecar": sidecar,                     # G1: agent must wrap in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>
        "user_message_data": {                  # values to plug into consume-prompt.md v1.1 user template
            "question_id": qid,
            "q": q,
            "sidecar_json": json.dumps(sidecar),
        },
        "consume_prompt_path": "skills/references/consume-prompt.md",
        "manifest_seed": manifest,              # call .finish() after LLM step + add `model` field
        "instructions": ("Load consume-prompt.md v1.1 system+user templates verbatim, "
                         "wrap sidecar_json in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>, "
                         "fill user_message_data, call your LLM, parse JSON per v1.1 schema "
                         "(status ∈ {answer,partial,abstain,supported,ambiguous,not_found}), "
                         "set manifest.model and call manifest.finish()."),
    }


def run_sidecar_author_pdf(pdf_path: str, *, output_path: str | None = None,
                            include_cited: bool = True) -> dict:
    """Prepare the sidecar-author Path F (PDF) workflow for the agent.

    Returns a dict the agent uses to: (1) read the PDF multimodally + apply
    gen-prompt.md verbatim → produce raw YAML, (2) call run_sidecar_author_postgen()
    on the raw output to run sanitize/lint/verify_metadata.

    Note: the multimodal LLM call is agent-mediated (orchestrator can't make
    multimodal calls without a per-platform integration). This runner handles
    everything else: dispatch routing, output path management, and the
    post-generation pipeline.
    """
    from pathlib import Path
    pdf_p = Path(pdf_path)
    if not pdf_p.exists():
        return {"abstained": True, "reason": f"invalid_slot_type.pdf_path",
                "detail": f"{pdf_path} does not exist"}
    if not pdf_p.suffix.lower() == ".pdf":
        return {"abstained": True, "reason": f"invalid_slot_type.pdf_path",
                "detail": f"{pdf_path} is not a .pdf file"}
    decision = dispatch("contribute", {"pdf_path": pdf_path}, "knows_yaml")
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    out = output_path or str(pdf_p.with_suffix(".knows.yaml"))
    manifest = Manifest(skill=skill, intent_class="contribute",
                        dispatch_tuple="(contribute,{pdf_path},knows_yaml)")
    return {
        "skill": skill,
        "pdf_path": pdf_path,
        "output_path": out,
        "include_cited": include_cited,
        "gen_prompt_path": "skills/references/gen-prompt.md",
        "post_gen_runner": "run_sidecar_author_postgen",
        "manifest_seed": manifest,
        "instructions": (
            f"1. Read {pdf_path} via your multimodal LLM capability.\n"
            f"2. Load skills/references/gen-prompt.md verbatim — system + user templates.\n"
            f"3. Generate complete KnowsRecord YAML following ALL rules in gen-prompt.md.\n"
            f"4. Save raw output to a tmp file, then call:\n"
            f"   from orchestrator import run_sidecar_author_postgen\n"
            f"   result = run_sidecar_author_postgen(<tmp_yaml_path>, '{out}', include_cited={include_cited})\n"
            f"5. result['lint_passed'] indicates 0-error gate; result['enriched'] counts auto-enrichments."
        ),
    }


def run_sidecar_author_postgen(raw_yaml_path: str, output_path: str, *,
                                 include_cited: bool = True) -> dict:
    """Post-generation pipeline: sanitize → lint → verify_metadata (+ optional --include-cited).

    Wraps the existing scripts/sanitize.py + lint.py + verify_metadata.py via subprocess.
    Returns dict with lint_passed, lint_errors, lint_warnings, verify_issues, enriched_count.
    """
    import subprocess
    from pathlib import Path
    raw = Path(raw_yaml_path)
    out = Path(output_path)
    if not raw.exists():
        return {"error": f"raw YAML {raw_yaml_path} does not exist"}
    scripts_dir = Path(__file__).parent
    # 1. Sanitize (always — handles markdown fences / XML tag artifacts)
    san = subprocess.run(["python3", str(scripts_dir / "sanitize.py"), str(raw), "-o", str(out)],
                          capture_output=True, text=True)
    sanitized = san.returncode == 0
    # 2. Lint (must pass with 0 errors)
    lint = subprocess.run(["python3", str(scripts_dir / "lint.py"), str(out)],
                           capture_output=True, text=True)
    lint_out = lint.stdout
    lint_passed = "PASS:" in lint_out and "0 errors" in lint_out
    n_warn = lint_out.count("WARN:")
    # 3. Verify metadata (with optional --include-cited)
    verify_args = ["python3", str(scripts_dir / "verify_metadata.py"), str(out)]
    if include_cited:
        verify_args.append("--include-cited")
    verify = subprocess.run(verify_args, capture_output=True, text=True)
    verify_out = verify.stdout
    verify_passed = "PASS:" in verify_out and "0 issues" in verify_out
    enriched = verify_out.count("ENRICHED ")
    return {
        "output_path": str(out),
        "sanitized": sanitized,
        "lint_passed": lint_passed,
        "lint_warnings": n_warn,
        "lint_output": lint_out,
        "verify_passed": verify_passed,
        "verify_output": verify_out,
        "enriched_count": enriched,
        "ready_to_publish": lint_passed and verify_passed,
    }


# ---------------- P1: paper-compare -----------------

_STOPWORDS = frozenset("""a an the of in on at for to from with by and or but is are was were
be been being have has had do does did this that these those it its as if then""".split())


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation (keep alphanum + dash), drop stopwords."""
    import re
    toks = re.findall(r"[a-z0-9-]+", text.lower())
    return {t for t in toks if t not in _STOPWORDS and len(t) > 1}


def _jaccard(a: str, b: str) -> float:
    """Jaccard similarity over normalized token sets. Stdlib-only proxy for cosine."""
    sa, sb = _tokenize(a), _tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _load_sidecar_either(source: str) -> tuple[dict, str]:
    """Load a sidecar from EITHER a hub RID OR a local file path.
    Returns (sidecar_dict, fetch_mode) where fetch_mode ∈ {"full", "local_file"}.
    Heuristic: source starts with "knows:" → hub; else → local file path.
    Raises NotFoundError / TransportError / FileNotFoundError as appropriate."""
    if source.startswith("knows:"):
        return fetch_sidecar(source), "full"
    import yaml
    from pathlib import Path
    p = Path(source)
    if not p.exists():
        raise FileNotFoundError(f"local path does not exist: {source}")
    return yaml.safe_load(p.read_text()), "local_file"


def run_paper_compare(rid_a: str | None = None, rid_b: str | None = None, *,
                       local_path_a: str | None = None,
                       local_path_b: str | None = None,
                       similarity_threshold: float = 0.5,
                       match_method: str = "llm_judge") -> dict:
    """End-to-end paper-compare per references/paper-compare.md contract.

    Sources: each side independently from hub (rid_a/rid_b) OR local file
    (local_path_a/local_path_b). Mixed mode supported (e.g. rid_a + local_path_b).

    `match_method`:
      - "llm_judge" (default, more accurate): runs text_overlap with permissive
        threshold to find candidates, then returns an `llm_judge_payload` field
        with the candidate pairs + system/user prompts for the agent to call
        its LLM. Agent should: (1) call its LLM with the payload, (2) parse
        boolean judgments per pair, (3) call `finalize_paper_compare(result,
        judgments)` to merge confirmed pairs into shared_claims.
        Reason for the default: text_overlap returned 0 shared pairs on
        obviously-related papers (e.g. DuoAttention vs KeyDiff both define
        "attention sinks") because terminology drifts across papers.
      - "text_overlap" (deterministic, no LLM): Jaccard over normalized
        token sets; pairs with similarity ≥ similarity_threshold are shared.
        Use when you want a one-shot deterministic answer without a follow-up
        LLM call (e.g. CI smoke tests).
    """
    side_a = rid_a or local_path_a
    side_b = rid_b or local_path_b
    if not side_a or not side_b:
        return {"abstained": True, "reason": "missing_required_input.rid_pair",
                "detail": "need exactly one of (rid_a|local_path_a) AND one of (rid_b|local_path_b)"}
    if side_a == side_b:
        return {"abstained": True, "reason": "invalid_slot_type.rid_pair",
                "detail": "self-diff is degenerate"}
    if rid_a and local_path_a:
        return {"abstained": True, "reason": "invalid_slot_type.local_path_a",
                "detail": "supply rid_a OR local_path_a, not both"}
    if rid_b and local_path_b:
        return {"abstained": True, "reason": "invalid_slot_type.local_path_b",
                "detail": "supply rid_b OR local_path_b, not both"}

    # Construct the canonical dispatch tuple based on which slots are present
    if rid_a and rid_b:
        slots = {"rid_pair": (rid_a, rid_b)}
        dispatch_tuple = "(diff,{rid_pair},diff_report)"
    elif local_path_a and local_path_b:
        slots = {"local_path_a": local_path_a, "local_path_b": local_path_b}
        dispatch_tuple = "(diff,{local_path_a,local_path_b},diff_report)"
    else:
        # Mixed: rid_a + local_path_b OR local_path_a + rid_b — normalize to (rid, local_path_b) per §1.5
        if local_path_a and rid_b:
            rid_a, local_path_b = rid_b, local_path_a  # swap so rid_a is the hub side
            side_a, side_b = rid_a, local_path_b
        slots = {"rid": rid_a, "local_path_b": local_path_b}
        dispatch_tuple = "(diff,{rid,local_path_b},diff_report)"

    decision = dispatch("diff", slots, "diff_report")
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    manifest = Manifest(skill=skill, intent_class="diff",
                        dispatch_tuple=dispatch_tuple,
                        returned_rids=[side_a, side_b])

    try:
        sa, mode_a = _load_sidecar_either(side_a)
    except NotFoundError:
        manifest.abstained = True
        manifest.abstained_reason = f"rid_not_found.{side_a}"
        return {"abstained": True, "reason": manifest.abstained_reason, "manifest": manifest.finish()}
    except FileNotFoundError as e:
        manifest.abstained = True
        manifest.abstained_reason = "invalid_slot_type.local_path_a"
        return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}
    except TransportError as e:
        manifest.abstained = True
        manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
        return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}

    try:
        sb, mode_b = _load_sidecar_either(side_b)
    except NotFoundError:
        manifest.abstained = True
        manifest.abstained_reason = f"rid_not_found.{side_b}"
        return {"abstained": True, "reason": manifest.abstained_reason, "manifest": manifest.finish()}
    except FileNotFoundError as e:
        manifest.abstained = True
        manifest.abstained_reason = "invalid_slot_type.local_path_b"
        return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}
    except TransportError as e:
        manifest.abstained = True
        manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
        return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}

    manifest.fetch_mode_per_rid = {side_a: mode_a, side_b: mode_b}

    # G7 + G2' on both records (local files trusted; hub records lint-pass by construction)
    candidates = []
    for label, sc in [(side_a, sa), (side_b, sb)]:
        candidates.append({**sc, "stats": {"stmt_count": len(sc.get("statements", []))},
                           "coverage_statements": sc.get("coverage", {}).get("statements"),
                           "lint_passed": True, "record_id": label})
    kept = filter_records(candidates, "paper-compare", manifest)  # use this skill's own policy entry
    if len(kept) != 2:
        manifest.abstained = True
        manifest.abstained_reason = ("empty_working_set_after_quality_filter"
                                      if manifest.quality_exclusions
                                      else "empty_working_set_after_profile_filter")
        return {"abstained": True, "reason": manifest.abstained_reason,
                "manifest": manifest.finish()}

    # Compute shared/divergent/contradictions/shared_citations
    a_stmts = sa.get("statements", []); b_stmts = sb.get("statements", [])
    shared, used_a, used_b = [], set(), set()
    pairs = sorted(
        ((_jaccard(a["text"], b["text"]), i, j)
         for i, a in enumerate(a_stmts) for j, b in enumerate(b_stmts)),
        reverse=True)
    candidate_pairs_for_judge = []  # only populated in llm_judge mode
    # llm_judge mode: take top-30 candidates by Jaccard (any score, even 0.0)
    # so the LLM has enough material to judge semantic equivalence
    # (Jaccard misses paraphrase / synonym pairs that LLM catches).
    LLM_JUDGE_MAX_CANDIDATES = 30
    for sim, i, j in pairs:
        if match_method == "llm_judge":
            if len(candidate_pairs_for_judge) >= LLM_JUDGE_MAX_CANDIDATES:
                break
            # Defer the keep/reject decision to the LLM; record candidate (no threshold)
            candidate_pairs_for_judge.append({
                "candidate_id": f"pair_{len(candidate_pairs_for_judge)}",
                "stmt_a_id": a_stmts[i]["id"],
                "stmt_a_text": a_stmts[i]["text"],
                "stmt_b_id": b_stmts[j]["id"],
                "stmt_b_text": b_stmts[j]["text"],
                "text_overlap_score": round(sim, 3),
            })
            continue  # don't lock used_a/used_b yet — LLM may reject this pair
        # text_overlap mode: enforce threshold
        if sim < similarity_threshold:
            break
        if i in used_a or j in used_b:
            continue
        shared.append({
            "stmt_a_id": a_stmts[i]["id"], "stmt_b_id": b_stmts[j]["id"],
            "similarity_score": round(sim, 3), "match_method": "text_overlap",
            "shared_text_summary": a_stmts[i]["text"][:200],
        })
        used_a.add(i); used_b.add(j)

    DIVERGENT_TYPES = {"claim", "method", "limitation"}
    only_in_a = [{"stmt_id": s["id"], "text": s["text"], "type": s["statement_type"]}
                 for i, s in enumerate(a_stmts)
                 if i not in used_a and s.get("statement_type") in DIVERGENT_TYPES]
    only_in_b = [{"stmt_id": s["id"], "text": s["text"], "type": s["statement_type"]}
                 for j, s in enumerate(b_stmts)
                 if j not in used_b and s.get("statement_type") in DIVERGENT_TYPES]

    CONTRA_PREDS = {"challenged_by", "supersedes", "retracts"}
    contradictions = []
    cross_skipped = 0
    for src_rid, src_sc, other_rid in [(side_a, sa, side_b), (side_b, sb, side_a)]:
        for rel in src_sc.get("relations", []):
            if rel.get("predicate") not in CONTRA_PREDS:
                continue
            obj = rel.get("object_ref", "")
            # Cross-record qualifier: "knows:rid#stmt:foo"
            if "#" in obj and obj.startswith(other_rid):
                contradictions.append({
                    "subject_rid": src_rid, "subject_stmt_id": rel.get("subject_ref"),
                    "predicate": rel["predicate"],
                    "object_rid": other_rid, "object_stmt_id": obj.split("#")[1],
                    "evidence_anchor": rel.get("id"),
                })
            elif obj.startswith("knows:") and "#" in obj:
                cross_skipped += 1  # cross-profile or other-record skip

    a_cited = [a for a in sa.get("artifacts", []) if a.get("role") == "cited"]
    b_cited = [a for a in sb.get("artifacts", []) if a.get("role") == "cited"]
    # Match on art:id intersection OR on shared identifier (doi/arxiv/url)
    shared_citations = []
    seen_pairs = set()
    a_by_id = {a["id"]: a for a in a_cited}
    b_by_id = {a["id"]: a for a in b_cited}
    for art_id in a_by_id.keys() & b_by_id.keys():
        shared_citations.append({"art_id": art_id, "rid_a_role": "cited",
                                  "rid_b_role": "cited", "match_method": "art_id"})
        seen_pairs.add((art_id, art_id))
    # Identifier-based intersection across remaining cited artifacts
    for ka in ("doi", "arxiv", "url", "isbn"):
        a_idx = {a.get("identifiers", {}).get(ka): a for a in a_cited
                  if a.get("identifiers", {}).get(ka)}
        b_idx = {b.get("identifiers", {}).get(ka): b for b in b_cited
                  if b.get("identifiers", {}).get(ka)}
        for v in a_idx.keys() & b_idx.keys():
            pair = (a_idx[v]["id"], b_idx[v]["id"])
            if pair in seen_pairs or (a_idx[v]["id"], a_idx[v]["id"]) in seen_pairs:
                continue
            shared_citations.append({"art_id_a": a_idx[v]["id"], "art_id_b": b_idx[v]["id"],
                                      "rid_a_role": "cited", "rid_b_role": "cited",
                                      "match_method": f"identifier:{ka}", "matched_value": v})
            seen_pairs.add(pair)

    result = {
        "rid_a": side_a, "rid_b": side_b,
        "fetch_mode_a": mode_a, "fetch_mode_b": mode_b,
        "match_method": match_method,
        "shared_claims": shared,
        "divergent_claims": {"only_in_a": only_in_a, "only_in_b": only_in_b},
        "contradictions": contradictions,
        "shared_citations": shared_citations,
        "manifest": manifest.finish(),
        "n_shared_claims": len(shared),
        "n_only_in_a": len(only_in_a), "n_only_in_b": len(only_in_b),
        "n_contradictions": len(contradictions),
        "n_shared_citations": len(shared_citations),
        "cross_profile_relations_skipped": cross_skipped,
    }
    if match_method == "llm_judge":
        # Include the candidate pairs + LLM-judging instructions for the agent
        result["llm_judge_payload"] = {
            "candidate_pairs": candidate_pairs_for_judge,
            "n_candidates": len(candidate_pairs_for_judge),
            "system_message": (
                "You are a careful semantic-similarity judge. For each pair of claim statements, "
                "decide whether the two statements assert the SAME proposition (semantically equivalent), "
                "even if phrased differently. Output a single JSON object: "
                "{\"judgments\": [{\"candidate_id\": \"pair_N\", \"shared\": true|false, "
                "\"reason\": \"<≤20 words>\"}]}. Be strict — only mark `true` when the propositions "
                "are genuinely equivalent (paraphrase, restatement, or alternative formalization), not just topically related."
            ),
            "user_message_template": (
                "Decide which of the following statement pairs assert the same claim.\n\n"
                "Pairs:\n{pairs_json}\n\n"
                "Output the JSON object."
            ),
            "instructions": (
                "1. Render `pairs_json` as JSON list of {candidate_id, stmt_a_text, stmt_b_text}.\n"
                "2. Call your LLM with system + filled user message.\n"
                "3. Parse the response's `judgments` array.\n"
                "4. Call `finalize_paper_compare(this_result, judgments)` to merge confirmed pairs into shared_claims."
            ),
        }
        # Empty `shared` initially — populated by finalize_paper_compare()
        result["shared_claims"] = []
        result["n_shared_claims"] = 0
        result["llm_judge_pending"] = True
    return result


def finalize_paper_compare(initial_result: dict, judgments: list[dict]) -> dict:
    """Step 2 of LLM-judge mode: merge LLM judgments into the diff_report.

    `judgments` is a list of {candidate_id, shared: bool, reason: str} dicts
    from the agent's LLM call on `initial_result["llm_judge_payload"]`.

    Returns a fresh result dict with `shared_claims` populated based on confirmed
    pairs (judgments[].shared == True). Greedy: same-stmt double-claims resolved
    by descending text_overlap_score (deterministic tie-break).
    """
    if not initial_result.get("llm_judge_pending"):
        return {"error": "initial_result is not in llm_judge_pending mode"}
    payload = initial_result.get("llm_judge_payload", {})
    candidates = payload.get("candidate_pairs", [])
    cand_by_id = {c["candidate_id"]: c for c in candidates}
    judgment_by_id = {j["candidate_id"]: j for j in judgments
                       if isinstance(j, dict) and "candidate_id" in j}

    # Confirmed candidates, sorted by text_overlap_score descending (tie-break)
    confirmed = sorted(
        [(cand_by_id[cid], j) for cid, j in judgment_by_id.items()
         if j.get("shared") and cid in cand_by_id],
        key=lambda pair_j: -pair_j[0]["text_overlap_score"])
    used_a, used_b, shared = set(), set(), []
    for cand, judgment in confirmed:
        a_id, b_id = cand["stmt_a_id"], cand["stmt_b_id"]
        if a_id in used_a or b_id in used_b:
            continue  # greedy: skip if either side already matched
        shared.append({
            "stmt_a_id": a_id, "stmt_b_id": b_id,
            "similarity_score": cand["text_overlap_score"],
            "match_method": "llm_judge",
            "shared_text_summary": cand["stmt_a_text"][:200],
            "llm_reason": judgment.get("reason", ""),
        })
        used_a.add(a_id); used_b.add(b_id)

    # Recompute divergent now that LLM-confirmed shared are known
    # (only_in_a/only_in_b in initial_result were computed against the empty shared list)
    final = dict(initial_result)
    final["shared_claims"] = shared
    final["n_shared_claims"] = len(shared)
    final["llm_judge_pending"] = False
    final["n_judgments_processed"] = len(judgment_by_id)
    final["n_judgments_confirmed"] = len(confirmed)
    return final


# ---------------- P2: version-inspector -----------------

def run_version_inspector(rid: str, *, max_depth: int = 20) -> dict:
    """Backward `replaces` chain walk per references/version-inspector.md contract.

    Hard non-goals enforced: no forward discovery, no heuristic latest, no sibling
    enumeration. Detects chain_break / chain_cycle / depth_cap with explicit markers.
    """
    decision = dispatch("inspect_lineage", {"rid": rid}, "version_chain_report")
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    # Clamp max_depth to documented [1, 20] safety bounds
    max_depth = max(1, min(int(max_depth), 20))
    manifest = Manifest(skill=skill, intent_class="inspect_lineage",
                        dispatch_tuple="(inspect_lineage,{rid},version_chain_report)",
                        returned_rids=[rid])

    # Initial fetch is special — 404 here means the user-supplied RID doesn't exist;
    # this is rid_not_found.<rid> abstain, NOT chain_break (which means chain has at
    # least 1 valid hop and a parent edge points to a missing record).
    try:
        first_sc = fetch_sidecar(rid)
    except NotFoundError:
        manifest.abstained = True
        manifest.abstained_reason = f"rid_not_found.{rid}"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "manifest": manifest.finish()}
    except TransportError as e:
        manifest.abstained = True
        manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
        return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}
    # G7: profile filter on starting record (later hops trust the chain)
    # Manifest contract per §6.1: explicitly populate applied_profile_filters +
    # applied_quality_policy from this skill's registered policy entries
    # (version-inspector doesn't go through filter_records — chain walk is special).
    manifest.applied_profile_filters = list(ACCEPTS_PROFILES.get("version-inspector", []))
    manifest.applied_quality_policy = dict(QUALITY_POLICIES.get("version-inspector", {}))
    if first_sc.get("profile") != "paper@1":
        manifest.abstained = True
        manifest.abstained_reason = "empty_working_set_after_profile_filter"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "manifest": manifest.finish()}

    chain = []; seen = set()
    chain_break = False; break_at = None
    chain_cycle = False; cycle_at = None
    depth_capped = False
    current = rid
    current_sc = first_sc
    TAG_NAMES = ["current", "parent", "grandparent", "great-grandparent"]
    for position in range(1, max_depth + 1):
        if current in seen:
            chain_cycle = True; cycle_at = current; break
        seen.add(current)
        # First hop reuses first_sc; subsequent hops fetch
        if position == 1:
            sc = first_sc
        else:
            try:
                sc = fetch_sidecar(current)
            except NotFoundError:
                chain_break = True; break_at = current; break
            except TransportError as e:
                manifest.abstained = True
                manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
                return {"abstained": True, "reason": manifest.abstained_reason, "detail": str(e), "manifest": manifest.finish()}
        chain.append({
            "position": position,
            "tag": TAG_NAMES[position - 1] if position <= 4 else f"ancestor (depth {position})",
            "rid": current,
            "version_record": sc.get("version", {}).get("record"),
            "record_status": sc.get("record_status"),
            "freshness_as_of": sc.get("freshness", {}).get("as_of"),
        })
        manifest.fetch_mode_per_rid[current] = "full"
        next_rid = sc.get("replaces")
        if not next_rid:
            break
        current = next_rid
        if current not in manifest.returned_rids:
            manifest.returned_rids.append(current)
    else:
        depth_capped = True

    return {
        "starting_rid": rid,
        "chain": chain,
        "chain_length": len(chain),
        "chain_break": chain_break,
        "chain_break_at_rid": break_at,
        "chain_cycle": chain_cycle,
        "chain_cycle_at_rid": cycle_at,
        "depth_capped": depth_capped,
        "forward_view": "unavailable",
        "sibling_view": "unavailable",
        "latest_inference": ("NOT PROVIDED — latest-status asserted only via explicit "
                              "replaces edge from a successor; this skill does not infer latest"),
        "manifest": manifest.finish(),
    }


# ---------------- P3: sidecar-reviser -----------------

REVISER_WHITELIST = frozenset(["record_status", "freshness.as_of", "version.record",
                                 "replaces", "provenance.revised_by"])
_RECORD_STATUS_ENUM = frozenset(["active", "superseded", "retracted", "draft", "deprecated"])


def _validate_patch(field: str, value, original: dict) -> str | None:
    """Return None on valid; else error string per references/sidecar-reviser.md §7."""
    import re
    if field == "record_status":
        if value not in _RECORD_STATUS_ENUM:
            return f"record_status must be in {sorted(_RECORD_STATUS_ENUM)}, got {value!r}"
    elif field == "freshness.as_of":
        if not isinstance(value, str) or not (
            re.match(r"^\d{4}-\d{2}-\d{2}$", value)
            or re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", value)):
            return f"freshness.as_of must match YYYY-MM-DD or full ISO-8601 UTC, got {value!r}"
    elif field == "version.record":
        if not isinstance(value, str) or not re.match(r"^\d+\.\d+(\.\d+)?$", value):
            return f"version.record must match semver-like ^\\d+\\.\\d+(\\.\\d+)?$, got {value!r}"
    elif field == "replaces":
        if not isinstance(value, str) or not re.match(
                r"^knows:[a-z0-9_/.-]+/\d+\.\d+(\.\d+)?$", value):
            return f"replaces must be valid record_id, got {value!r}"
        if value == original.get("record_id"):
            return f"replaces self-reference forbidden ({value} == record_id)"
        if value == original.get("replaces"):
            return f"replaces immediate-cycle forbidden (already current parent)"
    elif field == "provenance.revised_by":
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            return f"provenance.revised_by must be non-empty str ≤256 chars, got len={len(value) if isinstance(value,str) else 'N/A'}"
    return None


def _set_dotted(d: dict, path: str, value) -> None:
    keys = path.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def run_sidecar_reviser(target_rid: str, field_patches: dict, *,
                         output_path: str | None = None) -> dict:
    """Whitelist patcher per references/sidecar-reviser.md contract.

    Validates all patches BEFORE mutation; on any validator failure aborts (no partial
    file written). Re-lints revised YAML to ensure validity preserved.
    """
    import copy, difflib
    from pathlib import Path
    try:
        import yaml
    except ImportError:
        return {"abstained": True, "reason": "skill_runtime_exception.YamlMissing",
                "detail": "pyyaml required: pip install pyyaml"}

    if not isinstance(field_patches, dict) or not field_patches:
        return {"abstained": True, "reason": "missing_required_input.field_patches"}

    # 1. Whitelist check
    bad_keys = set(field_patches.keys()) - REVISER_WHITELIST
    if bad_keys:
        return {"abstained": True, "reason": "invalid_slot_type.field_patches",
                "detail": f"non-whitelist keys: {sorted(bad_keys)}"}

    decision = dispatch("revise_local",
                        {"target_rid": target_rid, "field_patches": field_patches},
                        "diff_and_yaml")
    if decision["action"] != "route":
        return {"abstained": True, **decision}
    skill = decision["skill"]
    manifest = Manifest(skill=skill, intent_class="revise_local",
                        dispatch_tuple="(revise_local,{target_rid,field_patches},diff_and_yaml)",
                        returned_rids=[target_rid])
    try:
        original = fetch_sidecar(target_rid)
    except NotFoundError:
        manifest.abstained = True
        manifest.abstained_reason = f"rid_not_found.{target_rid}"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "manifest": manifest.finish()}
    except TransportError as e:
        manifest.abstained = True
        manifest.abstained_reason = "upstream_unavailable_retries_exhausted"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "detail": str(e), "manifest": manifest.finish()}
    manifest.fetch_mode_per_rid[target_rid] = "full"

    # G7 + G2': sidecar-reviser declares accepts_profiles: [paper@1] in its frontmatter
    # AND its own quality_policy. filter_records mutates manifest with the correct
    # policy + filter values so manifest contract per dispatch-and-profile.md §6.1 holds.
    profile_kept = filter_records(
        [{**original, "stats": {"stmt_count": len(original.get("statements", []))},
          "coverage_statements": original.get("coverage", {}).get("statements"),
          "lint_passed": True, "record_id": target_rid}],
        "sidecar-reviser",  # use this skill's own policy entry (added to ACCEPTS_PROFILES + QUALITY_POLICIES)
        manifest)
    if not profile_kept:
        manifest.abstained = True
        manifest.abstained_reason = ("empty_working_set_after_profile_filter"
                                      if original.get("profile") != "paper@1"
                                      else "empty_working_set_after_quality_filter")
        return {"abstained": True, "reason": manifest.abstained_reason,
                "detail": (f"profile mismatch: got {original.get('profile')!r}"
                            if original.get("profile") != "paper@1"
                            else "record failed quality_policy"),
                "manifest": manifest.finish()}

    # 2. Validate every patch BEFORE mutation
    errors = []
    for path, value in field_patches.items():
        err = _validate_patch(path, value, original)
        if err:
            errors.append(f"{path}: {err}")
    if errors:
        manifest.abstained = True
        manifest.abstained_reason = "invalid_slot_type.field_patches"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "detail": errors, "manifest": manifest.finish()}

    # 3. Apply patches to deep copy
    revised = copy.deepcopy(original)
    for path, value in field_patches.items():
        _set_dotted(revised, path, value)

    # 4. Write new YAML
    out = output_path or str(Path("/tmp") / f"{target_rid.replace(':','_').replace('/','_')}_revised.knows.yaml")
    orig_yaml = yaml.dump(original, sort_keys=False, allow_unicode=True, default_flow_style=False)
    rev_yaml = yaml.dump(revised, sort_keys=False, allow_unicode=True, default_flow_style=False)
    Path(out).write_text(rev_yaml)

    # 5. Re-lint via post-gen pipeline
    relint = run_sidecar_author_postgen(out, out, include_cited=False)
    if not relint["lint_passed"]:
        manifest.abstained = True
        manifest.abstained_reason = "skill_runtime_exception.RevisionBreaksLint"
        return {"abstained": True, "reason": manifest.abstained_reason,
                "lint_output": relint["lint_output"], "manifest": manifest.finish()}

    # 6. Compute diff
    diff = "\n".join(difflib.unified_diff(orig_yaml.splitlines(), rev_yaml.splitlines(),
                                            fromfile="original", tofile="revised", lineterm=""))
    return {
        "target_rid": target_rid,
        "applied_patches": dict(field_patches),
        "patches_attempted": list(field_patches.keys()),
        "diff": diff,
        "output_path": out,
        "lint_passed_after_revision": True,
        "lint_warnings_after_revision": relint["lint_warnings"],
        "governance_disclaimer": ("Local revision only — does NOT certify canonicality, "
                                    "does NOT update the hub registry, does NOT mutate prior "
                                    "records' state. Upload handoff via sidecar-author "
                                    "(DEFERRED in v1.0)."),
        "manifest": manifest.finish(),
    }


# ---------------- CLI -----------------

def _cli() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Knows orchestrator runtime")
    sub = p.add_subparsers(dest="cmd")

    pf = sub.add_parser("paper-finder", help="run paper-finder")
    pf.add_argument("query")
    pf.add_argument("--top-k", type=int, default=10)
    pf.add_argument("--artifact", default="ranked_paper_list",
                    choices=["ranked_paper_list", "bibtex"])
    pf.add_argument("--year-min", type=int, default=None,
                    help="server-side filter: year >= N")
    pf.add_argument("--year-max", type=int, default=None,
                    help="server-side filter: year <= N")
    pf.add_argument("--venue-type", default=None,
                    choices=["conference", "journal", "preprint", "workshop", "published"],
                    help=("server-side filter: ONE venue_type. Spec canonical: "
                          "conference|journal|preprint|workshop. NOTE most hub records "
                          "still use transitional 'published' (covers conference+journal); "
                          "use 'published' for current data, the canonical 4 once hub migrates"))
    pf.add_argument("--venue", default=None,
                    help="client-side filter: substring match on venue (e.g. 'USENIX', 'IEEE S&P')")
    pf.add_argument("--discipline", default=None,
                    help="server-side filter: discipline (sparse on hub records — may return 0)")
    pf.add_argument("--sort", default=None,
                    choices=["latest", "trending", "claims"],
                    help="server-side sort (server default: latest)")
    pf.add_argument("--no-or-fallback", action="store_true",
                    help="disable OR-fallback when AND-logic returns 0 hits")
    pf.add_argument("--page-limit", type=int, default=None,
                    help="server-side limit per page (default: max(top_k, 20), capped at 100)")

    sr = sub.add_parser("sidecar-reader", help="prepare sidecar-reader LLM payload")
    sr.add_argument("rid_or_q",
                    help="hub RID (starts with 'knows:') OR question (when --local supplied)")
    sr.add_argument("q_or_unused", nargs="?", default=None,
                    help="question (when first arg is RID); ignored when --local mode")
    sr.add_argument("--local", default=None,
                    help="path to local .knows.yaml (P0: ask Qs about your own freshly-generated sidecar)")

    sa = sub.add_parser("sidecar-author-pdf", help="prepare sidecar-author Path F (PDF) workflow")
    sa.add_argument("pdf_path")
    sa.add_argument("-o", "--output", default=None)
    sa.add_argument("--no-cited", action="store_true", help="Skip --include-cited enrichment")

    sp = sub.add_parser("sidecar-author-postgen",
                        help="Run sanitize → lint → verify on a raw LLM-generated YAML")
    sp.add_argument("raw_yaml")
    sp.add_argument("output")
    sp.add_argument("--no-cited", action="store_true")

    pc = sub.add_parser("paper-compare", help="Pairwise diff of two sidecars (hub OR local)")
    pc.add_argument("source_a", help="hub RID OR local path to .knows.yaml")
    pc.add_argument("source_b", help="hub RID OR local path to .knows.yaml")
    pc.add_argument("--threshold", type=float, default=0.5)
    pc.add_argument("--text-overlap", action="store_true",
                    help="Use deterministic Jaccard match instead of llm_judge default. "
                    "llm_judge (default) returns candidate-pair payload for the agent's LLM "
                    "to confirm; finalize via finalize_paper_compare(result, judgments). "
                    "text_overlap is faster but misses cross-terminology matches.")

    vi = sub.add_parser("version-inspector", help="Walk replaces chain backward")
    vi.add_argument("rid")
    vi.add_argument("--max-depth", type=int, default=20)

    dx = sub.add_parser("disciplines", help="Browse hub by discipline (trending/claims/arxiv)")
    dx.add_argument("--view", default="trending", choices=["trending", "claims", "arxiv"])

    hl = sub.add_parser("health", help="Pre-flight hub availability check")

    cc = sub.add_parser("coverage-check",
                         help="Hub coverage diagnostic: how much hub coverage exists for a topic?")
    cc.add_argument("query", help="Topic to probe (e.g. 'side channel attacks')")
    cc.add_argument("--year-min", type=int, default=None)
    cc.add_argument("--venue-type", default=None,
                     choices=list(VENUE_TYPE_ENUM),
                     help="Filter by venue type")

    ck = sub.add_parser("cite-key",
                         help="Derive a BibTeX-style citation key from a hub RID (e.g. 'dao2023')")
    ck.add_argument("rid", help="Hub RID (starts with 'knows:')")

    sv = sub.add_parser("sidecar-reviser", help="Whitelist patcher")
    sv.add_argument("target_rid")
    sv.add_argument("patches_json", help='JSON dict, e.g. \'{"version.record":"1.1.0"}\'')
    sv.add_argument("-o", "--output", default=None)

    args = p.parse_args()
    if args.cmd == "paper-finder":
        out = run_paper_finder(args.query, top_k=args.top_k, artifact=args.artifact,
                                year_min=args.year_min, year_max=args.year_max,
                                venue_type=args.venue_type, venue=args.venue,
                                discipline=args.discipline, sort=args.sort,
                                or_fallback=not args.no_or_fallback,
                                page_limit=args.page_limit)
        if "table" in out:
            print(out["table"])
        elif "bibtex" in out:
            print(out["bibtex"])
        else:
            print(json.dumps(out, indent=2))
        return 0 if not out.get("abstained") else 1
    if args.cmd == "sidecar-reader":
        # Local mode: --local PATH "question"; first positional is the question
        # Hub mode (default): "rid" "question"
        if args.local:
            out = run_sidecar_reader(local_path=args.local, q=args.rid_or_q)
        else:
            if not args.q_or_unused:
                print("ERROR: hub mode requires both rid and question (or use --local)")
                return 2
            out = run_sidecar_reader(rid=args.rid_or_q, q=args.q_or_unused)
        if "manifest_seed" in out:
            out = {**out, "manifest_seed": "<Manifest object — call .finish()>"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if not out.get("abstained") else 1
    if args.cmd == "sidecar-author-pdf":
        out = run_sidecar_author_pdf(args.pdf_path, output_path=args.output,
                                       include_cited=not args.no_cited)
        if "manifest_seed" in out:
            out = {**out, "manifest_seed": "<Manifest object — call .finish()>"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if not out.get("abstained") else 1
    if args.cmd == "sidecar-author-postgen":
        out = run_sidecar_author_postgen(args.raw_yaml, args.output,
                                           include_cited=not args.no_cited)
        # Strip verbose subprocess outputs from JSON dump
        compact = {k: v for k, v in out.items() if k not in ("lint_output", "verify_output")}
        print(json.dumps(compact, indent=2))
        if "lint_output" in out:
            print("\n--- lint output ---\n" + out["lint_output"])
        return 0 if out.get("ready_to_publish") else 1
    if args.cmd == "paper-compare":
        # Detect hub-RID vs local-path heuristic for each side (knows: prefix → hub)
        def _split(src):
            return ("rid", src) if src.startswith("knows:") else ("local", src)
        kind_a, val_a = _split(args.source_a)
        kind_b, val_b = _split(args.source_b)
        kwargs = {"similarity_threshold": args.threshold}
        if args.text_overlap:
            kwargs["match_method"] = "text_overlap"
        if kind_a == "rid":
            kwargs["rid_a"] = val_a
        else:
            kwargs["local_path_a"] = val_a
        if kind_b == "rid":
            kwargs["rid_b"] = val_b
        else:
            kwargs["local_path_b"] = val_b
        out = run_paper_compare(**kwargs)
        # Top-of-output summary header: scanning a 200-line JSON payload to find candidate
        # pairs is poor UX. Print top-3 first, reusing the already-sorted candidate_pairs
        # list (do NOT re-rank in the printer — would drift from the payload).
        if not out.get("abstained"):
            payload = out.get("llm_judge_payload") or {}
            cands = payload.get("candidate_pairs", [])
            n_total = payload.get("n_candidates", len(cands))
            if cands:
                print(f"=== Top-3 candidate pairs (of {n_total}) — preview before JSON ===")
                for c in cands[:3]:
                    score = c.get("text_overlap_score", 0.0)
                    print(f"  [{score:.2f}] {c['candidate_id']}: {c['stmt_a_id']} ↔ {c['stmt_b_id']}")
                    print(f"    A: {c['stmt_a_text'][:100]}")
                    print(f"    B: {c['stmt_b_text'][:100]}")
                print()
            elif out.get("shared_claims"):
                print(f"=== Top-3 shared claims (of {out['n_shared_claims']}, text_overlap) ===")
                for s in out["shared_claims"][:3]:
                    print(f"  [{s['similarity_score']:.2f}] {s['stmt_a_id']} ↔ {s['stmt_b_id']}")
                    print(f"    {s['shared_text_summary'][:100]}")
                print()
        # Trim verbose payloads for CLI display
        compact = {k: v for k, v in out.items()
                    if k not in ("shared_claims", "divergent_claims", "contradictions", "shared_citations")}
        print(json.dumps(compact, indent=2, ensure_ascii=False))
        return 0 if not out.get("abstained") else 1
    if args.cmd == "version-inspector":
        out = run_version_inspector(args.rid, max_depth=args.max_depth)
        compact = {k: v for k, v in out.items() if k != "chain"}
        print(json.dumps(compact, indent=2, ensure_ascii=False))
        if "chain" in out:
            print(f"\n=== Chain ({out['chain_length']} hops) ===")
            for hop in out["chain"]:
                print(f"  [{hop['position']}] ({hop['tag']}) {hop['rid']}")
                print(f"      version={hop['version_record']} status={hop['record_status']} as_of={hop['freshness_as_of']}")
        return 0 if not out.get("abstained") else 1
    if args.cmd == "disciplines":
        try:
            data = fetch_disciplines(view=args.view)
        except TransportError as e:
            print(json.dumps({"error": "upstream_unavailable_retries_exhausted",
                              "detail": str(e)}, indent=2))
            return 1
        print(f"# Hub disciplines (view={data.get('view')}, total_papers={data.get('total_papers')})\n")
        for g in data.get("groups", [])[:20]:
            sub_summary = ", ".join(f"{s['name']} ({s.get('paper_count','?')})"
                                     for s in g.get("subfields", [])[:5])
            # Group fields are total_papers/total_stmts (not paper_count/stmt_count)
            n_papers = g.get("total_papers") or g.get("paper_count")
            n_stmts = g.get("total_stmts") or g.get("stmt_count")
            print(f"- **{g['name']}** — {n_papers} papers / {n_stmts} stmts"
                  + (f"\n  subfields: {sub_summary}" if sub_summary else ""))
        return 0
    if args.cmd == "health":
        try:
            data = fetch_health()
        except TransportError as e:
            print(json.dumps({"status": "down", "detail": str(e)}, indent=2))
            return 1
        print(json.dumps(data, indent=2))
        return 0 if data.get("status") == "ok" else 1
    if args.cmd == "coverage-check":
        out = run_hub_coverage_check(args.query, year_min=args.year_min,
                                       venue_type=args.venue_type)
        if "error" in out:
            print(json.dumps(out, indent=2))
            return 1
        print(f"# Hub coverage for {out['query']!r}")
        f = out["filters_applied"]
        flt = ", ".join(f"{k}={v}" for k, v in f.items() if v is not None) or "none"
        print(f"  filters: {flt}")
        print(f"  hub total: {out['hub_total_papers']} papers")
        print(f"  topic hits hub-wide: {out['topic_total_hits']}")
        print(f"  verdict: **{out['verdict'].upper()}**")
        print(f"  advice: {out['advice']}\n")
        if out["top_subfields_by_topic_hits"]:
            print("## Top subfields by topic hits")
            for r in out["top_subfields_by_topic_hits"]:
                print(f"  - {r['full_path']}: {r['topic_hits_in_subfield']} / {r['papers_in_subfield']} papers")
        else:
            print("## No subfield matches — topic may be off-corpus or too narrow")
        return 0
    if args.cmd == "cite-key":
        try:
            print(cite_key(args.rid))
            return 0
        except (TransportError, NotFoundError) as e:
            print(json.dumps({"error": "cite_key_lookup_failed", "rid": args.rid,
                              "detail": str(e)}, indent=2))
            return 1
    if args.cmd == "sidecar-reviser":
        try:
            patches = json.loads(args.patches_json)
        except json.JSONDecodeError as e:
            print(f"ERROR: patches_json invalid: {e}"); return 2
        out = run_sidecar_reviser(args.target_rid, patches, output_path=args.output)
        compact = {k: v for k, v in out.items() if k != "diff"}
        print(json.dumps(compact, indent=2, ensure_ascii=False))
        if "diff" in out:
            print("\n=== Unified diff ===\n" + out["diff"])
        return 0 if not out.get("abstained") else 1
    p.print_help()
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(_cli())
    except TransportError as e:
        # Catch transport failures at the CLI boundary — print clean abstain JSON
        # rather than letting a urllib/network traceback escape to the user
        print(json.dumps({
            "abstained": True,
            "reason": "upstream_unavailable_retries_exhausted",
            "detail": str(e),
        }, indent=2))
        raise SystemExit(1)
