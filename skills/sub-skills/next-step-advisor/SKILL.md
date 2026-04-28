---
name: knows-next-step-advisor
description: "Produce an evidence-backed next-step research brief — N candidate research questions for a topic, each grounded in retrieved sidecars' open questions / limitations. Triggers: 'what should I work on next in X', 'where are the gaps in Y research', 'give me 5 thesis ideas about Z', 'what's underexplored in W'. Heuristic by design — bounded by the top-K retrieved sidecars, not a corpus-wide gap detector."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: brief_next_steps
required_inputs:
  - query_text                      # research area / topic in natural language

requested_artifacts:
  - next_step_brief                 # Markdown brief: N candidate questions, each with supporting refs

# Profile contract — G7
accepts_profiles: [paper@1]

# Quality policy — G2' (strict, since speculative synthesis is the failure mode)
quality_policy:
  require_lint_passed: true
  allowed_coverage:                 # exclude `partial` aggressively — partial coverage is exactly where speculation creeps in
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (default partial: only need question + limitation statements, not full record)
requires_full_record: false

# emits_profile omitted — next_step_brief is prose, not a sidecar artifact (read-only)
---

# next-step-advisor — Evidence-backed next-step research brief

**High-risk skill — abstain rules are strict by design.** Without them, the output degrades into plausible-sounding LLM speculation that damages user trust. The core value is **grounded** advice — each candidate question must trace to specific `question`-typed or `limitation`-typed statements in retrieved sidecars.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_search, fetch_partial, filter_records, Manifest

# 1. Dispatch tuple
TOPIC = "multi-path CoT in LLM reasoning"
TOP_K = 12

decision = dispatch("brief_next_steps", {"query_text": TOPIC}, "next_step_brief")
assert decision["action"] == "route"

# 2. G5 + G7 + G2': retrieve top-K
manifest = Manifest(skill="next-step-advisor", intent_class="brief_next_steps",
                    queries=[TOPIC],
                    dispatch_tuple="(brief_next_steps,{query_text},next_step_brief)")
hits = fetch_search(TOPIC, sort="trending", limit=min(TOP_K * 3, 100)).get("results", [])[:TOP_K]
# sort="trending" prefers community-attended papers — more likely to have outstanding limitations
# the field has noticed but not solved. Falls back to "latest" if trending data sparse on this topic.
# limit > top_k over-fetches so G2'/G7 filters have headroom.
manifest.returned_rids = [h["record_id"] for h in hits]
kept = filter_records(hits, "next-step-advisor", manifest)
if not kept:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 3. G3 partial fetch — only statements (we need `question` + `limitation` types)
contexts = []
for h in kept:
    rid = h["record_id"]
    part = fetch_partial(rid, "statements")
    qs = [s for s in part.get("items", []) if s.get("statement_type") in ("question", "limitation")]
    if qs:
        contexts.append({"rid": rid, "title": h.get("title"), "questions_or_limits": qs})
    manifest.fetch_mode_per_rid[rid] = "partial:statements"

# 4a. HARD ABSTAIN (numeric): if total questions+limitations across all kept records < 3, refuse:
total_evidence = sum(len(c["questions_or_limits"]) for c in contexts)
if total_evidence < 3:
    manifest.abstained = True
    manifest.abstained_reason = "empty_working_set_after_quality_filter"
    print({"abstained": True, "reason": "too few question/limitation statements to ground a brief — try a more specific topic OR more sidecars"})
    raise SystemExit

# 4b. HARD ABSTAIN (topical, §4.1): for intersection queries (A × B), require ≥ 1
#     statement that names BOTH sides. Without this precheck, the LLM can stitch a
#     statement about A onto a statement about B — speculation by composition.
from orchestrator import parse_intersection_query, topical_grounding_count
intersection = parse_intersection_query(TOPIC)
if intersection:
    a, b = intersection
    all_stmts = [s for c in contexts for s in c["questions_or_limits"]]
    n_topical = topical_grounding_count(all_stmts, a, b)
    if n_topical < 1:
        manifest.abstained = True
        manifest.abstained_reason = "empty_working_set_after_quality_filter"
        print({"abstained": True,
               "reason": f"intersection query '{a}' × '{b}': 0 statements name both — Q/L count was {total_evidence} but none span the intersection. Pivot retrieval source (Scholar/arXiv) before committing."})
        raise SystemExit

# 5. LLM call — use the canonical prompt from `references/next-step-advisor-prompt.md`.
#    The prompt locks in: banned-phrase enforcement (15 speculation tells), grounding contract
#    (every candidate must cite stmt:* + verbatim_quote substring), banned candidate categories
#    (replication, generic apply-to-domain, improve-by-N%, vacuous combinations), JSON output
#    schema, and the mandatory heuristic disclaimer. Do NOT re-derive these rules per agent —
#    use the canonical prompt verbatim, then run the post-LLM banned-phrase + grounding checks
#    that document specifies (with one regenerate retry on failure).
# Output: structured JSON per the prompt's schema, plus the disclaimer footer in the
# user-facing prose.

# 6. Manifest finalize: explicitly mark as heuristic (not corpus-wide):
manifest.model = "claude-opus-4-7"
print(manifest.finish())
# The output prose MUST also include this disclaimer footer (G4 governance gap):
#   "This brief is heuristic, not corpus-wide. Recall is bounded by the top-K retrieved
#    sidecars (here K=12) and their `question`/`limitation` coverage. A gap not surfaced
#    here may still exist in the broader literature."
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `next_step_brief` | Markdown brief: 3-5 grounded questions, evidence inventory, heuristic disclaimer |

## Hard abstain rules (this skill is unusual — extra strict)

| Condition | `abstained_reason` |
|---|---|
| `query_text` missing or empty | `missing_required_input.query_text` |
| Working set empty after G7/G2' | `empty_working_set_after_profile_filter` / `_quality_filter` |
| **< 3 question/limitation statements** across all kept records | `empty_working_set_after_quality_filter` (insufficient grounding evidence) |
| LLM tries to output > 5 candidate questions | abort + retry; cap at 5 |
| LLM outputs a candidate without ≥1 stmt:* citation | abort + retry; if 2 retries fail → abstain `skill_runtime_exception.UngroundedSpeculation` |

## Banned phrases (compile-time check)

If the LLM output contains any of these without a `[stmt:* from RID]` citation in the same sentence, regenerate:
- "could explore" / "might investigate" / "promising direction"
- "future work could" / "this opens up" / "intriguing avenue"
- "underexplored" / "ripe for" / "ample opportunity"

These are the speculation tells that damage user trust. Either back the claim with a sidecar reference or omit it.

## Manifest emission

Per G6 + G4: `skill: next-step-advisor`, `intent_class: brief_next_steps`, `dispatch_tuple`, `queries: [TOPIC]`, `returned_rids`, `fetch_mode_per_rid` all `partial:statements`, `model`, plus skill-specific `evidence_inventory: {n_questions, n_limitations, n_kept_records}`. The output MUST embed the heuristic disclaimer (G4 governance-gap).

## Out of scope (v1.2)

- Cross-conference temporal analysis ("after ICLR 2026 ended, what's still open?") — would need date-filtered search, currently best-effort.
- Funding-feasibility scoring — pure research-direction signal only.
- LLM-judged "novelty score" per candidate — too noisy without human review.
- Multi-topic blending ("multi-path CoT AND federated learning") — single topic only in v1.2.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
