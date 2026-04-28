---
name: knows-survey-narrative
description: "Compose a related-work paragraph (1-3 paragraphs of academic prose with `\\cite{}` keys) grounded in N retrieved sidecars on a topic. Triggers: 'write me a related-work paragraph on X', 'summarize the literature on Y', 'give me a background section about Z', 'compose related work for my paper intro on W'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: synthesize_prose
required_inputs:
  # Exactly one (mutually exclusive — supplying both is invalid_slot_type per §1.5 OR-pair):
  - query_text                      # free-text topic; skill calls paper-finder internally to retrieve
  - rid_set                         # pre-supplied list of record_ids; skill skips retrieval

requested_artifacts:
  - related_work_paragraph          # 1-3 paragraphs Markdown prose with \cite{key} citations

# Profile contract — G7 (synthesizing prose about papers, so paper@1 only)
accepts_profiles: [paper@1]

# Quality policy — G2' (synthesis must filter out partial/low-statement records to avoid hallucinating from thin sidecars)
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (default: partial fetch /partial?section=statements is enough for synthesis at scale)
requires_full_record: false

# emits_profile omitted — related_work_paragraph is prose, not a sidecar artifact (read-only skill)
---

# survey-narrative — Compose a related-work paragraph grounded in retrieved sidecars

Different from `survey-table` (structured comparison) — this produces **flowing academic prose**.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_search, fetch_partial, filter_records, Manifest

# 1. Dispatch tuple: (synthesize_prose, {query_text}, related_work_paragraph)
#    OR (synthesize_prose, {rid_set: [...]}, related_work_paragraph) if user pre-supplied RIDs
TOPIC = "diffusion models with differential privacy"
TOP_K = 8
decision = dispatch("synthesize_prose", {"query_text": TOPIC}, "related_work_paragraph")
assert decision["action"] == "route"

# 2. Retrieve via paper-finder semantics (G5 transport, G7 filter, G2' quality)
manifest = Manifest(skill="survey-narrative", intent_class="synthesize_prose",
                    queries=[TOPIC],
                    dispatch_tuple="(synthesize_prose,{query_text},related_work_paragraph)")
hits = fetch_search(TOPIC, sort="claims", limit=min(TOP_K * 3, 100)).get("results", [])[:TOP_K]
# sort="claims" prefers richest sidecars (highest stmt_count) — best signal for grounded synthesis.
# limit > top_k over-fetches so G2'/G7 filters have headroom.
manifest.returned_rids = [h.get("record_id","?") for h in hits]
kept = filter_records(hits, "survey-narrative", manifest)
if not kept:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 3. G3 default: partial fetch (statements-only) for each kept record (token-efficient)
contexts = []
for h in kept:
    rid = h["record_id"]
    part = fetch_partial(rid, "statements")           # returns {record_id, items: [...]}
    contexts.append({"rid": rid, "title": h.get("title",""), "year": h.get("year"),
                     "statements": part.get("items", [])})
    manifest.fetch_mode_per_rid[rid] = "partial:statements"

# 4. LLM call — use the canonical prompt from `../../references/survey-narrative-prompt.md`.
#    The prompt locks in: 20 academic-prose padding banned phrases ("considerable interest",
#    "remarkable success", "growing body of work", "in recent years", etc.), citation-grounding
#    contract (every substantive sentence ends with \cite{key}, every key from the keys-table),
#    word-count discipline (100-400 words across 1-3 paragraphs), no-cross-paper-claim rule,
#    no-empirical-numbers-from-memory rule, and neutral-academic tone register.
#    Do NOT re-derive these per agent — use the canonical prompt verbatim.
#    Run the post-LLM padding-phrase check + citation-grounding check (one regenerate retry).
#
# Citation keys table — derived from cite_key() before invoking the prompt:
#     from orchestrator import cite_key
#     keys = {h["record_id"]: cite_key(h["record_id"]) for h in kept}
#     # → {"knows:dao/flashattention/1.0.0": "dao2022", ...}
# Pass the keys table into the user message; the LLM may ONLY use these keys.

# 5. Manifest finalize: model, token_cost_estimate, abstained=false
manifest.model = "claude-opus-4-7"
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `related_work_paragraph` | 1-3 paragraphs of academic Markdown prose, every substantive claim ending with `\cite{<key>}` keyed to retrieved sidecars |

## Hallucination-refusal triggers

The agent body MUST refuse to write a sentence if it cannot be grounded in the retrieved statements. Symptoms requiring refusal:
- A claim the user implies but no retrieved sidecar supports → omit, do not invent
- Cross-paper conclusion not stated in any single sidecar → use cautious phrasing ("Several papers report ...") OR omit
- Empirical numbers not present in retrieved statements → omit; do NOT make up percentages

If after grounding the prose has < 2 cited sentences, abstain with `empty_working_set_after_quality_filter` (effectively zero usable evidence even after retrieval).

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| Both `query_text` AND `rid_set` supplied (OR-violation) | `invalid_slot_type.<second>` |
| Neither supplied | `missing_required_input.query_text` |
| `query_text` empty / `rid_set` empty list | `invalid_slot_type.<slot>` |
| API search returns 0 hits | `empty_working_set_after_profile_filter` (no-hits tie-breaker) |
| All hits dropped by G7 / G2' | `empty_working_set_after_profile_filter` / `_quality_filter` |
| Generated prose has < 2 grounded citations after agent refusal | `empty_working_set_after_quality_filter` (effective grounding empty) |

## Manifest emission (G6)

Per G6: `skill: survey-narrative`, `intent_class: synthesize_prose`, `dispatch_tuple`, `queries: [TOPIC]` or empty if `rid_set`, `returned_rids: [hit RIDs]`, `applied_profile_filters: [paper@1]`, `applied_quality_policy`, `excluded_*` and `quality_exclusions`, `fetch_mode_per_rid` all `partial:statements` (G3 default), `model`, `token_cost_estimate`. The output prose **MUST reference manifest.json** in a footnote (e.g. "Generated via knows survey-narrative; provenance: manifest.json").

## Out of scope (v1.1)

- Cross-discipline narrative blending — agent will struggle with disparate vocabulary; defer to v1.x with explicit `discipline` filter.
- LaTeX `bibitem` generation alongside prose — separate concern; user can call `paper-finder bibtex` route on the same `rid_set`.
- Auto-tone matching to user's draft (formal vs casual) — v1.x.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
