---
name: knows-survey-table
description: "Build a structured side-by-side comparison table across multiple papers on user-supplied dimensions (e.g., dataset, method, accuracy, year) — outputs Markdown plus LaTeX tabular. Triggers: 'compare these 5 papers in a table', 'make a comparison matrix showing X by accuracy and parameters', 'summarize these sidecars side-by-side', 'put these papers in a table comparing dataset and result', 'spreadsheet view of these papers', 'feature matrix across these references'. Use when the user wants a structured comparison; use survey-narrative instead when they want flowing prose."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: synthesize_table
required_inputs:
  - rid_set                         # list of record_ids to tabulate (3-12 typical, hard cap at 20)
  - comparison_axes                 # list[string] — user-supplied column headers (e.g. ["dataset", "metric", "method"])
optional_inputs:
  - brainstorm_summary              # OPTIONAL fenced YAML block produced by the `survey-shape` stance (Type B, v0.11+). When present, the skill switches to CONSUME MODE — uses stance-locked comparison_axes + row_inclusion_rule + centerpieces instead of taking them from required_inputs. If brainstorm_summary is supplied, the rid_set + comparison_axes required_inputs are derived from it (the user no longer needs to pass them separately). Schema: `brainstorm-v1` with `emit_chain: [survey-shape, survey-table]`.

requested_artifacts:
  - comparison_table                # Markdown table + LaTeX tabular block

# Profile contract — G7
accepts_profiles: [paper@1]

# Quality policy — G2'
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (need full records: extracting axis values means scanning statements + evidence)
requires_full_record: true

# emits_profile omitted — comparison_table is prose/table, not a sidecar artifact (read-only)
---

# survey-table — Structured comparison table across N papers

Different from `survey-narrative` (flowing prose) — this produces a **structured table** on user-defined axes. The orchestrator will NOT invent the axes; user MUST supply them.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_search, fetch_sidecar, filter_records, Manifest, run_paper_finder

# 0. Resolve user-supplied paper names → hub RIDs (most users give names, not RIDs).
#    If the user already supplied RIDs, skip this step. If they gave paper names,
#    run paper-finder per name and take the top hit. If a paper isn't on the hub
#    (common for canonical pre-2024 work), abstain rather than substitute a random
#    hub neighbor — wrong-paper output is worse than no output.
USER_PAPER_NAMES = ["FlashAttention Dao 2022", "PagedAttention Kwon 2023", "StreamingLLM Xiao 2023"]
RIDS = []
missing = []
for name in USER_PAPER_NAMES:
    hits = fetch_search(name, limit=1).get("results", [])
    if hits:
        RIDS.append(hits[0]["record_id"])
    else:
        missing.append(name)
if missing:
    print({"abstained": True, "reason": "hub_missing_canonical_papers",
           "detail": f"not in hub: {missing}; user must supply RIDs directly OR fall back to grounded web search"})
    raise SystemExit

# 1. Dispatch tuple (RIDS now resolved, axes user-supplied)
AXES = ["dataset", "model_size", "headline_metric"]

decision = dispatch("synthesize_table", {"rid_set": RIDS, "comparison_axes": AXES}, "comparison_table")
assert decision["action"] == "route"

# 2. G5 + G7 + G2': fetch full records, filter
manifest = Manifest(skill="survey-table", intent_class="synthesize_table",
                    dispatch_tuple="(synthesize_table,{rid_set,comparison_axes},comparison_table)",
                    returned_rids=RIDS)
sidecars = []
for rid in RIDS:
    sc = fetch_sidecar(rid)
    sidecars.append({**sc, "stats":{"stmt_count":len(sc.get("statements",[]))},
                     "coverage_statements":sc.get("coverage",{}).get("statements"),
                     "lint_passed":True, "record_id":rid})
    manifest.fetch_mode_per_rid[rid] = "full"
kept = filter_records(sidecars, "survey-table", manifest)
if len(kept) < 2:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 3. LLM call — use the canonical prompt from `../../references/survey-table-prompt.md`.
#    The prompt locks in: cell-grounding contract (every n_a=false cell substring-matches
#    a real stmt:*/ev:* anchor), axis discipline (no added/dropped columns), N/A protocol
#    (mark N/A rather than guess), banned marketing cell values ("various", "multiple",
#    "depends on", "TBD", etc.), unit-preservation rule, and synonym-matching hints for
#    common axis labels (dataset/benchmark, model_size/parameters, etc.).
#    Do NOT re-derive these per agent — use the canonical prompt verbatim.
#    Run the post-LLM cell-grounding + axis-discipline + > 50% N/A coverage checks.

# 4. Render the Markdown + LaTeX tables from the JSON cells per the prompt's §7 templates.
#    Row labels via cite_key() helper (e.g. "Vaswani 2017"). Provenance footer required
#    when N/A rate > 20%.

# 5. Manifest finalize: returned_rids, fetch_mode_per_rid (all "full"), n_axis_misses logged
manifest.model = "claude-opus-4-7"
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `comparison_table` | Markdown table (rows=papers, columns=axes) + LaTeX `tabular` block + per-cell provenance footnotes |

## Hard rule: user supplies axes

The orchestrator will NOT invent comparison axes. If user says "make a table" without specifying axes, the dispatcher emits clarification asking for them. After clarification, if still unspecified → abstain `missing_required_input.comparison_axes`.

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `rid_set` missing or empty | `missing_required_input.rid_set` |
| `comparison_axes` missing or empty | `missing_required_input.comparison_axes` |
| Either slot wrong type (e.g. `comparison_axes` is string not list) | `invalid_slot_type.<slot>` |
| Any rid 404s | `rid_not_found.<rid>` (table abandoned — partial table is bad UX) |
| `< 2` records pass G7 + G2' (a 1-row "table" is degenerate) | `empty_working_set_after_quality_filter` |
| > 20 rids supplied (hard cap, table exceeds readable density) | `invalid_slot_type.rid_set` |

