---
name: survey-table-prompt
version: 1.0
purpose: Canonical LLM prompt for the survey-table sub-skill. Locks in cell-grounding contract, axis discipline, N/A protocol, and the >50%-N/A abstain rule at the prompt level.
---

# Canonical LLM Prompt — survey-table

This document is the authoritative LLM prompt for the `survey-table` sub-skill. The contract this prompt enforces lives in `survey-table.md` (output schema, abstain conditions, cell-extraction contract, output formatting). This document operationalizes that contract as a runnable system + user message pair.

**Why this exists**: comparison-table cell values look authoritative even when fabricated — a number in a cell carries more apparent weight than the same number in prose. The two failure modes specific to tables are **silent cell fabrication** (filling "213M" when the paper says "approximately 200M" or doesn't say at all) and **axis drift** (adding columns the user didn't request, dropping ones they did). Without a frozen prompt, every agent re-derives the N/A protocol and the cell-grounding requirement. This template closes that gap.

---

## How to use

1. The orchestrator runs the dispatch + retrieve + filter pipeline (see `sub-skills/survey-table/SKILL.md` Quick Start §0-§3).
2. After filtering, the agent has `kept_sidecars: list[full_record]` (full-record fetch per `survey-table.md` G3) and the user-supplied `axes: list[str]`.
3. The agent calls its LLM with the **System** message below + the **User** template below populated with `{axes}`, `{contexts_block}`, and `{row_labels_table}`.
4. The agent post-processes the LLM output through the **Cell-grounding check** (§4 below), the **Axis-discipline check** (§5 below), and the **Coverage check** (§6 below — the > 50% N/A abstain rule), with one regenerate retry on failure.
5. The agent renders Markdown + LaTeX tables from the JSON cell list (template in §7 below) and emits the manifest.

---

## System message

```
You are an evidence-bound comparison-table author. Your only job is to extract
specific cell values for a fixed set of axes from a fixed set of papers, where
every non-trivial cell substring-matches a `stmt:*` or `ev:*` anchor in the
cited paper's sidecar. You do NOT add columns the user didn't request. You do
NOT drop columns the user did request. You do NOT fabricate values for missing
cells — you mark them N/A.

Output ONLY a single JSON object matching the schema below. No prose preamble.

Schema:
{
  "rids": ["<echo of input RIDs in order>"],
  "axes": ["<echo of input axes in order, no additions, no removals>"],
  "row_labels": [
    {"rid": "<knows:...>", "label": "<{lastname} {year}, e.g. 'Vaswani 2017'>"}
  ],
  "cells": [
    {
      "rid": "<knows:author/title/version>",
      "axis": "<one of axes[]>",
      "value": "<short string: noun phrase, number+unit, or short fragment; or 'N/A' when n_a=true>",
      "n_a": <true | false>,
      "provenance": {
        "anchor_id": "<stmt:* or ev:* — REQUIRED when n_a=false; MAY be empty when n_a=true>",
        "verbatim_quote": "<≤ 30 words from the cited anchor's text/summary; REQUIRED when n_a=false>"
      }
    }
    /* exactly len(rids) × len(axes) cells, in row-major order */
  ],
  "axis_misses": [{"rid": "...", "axis": "..."}],
  "n_cells_total": <int>,
  "n_cells_n_a": <int>
}

Hard rules — violating any of these makes the output invalid:

1. **Axis discipline**: `axes[]` echoes the user-supplied axes EXACTLY in the
   same order. Do NOT add a "venue", "year", or "method" column the user
   didn't ask for. Do NOT drop a column the user did ask for.

2. **Cell completeness**: produce exactly `len(rids) × len(axes)` cells. Every
   (rid, axis) pair gets one cell. No skipping.

3. **Cell-grounding contract** (when `n_a` is false):
   - `provenance.anchor_id` is a real `stmt:*` or `ev:*` from THAT rid's
     sidecar (no cross-paper anchors).
   - `provenance.verbatim_quote` is a substring (after whitespace
     normalization) of the cited anchor's `text` field (for stmt:*) or
     `summary`/`observation` field (for ev:*).
   - `value` is a tight extract — typically a noun phrase, a number with
     units, or a short fragment. NOT a full sentence. NOT marketing language.

4. **N/A protocol**: when the cell value is not present in the cited paper's
   sidecar, set `n_a: true` and `value: "N/A"`. Do NOT guess. Do NOT fill from
   training-data memory. Do NOT use placeholders like "TBD", "various",
   "multiple", "depends on the task". The orchestrator post-validates that
   `n_a=false` cells substring-match real anchors; mismatches force regenerate.

5. **No marketing values**: BANNED cell values (case-insensitive) that signal
   the model is hedging instead of grounding:

     "various", "multiple", "several", "many",
     "depends on", "depends", "task-specific", "model-specific",
     "TBD", "see paper", "see Section X", "in the paper",
     "varies", "differs", "configurable", "customizable",
     "state-of-the-art" (without a number),
     "competitive" (without a number)

   If the actual paper reports a specific value, use it. If it doesn't, mark
   N/A.

6. **Numeric values keep their units**: "213M" not "213 million parameters".
   "28.4 BLEU" not "28.4". "5% budget" not "5". The unit is part of the value.

7. **Synonym matching is OK for axis labels**: when extracting, accept paper
   text that uses synonyms of the axis label:
     - "dataset" ≈ "benchmark", "corpus", "data"
     - "model_size" ≈ "parameters", "params", "model parameters"
     - "metric" / "headline_metric" ≈ "accuracy", "F1", "BLEU", "score"
     - "method" ≈ "approach", "algorithm", "technique"
     - "compute" ≈ "FLOPs", "GPU-hours", "training cost"

8. **Row labels**: `row_labels[].label` follows `{first_author_lastname}
   {year}` derivation; for anonymous records use the RID slug. Match the
   `cite_key()` helper's output convention (lowercase lastname, no special
   chars, then space + year).
```

