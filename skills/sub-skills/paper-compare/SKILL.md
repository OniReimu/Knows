---
name: knows-paper-compare
description: "Pairwise compare two KnowsRecord sidecars — shared claims, divergent claims, contradictions, shared citations. Triggers: 'compare paper X and Y', 'what does Y claim that X doesn't', 'diff these two sidecars', 'where do A and B disagree'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: diff
required_inputs:
  - rid_pair                        # tuple[rid_a, rid_b] — both record_ids on knows.academy
requested_artifacts:
  - diff_report                     # structured diff: shared / divergent / contradictory / shared_citations

# Profile contract — G7 (single profile, both sides paper@1)
accepts_profiles: [paper@1]

# Quality policy — G2'
quality_policy:
  require_lint_passed: true
  allowed_coverage:                  # exclude `partial` — diff over partial coverage produces noise
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (need full records: relations + statements both sides)
requires_full_record: true

# emits_profile omitted — diff_report is not a sidecar artifact (read-only skill)
---

# paper-compare — Pairwise diff of two sidecars

Pairwise depth-comparison: focuses on shared/divergent/contradictory **claims** and **shared citations**, exploiting the relation graph (`challenged_by`, `supersedes`, `cites`). Different from `survey-table` (N-way breadth comparison on user-supplied axes).

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import fetch_sidecar, filter_records, Manifest, dispatch

# 1. Dispatch tuple: (diff, {rid_pair: (a, b)}, diff_report)
RID_A = "knows:vaswani/attention/1.0.0"
RID_B = "knows:liu/multi-path-cot/1.0.0"

decision = dispatch("diff", {"rid_pair": (RID_A, RID_B)}, "diff_report")
assert decision["action"] == "route"

# 2. G5 transport: fetch both full records
manifest = Manifest(skill="paper-compare", intent_class="diff",
                    dispatch_tuple="(diff,{rid_pair},diff_report)")
sa = fetch_sidecar(RID_A); sb = fetch_sidecar(RID_B)
manifest.returned_rids = [RID_A, RID_B]
manifest.fetch_mode_per_rid = {RID_A: "full", RID_B: "full"}

# 3. G7 + G2' (both records must pass paper-compare's policy)
kept = filter_records([
    {**sa, "stats":{"stmt_count":len(sa.get("statements",[]))}, "coverage_statements":sa.get("coverage",{}).get("statements"), "lint_passed":True, "record_id":RID_A},
    {**sb, "stats":{"stmt_count":len(sb.get("statements",[]))}, "coverage_statements":sb.get("coverage",{}).get("statements"), "lint_passed":True, "record_id":RID_B},
], "paper-compare", manifest)
if len(kept) != 2:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 4. Compute diff (in your LLM head, or use a structured matcher):
#    - shared_claims    : statements with similar text on both sides (cosine ≥ 0.85 OR LLM judge)
#    - divergent_claims : claim on A only OR claim on B only (no semantic match)
#    - contradictions   : A.statement + B.statement linked by predicate `challenged_by` or `supersedes`
#    - shared_citations : intersection of {art:* with role: cited} on both sides

# 5. Format Markdown diff_report:
#    ## Shared claims (N)\n... ## Divergent claims (M)\n... ## Contradictions (K)\n... ## Shared citations (J)
# 6. Manifest: dispatch_tuple, returned_rids=[RID_A,RID_B], fetch_mode_per_rid (both "full"), abstained?
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `diff_report` | Structured Markdown report: shared_claims / divergent_claims / contradictions / shared_citations sections |

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `rid_pair` slot missing or wrong shape (not 2-tuple) | `missing_required_input.rid_pair` / `invalid_slot_type.rid_pair` |
| Either rid returns 404 from hub | `rid_not_found.<rid>` |
| Either record fails G7 profile filter (e.g. one is `review@1`) | `empty_working_set_after_profile_filter` |
| Either record fails G2' quality filter | `empty_working_set_after_quality_filter` |
| `rid_a == rid_b` (self-diff) | `invalid_slot_type.rid_pair` (self-diff is a degenerate case) |

## Manifest emission (G6)

Per G6: `skill: paper-compare`, `intent_class: diff`, `dispatch_tuple: (diff,{rid_pair},diff_report)`, `returned_rids: [a,b]`, `applied_profile_filters: [paper@1]`, `fetch_mode_per_rid: {a:"full", b:"full"}` (G3), abstained reasons as above.

## Out of scope (v1)

- N-way comparison (3+ papers) — use `synthesize_table` instead.
- Cross-profile diff (paper@1 vs review@1) — semantically different; would need its own intent_class.
- LLM-judged semantic similarity for shared_claims — agent-mediated default uses simple text overlap; LLM upgrade is v1.x.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
