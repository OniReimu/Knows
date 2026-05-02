# Knows Evaluation Results

[English](./evaluation.md) | [中文](./evaluation.zh.md)

> Full experimental results from the Knows technical report. For a 4-line headline, see the main [README](../README.md#evaluation).

## Key Results

<table>
<tr>
<td width="50%">

### Weak Models: +29 to +42pp Accuracy

| Model | PDF | Knows | Improvement |
|:------|----:|------:|:-----------:|
| Qwen3.5-0.8B | 19% | **47%** | **+29pp** |
| Qwen3.5-2B | 25% | **67%** | **+42pp** |

An LLM-as-judge (Claude Sonnet 4) confirms weak models reading sidecars reach **75-77%** accuracy, approaching medium models reading PDFs (78-83%).

</td>
<td width="50%">

### 55% Fewer Tokens, Same Accuracy

| Condition | Accuracy | Tokens | Efficiency |
|:----------|:--------:|-------:|:----------:|
| PDF | 59% | 9,955 | 5.9%/1Ktok |
| **Full Sidecar** | **59%** | **4,463** | 13.2%/1Ktok |
| Stmts-only | 52% | 693 | **75.0%/1Ktok** |

Full sidecar matches PDF accuracy. Statements-only retains 88% accuracy at **93% fewer tokens** (12.7x more efficient).

</td>
</tr>
</table>

### Traceability: 0% (PDF) → 64-91% (Knows)

Agent-generated reviews with Knows reference specific claim/evidence IDs in their weakness sections. PDF reviews contain **zero** per-weakness ID references across all four models tested.

### Cross-Discipline Coverage

Evaluated on **20 papers** across **14 disciplines** (CS, Biology, Chemistry, Physics, Economics, Psychology, Medicine, Education, Philosophy, Mathematics, Civil/Mechanical/Electrical Engineering, Semiconductor). On length-controlled papers (2K-20K words), Knows improves accuracy in **6 of 10 disciplines** for weak models.

---

## Evaluation Summary

Eleven experiments (E1-E10) across 20 papers, 14 disciplines, 8+ LLM agents:

| Experiment | Scope | Key Finding |
|:-----------|:------|:------------|
| **E1** Task Accuracy | 140Q x 20p x 6m x 3 cond | Weak: +29 to +42pp; Strong: -1pp but 64-83% fewer tokens |
| **E2** Token Efficiency | From E1 | 29-83% reduction (MiMO-V2-Flash: 2,856K → 401K) |
| **E3** Latency | From E1 | 3.4-4.6x speedup for local weak models |
| **E4** Review Traceability | 15p x 4m x 2 cond | Per-weakness traceability: 64-91% (Knows) vs 0% (PDF) |
| **E5** Consistency | 15p x 3 injections | Structural: 100% detected; Semantic: 0% (clean boundary) |
| **E6** Cross-Paper | 15p x 4m x 4Q | 4-17x more ID references with Knows |
| **E7** LLM Generation | 5p x 7m | Lint pass: Claude 100%, non-Claude <20%. Haiku 4.5 = Opus quality at 15x less cost |
| **E8** Ablation | 15p x 5 cond x 4m | Full sidecar = PDF accuracy (59%) with 55% fewer tokens |
| **E9** Granularity | 8p x 4 tiers x 2 cond | Dense sidecars (+2.5x stmts): medium +27pp, strong +29pp avg |
| **E9b** Dense+Fallback | 8p x 2m x 2 cond | Fallback marginal for dense sidecars; dense-only is optimal |
| **E10a** Cross-Eval (one-shot) | 5p x 4gen x 2cons | Non-Claude one-shot: 21-50% consumption accuracy |
| **E10b** Cross-Eval (agent) | 20p x 3gen | Opus 88.6%, Haiku-dense 72.9%, Haiku 64.3%. Opus remains quality leader |

### Length Effect

Knows advantage scales with paper length:

| Paper Length | Weak Δ | Medium Δ | Strong Δ |
|:-------------|:------:|:--------:|:--------:|
| SHORT (<2K words) | +8pp | +8pp | +14pp |
| MEDIUM (2-8K) | **+29pp** | -6pp | -5pp |
| STANDARD (8-20K) | **+40pp** | -19pp | -9pp |
| LONG (>20K) | **+57pp** | +13pp | **+17pp** |

### Scoring Robustness

| Model | Keyword Knows | LLM-Judge Knows | PDF (LLM) |
|:------|:------------:|:---------------:|:---------:|
| Qwen3.5-0.8B | 47% | **75%** | 24% |
| Qwen3.5-2B | 67% | **77%** | 25% |

**Weak model + Knows (75-77%) ≈ Medium model + PDF (78-83%)**