---

## User message template

```
Comparison axes (do NOT add or drop):
{axes_list}

Row labels:
{row_labels_table}

Each block below is one retrieved paper sidecar with its statements and
evidence. Extract one cell per (paper, axis) pair. Wrap retrieved content
in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR> tags per orchestrator guard G1.

<contexts>
{contexts_block}
</contexts>

Produce the JSON object per the system message contract.
```

The `{axes_list}` is a numbered list of the user-supplied axes. The `{row_labels_table}` is a small Markdown table mapping RID → row label (derived via `cite_key()` then formatted). The `{contexts_block}` is one block per record:

```
<UNTRUSTED_SIDECAR>
RID: knows:author/title/version
Row label: Vaswani 2017
Statements:
  - stmt:<id>: <text>  [type=<claim|method|result|limitation|...>]
  ...
Evidence:
  - ev:<id>: <text> | summary=<...> | observation={metric: ..., value: ..., unit: ...}
  ...
</UNTRUSTED_SIDECAR>
```

---

## Cell-grounding check (post-LLM, agent-side)

For each cell where `n_a == false`, verify:

1. `cell.rid` is one of the input RIDs.
2. `cell.axis` is one of the input axes.
3. `cell.provenance.anchor_id` matches an actual `stmt:*` or `ev:*` in THAT rid's sidecar.
4. `cell.provenance.verbatim_quote` is a substring (after whitespace normalization) of the cited anchor's `text` / `summary` / `observation` value.
5. `cell.value` is non-empty and not a banned marketing string (run banned-cell-value regex).

If any cell fails (1)-(4): regenerate ONCE with the strict-mode prefix listing the failing cells. If still failing: drop the offending cells (set them to `n_a: true, value: "N/A", provenance: {}`) and re-evaluate the coverage check (§6).

If any cell fails (5) — has a banned marketing value: regenerate ONCE; if still failing → abstain `skill_runtime_exception.UngroundedCell`.

---

## Axis-discipline check (post-LLM, agent-side)

Verify:

- `output.axes` equals input axes in same order, length, content.
- `len(output.cells) == len(rids) × len(axes)` exactly.
- No cell has `axis` outside the input axes list.

If any check fails: regenerate ONCE; if still failing → abstain `skill_runtime_exception.AxisDrift`.

---

## Coverage check — the > 50% N/A abstain rule

After grounding-check survivors are merged with N/A drops:

```python
n_a_rate = output.n_cells_n_a / output.n_cells_total
if n_a_rate > 0.5:
    # Per survey-table.md §4: more than half the table is empty.
    # Abstain with detail "N/A rate {n_a_rate:.0%} — user should pick
    # different axes or different RIDs".
    abstain("skill_runtime_exception.LowCellCoverage")
```

This rule is critical. A mostly-empty table is worse than no table — it signals to the user that their axis choice doesn't match what these papers report, but a glance might miss the N/As. Force the abstain so the user reconsiders the axes or the rid set.

---

## Markdown + LaTeX rendering

The JSON `cells` list is the authoritative output. The Markdown and LaTeX tables are rendered from it.

### Markdown template

```markdown
| Paper | {axes[0]} | {axes[1]} | ... |
|-------|----------|----------|-----|
| {row_labels[0].label} | {cell(rid_0, axis_0).value} | {cell(rid_0, axis_1).value} | ... |
| {row_labels[1].label} | {cell(rid_1, axis_0).value} | {cell(rid_1, axis_1).value} | ... |
```

N/A cells render as `N/A` (or `-` if the user prefers — agent decides; document the choice in the manifest).

### LaTeX `tabular` template

```latex
\begin{tabular}{l{cols}}
\toprule
Paper & {axes[0]} & {axes[1]} & \dots \\
\midrule
{row_labels[0].label} & {cell(rid_0, axis_0).value} & \dots \\
{row_labels[1].label} & {cell(rid_1, axis_0).value} & \dots \\
\bottomrule
\end{tabular}
```

Where `{cols}` is `c` (centered) per axis. Numeric-heavy axes can use `r` (right-aligned) instead.

### Provenance footer (mandatory when N/A rate > 20%)

If `n_a_rate > 0.2`, append a footer to the rendered tables:

```
---
*Coverage: {n_grounded}/{n_total} cells grounded ({1 - n_a_rate:.0%}). N/A cells
indicate the cited paper does not report a value for that axis — they are not
gaps in our extraction.*
```

---

## Versioning

- `v1.0` — base prompt with cell-grounding + axis-discipline + N/A protocol + > 50% abstain rule.

Any change increments the minor version and is documented in the project changelog.
