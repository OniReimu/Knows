---
name: survey-shape
description: >
  Pre-survey scaffolding posture. Use when user says "help me shape this
  survey on X", "what's the right narrative arc for a related-work
  paragraph on Y", "which axes should I compare these N papers on", "I'm
  about to write a survey but don't know how to organize it", or invokes
  /survey-shape. Do NOT use for "draft me a related-work paragraph on X" —
  that routes directly to survey-narrative or survey-table. Stays active
  across turns; exits on emit_chain=[survey-shape, survey-narrative] or
  [survey-shape, survey-table].
---

# survey-shape

A posture for deciding the SHAPE of a survey before writing prose or filling table cells. The shape decision is the load-bearing call — once narrative arc / comparison axes are wrong, the writing wastes itself.

## Two outputs, one posture

A survey can be:
- **Prose** (related-work paragraph or section) — needs a narrative arc + centerpiece papers
- **Table** (comparison matrix) — needs comparison axes + a row inclusion rule

This stance handles either. The decision branches at handoff.

## For prose: arc decision

Help the user pick ONE of these archetypal arcs:

| Arc | When | Centerpiece structure |
|---|---|---|
| `chronological` | Field has a clear historical progression | Earliest pioneer → key inflection → current state |
| `methodological` | Field has 2-3 method families that compete | Family A vs Family B vs Family C, with neutral framing |
| `outcome-grouped` | Different methods optimize different metrics | Group by what they optimize, then within group by approach |
| `gap-driven` | The user's own work attacks an unaddressed gap | Survey ends with the gap your paper fills (rhetorically prep for the contribution) |
| `consolidating` | A theoretical lens unifies seemingly disparate work | State the lens, then re-cast each prior work through it |

Force a pick. "All of the above" is not an arc.

Then identify 3-5 centerpiece papers. A centerpiece is a paper the arc would collapse without — not the most-cited paper, the most-LOAD-BEARING paper. The user usually picks too many; help them cut.

## For table: axis decision

Help the user pick 4-7 comparison axes that:
1. Discriminate (every column has at least 2 distinct values across rows — no constant columns)
2. Are auditable (each cell can be filled from a paper@1 sidecar without speculation)
3. Matter to the user's audience (e.g., "private compute hours" for a DP audience, but not for a generic ML audience)

Reject axes like "novelty" or "impact" — they're judgment columns, not comparison columns.

Force the user to commit to a row inclusion rule: which papers are IN the comparison and which are NOT, and why. Surveys that include 50 papers without a stated inclusion rule are reading-list dumps.

## Anti-pad rules

- For prose: 5 centerpieces max. If the user wants 8, force them to articulate why each is load-bearing for the chosen arc; usually 2-3 fall away.
- For table: 7 axes max. If the user wants 10, force them to demonstrate each discriminates — usually 2-3 don't.
- Never let the user proceed with axes / centerpieces that aren't specifiable from existing paper@1 sidecars on the hub. If a centerpiece paper has no sidecar, it'll need one before survey-narrative / survey-table runs.

## Multi-turn until convergence

Per turn, propose or refine the arc/axes + your reasoning. User pushes back, narrows, swaps. Walk down: arc → centerpieces → row scope → audience. By turn 3 the shape should be locked.

## Handoff

For prose-target chains, emit:

```yaml
brainstorm_summary:
  schema: brainstorm-v1
  emit_chain: [survey-shape, survey-narrative]
  status: ready
  arc: methodological                       # one of the 5 archetypes
  arc_rationale: "<1-2 sentences>"
  centerpieces:
    - rid: knows:examples/...
      role: pioneer | inflection | foil | bridge | culmination
      load_bearing_reason: "<1 sentence — why this arc collapses without it>"
  audience: "<3-5 word audience descriptor — e.g., 'NeurIPS DP-DL community'>"
  word_budget: 300                          # target prose length
  human_confirmations: [...]
  rework_needed: []
```

For table-target chains, emit:

```yaml
brainstorm_summary:
  schema: brainstorm-v1
  emit_chain: [survey-shape, survey-table]
  status: ready
  comparison_axes:
    - name: "method family"
      type: categorical
      auditable: true
      values_seen: ["clip-then-noise", "subsample-aggregate", "PATE"]
    - name: "compute hours"
      type: numeric
      auditable: true
      unit: "GPU-hours"
  row_inclusion_rule: "Published in {NeurIPS, ICML, ICLR, S&P, CCS} 2018-2025 with a paper@1 sidecar on knows.academy"
  expected_row_count: 8
  centerpieces: [<rids>]
  human_confirmations: [...]
  rework_needed: []
```

Fail-closed: arc not in the 5 archetypes / axes lacking discriminative or auditable property / centerpiece without a sidecar → `status: needs_rework`.

## Out of scope

- Writing the prose / filling the table — survey-narrative and survey-table do that. Hand off via brainstorm_summary.
- Long-form survey papers (10+ pages) — this stance optimizes for paragraph or single-table units. Long surveys need their own architecture.
- Bibliography management — the chain assumes papers already have sidecars on the hub.

Related: [`../README.md`](../README.md) | [`../../sub-skills/survey-narrative/SKILL.md`](../../sub-skills/survey-narrative/SKILL.md) | [`../../sub-skills/survey-table/SKILL.md`](../../sub-skills/survey-table/SKILL.md)
