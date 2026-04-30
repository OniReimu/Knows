---
name: knows-survey-narrative
description: "Compose a related-work paragraph (1-3 paragraphs of academic prose with `\\cite{}` keys) grounded in N retrieved sidecars on a topic. Triggers: 'write me a related-work paragraph on X', 'summarize the literature on Y', 'give me a background section about Z', 'compose related work for my paper intro on W'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: synthesize_prose
required_inputs:
  # Exactly one (mutually exclusive — supplying both is invalid_slot_type per §1.5 OR-pair):
  - query_text                      # free-text topic; skill calls paper-finder internally to retrieve
  - rid_set                         # pre-supplied list of record_ids; skill skips retrieval
optional_inputs:
  - brainstorm_summary              # OPTIONAL fenced YAML block produced by the `survey-shape` stance (Type B, v0.11+). When present, the skill switches to CONSUME MODE — uses the stance-locked arc + centerpieces + audience instead of inferring narrative shape itself. Schema: `brainstorm-v1` with `emit_chain: [survey-shape, survey-narrative]`. Solo path (without brainstorm_summary) is the v0.10 default.

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

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A)

When invoked downstream of the `survey-shape` stance (Type B), survey-narrative receives a `brainstorm_summary` input INSTEAD OF `query_text`/`rid_set`. Per `dispatch-and-profile.md` §1.5, the consume-mode dispatch tuple is `(synthesize_prose, {brainstorm_summary}, related_work_paragraph)` — strictly mutually exclusive with the solo-mode tuples that take `query_text` or `rid_set`. Supplying `brainstorm_summary` AND `query_text`/`rid_set` together produces an `unknown_dispatch_tuple` abstain, NOT a "both honored" merge. The brainstorm_summary's `centerpieces[*].rid` IS the rid_set in consume mode (do not also pass an external rid_set). The skill switches from SOLO MODE (v0.10 default — agent infers arc + centerpieces from the topic) to CONSUME MODE (uses stance-locked arc + centerpieces).

### Why CONSUME MODE matters here

Solo survey-narrative makes two implicit decisions: (a) what narrative arc to use (chronological / methodological / outcome-grouped / gap-driven / consolidating), and (b) which papers are centerpieces. Both are user-judgment territory — the agent's default may not match the user's framing. survey-shape collects these decisions explicitly through dialogue; consume mode preserves them in the output prose.

### CONSUME MODE flow

```python
if brainstorm_summary is None:
    # SOLO MODE — current v0.10 path. Agent infers shape from topic + retrieved hits.
    ...
else:
    summary = parse_brainstorm_summary(brainstorm_summary)
    if summary["status"] == "abandon":
        manifest.abstained = True
        manifest.abstained_reason = "brainstorm_abandoned"
        raise SystemExit
    if summary["status"] == "needs_rework":
        return {"action": "return_to_stance", "rework_needed": summary["rework_needed"]}
    assert summary["status"] == "ready"
    assert summary["emit_chain"][-1] == "survey-narrative"

    # Verify required shape decisions
    rework_needed = []
    if summary.get("arc") not in {"chronological", "methodological", "outcome-grouped",
                                  "gap-driven", "consolidating"}:
        rework_needed.append({"reason": f"arc must be one of the 5 archetypes; got {summary.get('arc')!r}"})
    if not summary.get("centerpieces") or len(summary["centerpieces"]) < 2:
        rework_needed.append({"reason": "need ≥2 centerpieces"})
    # Verify each centerpiece RID has a sidecar (G7 + G2' will be re-applied below)
    for cp in summary.get("centerpieces", []):
        rid = cp.get("rid")
        if not rid:
            rework_needed.append({"reason": f"centerpiece missing rid: {cp}"})

    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed}

    # Use centerpieces as the rid_set (skip paper-finder), respect stance-locked arc + audience
    centerpiece_rids = [cp["rid"] for cp in summary["centerpieces"]]
    kept = filter_records(fetch_sidecars_by_rids(centerpiece_rids), "survey-narrative", manifest)
    # LLM generation now follows the stance-locked arc, with each centerpiece's `role`
    # (pioneer / inflection / foil / bridge / culmination) shaping its position in the arc:
    prose = generate_prose(arc=summary["arc"], centerpieces=summary["centerpieces"],
                            audience=summary["audience"], word_budget=summary.get("word_budget", 300),
                            kept=kept)
    manifest["workflow_chain"] = summary["emit_chain"]   # ["survey-shape", "survey-narrative"]
```

### Field mapping (brainstorm_summary → related_work_paragraph)

| brainstorm_summary field | survey-narrative use |
|---|---|
| `arc` | top-level structural decision; LLM prompt prefix instructs which archetype to use |
| `arc_rationale` | embedded in the LLM prompt as user-justification context |
| `centerpieces[*].rid` | takes the place of `rid_set` — skill does not call paper-finder |
| `centerpieces[*].role` | shapes paragraph order: pioneer first → inflection → foil → bridge → culmination |
| `centerpieces[*].load_bearing_reason` | embedded in the LLM prompt as the "why this paper matters" anchor |
| `audience` | LLM prompt instruction (e.g., "write for NeurIPS DP-DL community" — adjusts technical density) |
| `word_budget` | hard cap on output length |
| `emit_chain` | manifest workflow_chain |

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| `status: needs_rework` | `action: return_to_stance` |
| `arc` not in the 5 archetypes | `action: return_to_stance` |
| `< 2` centerpieces | `action: return_to_stance` |
| Any centerpiece RID has no sidecar (G7 fail) OR fails G2' quality | `action: return_to_stance` (cannot ground a survey on missing or low-quality records) |
| `emit_chain` does NOT end with `survey-narrative` | `invalid_slot_type.brainstorm_summary` (chain misrouted; if it ends with `survey-table`, route to that emitter instead) |

### `provenance.workflow_chain`

related_work_paragraph is Markdown, not a sidecar — workflow_chain goes in the manifest.

## Out of scope (v1.1)

- Cross-discipline narrative blending — agent will struggle with disparate vocabulary; defer to v1.x with explicit `discipline` filter.
- LaTeX `bibitem` generation alongside prose — separate concern; user can call `paper-finder bibtex` route on the same `rid_set`.
- Auto-tone matching to user's draft (formal vs casual) — v1.x.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