## Manifest emission

Per G6: `skill: survey-table`, `intent_class: synthesize_table`, `dispatch_tuple`, `queries: []` (this skill takes rid_set, not query_text), `returned_rids: <RIDS>`, `applied_profile_filters: [paper@1]`, `applied_quality_policy`, `fetch_mode_per_rid: {<rid>: "full"}` (G3 requires full), `model`, plus skill-specific `axis_misses` field listing (rid, axis) pairs where value was N/A.

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A)

When invoked downstream of the `survey-shape` stance (Type B), survey-table receives a `brainstorm_summary` carrying user-locked `comparison_axes` + `row_inclusion_rule` + `centerpieces`. CONSUME MODE replaces the user-typed `rid_set` + `comparison_axes` inputs with the stance-locked versions.

### Why CONSUME MODE matters here

Solo survey-table makes the user supply both the rid_set AND the comparison_axes upfront — but the user often doesn't know yet which axes are discriminative or which papers belong in scope. survey-shape negotiates these decisions through dialogue, with the discriminative + auditable axis tests applied in real-time. Consume mode preserves the negotiated outcome.

### CONSUME MODE flow

```python
if brainstorm_summary is None:
    # SOLO MODE — current v0.10 path. User supplied rid_set + comparison_axes directly.
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
    assert summary["emit_chain"][-1] == "survey-table"

    rework_needed = []
    # Verify comparison_axes (4-7 per stance contract)
    axes = summary.get("comparison_axes", [])
    if not (4 <= len(axes) <= 7):
        rework_needed.append({"reason": f"comparison_axes count must be 4-7; got {len(axes)}"})
    for ax in axes:
        if not ax.get("auditable"):
            rework_needed.append({"reason": f"axis {ax.get('name')!r} marked NOT auditable — cannot fill from sidecars"})
        if ax.get("type") not in {"categorical", "numeric", "boolean", "string"}:
            rework_needed.append({"reason": f"axis {ax.get('name')!r} has invalid type"})
    # Verify centerpieces present + row_inclusion_rule stated
    if not summary.get("row_inclusion_rule"):
        rework_needed.append({"reason": "row_inclusion_rule MUST be explicit (no implicit reading-list dumps)"})
    if not summary.get("centerpieces") or len(summary["centerpieces"]) < 3:
        rework_needed.append({"reason": "need ≥3 centerpieces (a 2-row table is degenerate)"})

    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed}

    # Override skill inputs with stance-locked versions
    centerpiece_rids = [cp["rid"] for cp in summary["centerpieces"]]
    comparison_axes_names = [ax["name"] for ax in summary["comparison_axes"]]
    kept = filter_records(fetch_sidecars_by_rids(centerpiece_rids), "survey-table", manifest)
    table_md, table_tex = render_comparison_table(kept, axes=summary["comparison_axes"],
                                                   row_inclusion_rule=summary["row_inclusion_rule"])
    manifest["workflow_chain"] = summary["emit_chain"]   # ["survey-shape", "survey-table"]
```

### Field mapping (brainstorm_summary → comparison_table)

| brainstorm_summary field | survey-table use |
|---|---|
| `comparison_axes[*].name` | column header |
| `comparison_axes[*].type` | cell-extraction strategy (numeric / categorical / boolean / string) |
| `comparison_axes[*].auditable` | gate — non-auditable axes are rejected at consume-mode entry |
| `comparison_axes[*].values_seen` | seed for cell extraction (LLM matches sidecar content against expected values) |
| `comparison_axes[*].unit` | added to numeric cells (e.g. "GPU-hours") |
| `row_inclusion_rule` | added as a Markdown footnote: "Rows: ${rule}" — explicit scope statement |
| `centerpieces[*].rid` | rid_set for the table |
| `centerpieces[*].load_bearing_reason` | available as tooltip / footnote per row (optional rendering) |
| `expected_row_count` | sanity check vs actual centerpiece count; mismatch → warn |
| `emit_chain` | manifest workflow_chain |

### Discriminative-axis post-check (v0.11 invariant)

Before emitting, verify each axis actually discriminates: for the `kept` rid_set, every column must have ≥2 distinct values. If a column has all identical values, it's not a discriminator — emit a warning and recommend dropping the axis. (survey-shape was supposed to enforce this, but the stance only saw `values_seen` from the user; the actual sidecar content may differ. Emitter double-checks.)

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| `status: needs_rework` | `action: return_to_stance` |
| `comparison_axes` count outside 4-7 | `action: return_to_stance` |
| Any axis `auditable: false` | `action: return_to_stance` |
| Missing `row_inclusion_rule` | `action: return_to_stance` |
| `< 3` centerpieces | `action: return_to_stance` (degenerate table) |
| `emit_chain` does NOT end with `survey-table` | `invalid_slot_type.brainstorm_summary` (likely meant survey-narrative) |

## Out of scope (v1.2)

- LLM-suggested axes — explicit user input required (anti-hallucination guard).
- Heatmap / chart rendering — output is text table only; visualization is a separate concern.
- Cross-discipline normalization (e.g. converting "f1" and "accuracy" into a common metric) — N/A reported.
- Automatic axis-value extraction from PDF if sidecar lacks it — Path F upstream (sidecar-author).

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
