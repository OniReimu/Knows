# survey-table — Reference Contract

**Status**: v1.0.

> **Companion**: `sub-skills/survey-table/SKILL.md`. Contract wins on disagreement.
>
> **Canonical LLM prompt**: `survey-table-prompt.md`. Use that prompt verbatim — it operationalizes the contract here (cell-grounding, axis discipline, N/A protocol, > 50% N/A abstain rule) and adds banned marketing cell values + synonym-matching hints so individual agents do not re-derive the rules.

---

## 1. Purpose and scope

Compose a structured comparison table across N papers (rows) on user-supplied axes (columns). Output: Markdown table + LaTeX `tabular` block + per-cell provenance footnotes.

**Out of scope (load-bearing)**:

- Inventing comparison axes — user MUST supply.
- Cross-discipline metric normalization (e.g. converting "F1" to "accuracy" automatically).
- Heatmap / chart visualizations.
- Auto-extraction of axis values from PDFs not yet sidecarred.

---

## 2. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `rid_set` | list[record_id] | yes | 2-20 records (1 = degenerate; > 20 = unreadable) |
| `comparison_axes` | list[string] | yes | 2-8 axes (column headers) |
| `axis_descriptions` | dict[axis, string] | no | Optional clarifications shown to LLM during extraction |

**Validation**:
- `len(rid_set) < 2` → `invalid_slot_type.rid_set` (1-row table is degenerate)
- `len(rid_set) > 20` → `invalid_slot_type.rid_set` (table exceeds readable density)
- `len(comparison_axes) < 2` → `invalid_slot_type.comparison_axes`
- `len(comparison_axes) > 8` → `invalid_slot_type.comparison_axes` (column overflow)
- Empty axis name (whitespace-only) → `invalid_slot_type.comparison_axes`

---

## 3. Output schema

```jsonc
{
  "rids": ["knows:..."],
  "axes": ["dataset", "model_size", "headline_metric"],
  "table_markdown": "<Markdown table string>",
  "table_latex": "\\begin{tabular}{...}\n...\n\\end{tabular}",
  "cells": [
    {
      "rid": "knows:vaswani/...",
      "axis": "dataset",
      "value": "WMT 2014 en-de",
      "provenance": {
        "anchor_id": "stmt:dataset-description | ev:wmt-table",
        "verbatim_quote": "<≤ 30 words>"
      },
      "n_a": false
    }
  ],
  "axis_misses": [{"rid": "...", "axis": "..."}],   // cells where value not found in sidecar (rendered as N/A in table)
  "manifest_path": "<path>"
}
```

**Hard rules**:

- Every cell with `n_a: false` MUST have non-empty `provenance.anchor_id` AND `provenance.verbatim_quote`.
- `verbatim_quote` MUST be a substring of the cited statement's `text` OR evidence's `summary` / observation values (case-insensitive after whitespace normalization).
- Cells with `n_a: true` are rendered as `N/A` or `-` in the table; provenance MAY be empty.
- The Markdown and LaTeX table strings MUST be syntactically valid (parse with a Markdown processor / LaTeX `tabular` regex).

---

## 4. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `rid_set` missing or empty | `missing_required_input.rid_set` |
| `comparison_axes` missing or empty | `missing_required_input.comparison_axes` |
| Either slot wrong type | `invalid_slot_type.<slot>` |
| Any rid in `rid_set` 404s | `rid_not_found.<rid>` (entire table abandoned — partial table is bad UX) |
| `< 2` records pass G7 + G2' filters | `empty_working_set_after_quality_filter` |
| > 50% of cells are N/A across the working set | `skill_runtime_exception.LowCellCoverage` (table mostly empty — user should pick different axes or different rids) |

The "> 50% N/A" rule is critical — it's the signal that the user's axes don't match what these papers report. Better to abstain and ask the user to revise than produce a table that's mostly empty.

---

## 5. Cell extraction contract

For each `(rid, axis)` cell:

```
1. Search rid's statements[] for any statement.text mentioning axis (case-insensitive substring + heuristic synonym match)
2. If statement found: extract value (typically a noun phrase, number, or short fragment); record provenance.anchor_id = stmt:* and verbatim_quote
3. Else search rid's evidence[] for any observation.metric matching axis OR evidence.summary mentioning axis
4. If evidence found: extract value (numeric value+unit, OR qualitative_value); record provenance.anchor_id = ev:* and verbatim_quote
5. Else: cell.value = "N/A", cell.n_a = true
```

The LLM does the extraction; the orchestrator post-validates the verbatim_quote substring match.

**Synonym hints** (built into the LLM system prompt; not user-facing):
- "dataset" ≈ "benchmark", "corpus", "data"
- "model_size" ≈ "parameters", "params", "model parameters"
- "metric" ≈ "accuracy", "F1", "BLEU", "score"
- "method" ≈ "approach", "algorithm", "technique"

---

## 6. Output formatting contract

### 6.1 Markdown table

```markdown
| Paper | dataset | model_size | headline_metric |
|---|---|---|---|
| Vaswani 2017 | WMT 2014 en-de | 213M | 28.4 BLEU |
| Liu 2024 | MedQA | - | 80% token reduction |
```

**Row label**: `{first_author_lastname} {year}` — same derivation as `survey-narrative` citation keys (anonymous → record_id slug).

### 6.2 LaTeX tabular

```latex
\begin{tabular}{lccc}
\toprule
Paper & dataset & model\_size & headline\_metric \\
\midrule
Vaswani 2017 & WMT 2014 en-de & 213M & 28.4 BLEU \\
Liu 2024 & MedQA & -- & 80\% token reduction \\
\bottomrule
\end{tabular}
```

Special-char escaping: `_` → `\_`, `%` → `\%`, `&` → `\&`, `#` → `\#`, `$` → `\$`. Numbers preserved verbatim.

---

## 7. Manifest emission contract

```jsonc
{
  "skill": "survey-table",
  "intent_class": "synthesize_table",
  "dispatch_tuple": "(synthesize_table,{rid_set,comparison_axes},comparison_table)",
  "queries": [],                              // takes rid_set, not query_text
  "returned_rids": [<rid_set>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* frontmatter */ },
  "fetch_mode_per_rid": { /* all "full" — G3 requires_full_record: true */ },
  "model": "<llm>",
  /* skill-specific */
  "n_axes": <int>,
  "n_rows": <int>,
  "n_cells_total": <n_rows * n_axes>,
  "n_cells_n_a": <int>,
  "n_a_rate": <float>                         // n_n_a / n_total; warn if > 0.3, abstain if > 0.5
}
```

---

## 8. Why this contract is load-bearing

Comparison tables in papers are heavily scrutinized — every cell must be defensible. Inventing a value (or pulling one from the wrong record) becomes a fact-checking nightmare for reviewers and a credibility hit for authors.

The substring-match requirement on `verbatim_quote` makes the skill safe — every cell traces to a specific anchor in a specific sidecar. The N/A coverage abstain rule prevents publishing tables that imply false comparability.

