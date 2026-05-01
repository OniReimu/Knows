# Knows: Make Any Paper Agent-Ready in Minutes

English | [中文](./README.zh.md)

> **One YAML file. Every claim, every number, every connection — structured, validated, and ready for your AI agent.**

[![Schema](https://img.shields.io/badge/Schema-v0.9-blue)](src/knows_sidecar/schema/knows-record-0.9.json)
[![Papers](https://img.shields.io/badge/Papers-20-green)]()
[![Disciplines](https://img.shields.io/badge/Disciplines-14-orange)]()
[![Platform](https://img.shields.io/badge/Platform-knows.academy-purple)](https://knows.academy)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## Why Knows Exists

Academic publishing is an ivory tower still pretending it's 1995.

We train researchers to write eight-part-essay papers in a format optimized for human eyeballs — and then we feed those same PDFs to AI agents that have to reverse-engineer the structure from prose. Every agent, every time, independently extracts claims, maps evidence to assertions, and resolves citation targets from the same unstructured text. It's lossy, it's duplicated, and it's absurd.

Meanwhile, agents are already the primary interface for consuming research. They review papers, they search literature, they synthesize findings. We are past the point where it makes sense to have humans write natural language for other humans, only to have machines re-parse it.

**The information flow should be inverted.** Content should be authored in the most efficient, structured, token-minimal form — optimized for agents. When a human needs to read it, the agent translates it into natural language. Not the other way around.

That's why we built **Knows**.

Not another paper-writing tool. Not another PDF parser. A **companion standard** that puts structured knowledge first and lets the format serve whoever — or whatever — is reading it.

---

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

## What is Knows?

**Knows** is a YAML sidecar that sits next to your PDF — the structured, agent-native representation of everything your paper claims, proves, and connects:

```
paper.pdf          ← Human artifact (unchanged)
paper.knows.yaml   ← Agent-facing companion
```

Schema-validated. Version-chained. 77% fewer tokens than PDF. No changes to the published artifact required.

```yaml
# paper.knows.yaml
$schema: https://knows.dev/schema/record-0.9.json
knows_version: 0.9.0
profile: paper@1
title: "Deep Residual Learning for Image Recognition"

statements:
  - id: stmt:c1
    statement_type: claim
    modality: empirical
    text: "ResNets achieve 3.57% top-5 error on ImageNet"
    confidence:
      claim_strength: high
      extraction_fidelity: high

evidence:
  - id: ev:imagenet
    evidence_type: table_result
    observations:
      - metric: top5_error
        value: 3.57
        unit: "%"

relations:
  - id: rel:1
    subject_ref: stmt:c1
    predicate: supported_by
    object_ref: ev:imagenet
```

---

## Orchestrator + Researcher Workflows (v1.0+)

Beyond the sidecar spec itself, Knows ships an **orchestrator skill** that routes researcher intent to specialized sub-skills — a ready-made workflow library on top of the [knows.academy](https://knows.academy) hub.

```
User intent → dispatch tuple → sub-skill → artifact
```

**MVP v1.0 (3 sub-skills)** — read-only discovery, downstream Q&A, upstream contribution covered:

| Sub-skill | User says... | Artifact |
|---|---|---|
| `paper-finder` | "find 10 papers on diffusion + privacy" | Ranked table + optional `papers.bib` |
| `sidecar-reader` | "what dataset did Vaswani use?" | JSON answer (consume-prompt v1.1) |
| `sidecar-author` | "make a sidecar from this PDF/LaTeX" | `paper.knows.yaml` (lint-pass + verify-pass) |

**v1.1+ planned** — paper-compare / review-sidecar / survey-narrative / survey-table / next-step-advisor / rebuttal-builder / version-inspector / sidecar-reviser / commentary-builder (v0.10). See [`skills/sub-skills/README.md`](skills/sub-skills/README.md) for the full 12-skill catalog and rollout schedule.

**7 orchestrator guards** (G1–G7) protect against prompt injection, quality leakage, untyped routing, profile contamination, and unbounded fetches. Full contract: [`skills/references/dispatch-and-profile.md`](skills/references/dispatch-and-profile.md).

**Try it** (3 demos) → [`docs/demos/`](docs/demos/) — `paper-finder.md` / `sidecar-reader.md` / `sidecar-author.md`.

---

## Installation

### Python CLI (`knows lint` / `knows gen` / `knows query` / ...)

```bash
pip install knows-sidecar
```

Or with uv:
```bash
uv add knows-sidecar
```

### Agent skills (Claude Code, Codex CLI, ...)

The orchestrator + 12 sub-skills + 11 interaction stances under [`skills/`](skills/) install via [`vercel-labs/skills`](https://github.com/vercel-labs/skills), a universal CLI that supports 50+ agents. The flags below skip the interactive agent/skill picker:

```bash
# Claude Code, project-level (recommended for paper repos)
npx skills add OniReimu/Knows -a claude-code -s '*' -y

# Claude Code, global (available across all projects)
npx skills add OniReimu/Knows -g -a claude-code -s '*' -y

# Codex CLI
npx skills add OniReimu/Knows -a codex -s '*' -y

# Both Claude Code and Codex CLI at once
npx skills add OniReimu/Knows -a claude-code -a codex -s '*' -y

# Install to every supported agent
npx skills add OniReimu/Knows --all
```

Without the `-a` and `-s` flags, the CLI opens an interactive picker that lists all 50+ supported agents and all 24 skills in this repo — use `--all` or the explicit flags above to skip it.

## CLI Usage

```bash
# Validate a sidecar
knows lint paper.knows.yaml

# Generate a scaffold from LaTeX
knows gen paper/main.tex -o paper.knows.yaml

# Analyze a sidecar
knows analyze paper.knows.yaml

# Query a paper using only its sidecar
knows query paper.knows.yaml "What is the main contribution?"

# Generate a structured review
knows review paper.knows.yaml -o review.knows.yaml

# Compare two papers
knows compare paper1.knows.yaml paper2.knows.yaml
```

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

---

## KnowsRecord Schema (v0.9)

30 root-level fields, 23 entity definitions, extensible via `x_extensions`.

```
KnowsRecord
  ├─ artifacts[]        paper, repository, dataset, model, benchmark, software, website, other
  ├─ statements[]       claim | assumption | limitation | method | question | definition
  │   modality:         empirical | theoretical | descriptive | normative
  │   confidence:       claim_strength × extraction_fidelity
  ├─ evidence[]         table_result | figure | experiment_run | proof | case_study | observation | ...
  │   observations[]:   value (numeric) OR qualitative_value (string)
  ├─ relations[]        supported_by | challenged_by | depends_on | limited_by | cites
  ├─ actions[]          optional executable hooks with safety policy
  ├─ provenance         origin, actor, method, verification
  ├─ replaces           record_id of previous version (version chain)
  ├─ version            spec × record × source
  └─ freshness          as_of, update_policy, stale_after
```

### Review-as-Sidecar

Reviews are also KnowsRecords (`profile: review@1`). Each weakness links to specific original claims via cross-record references:

```yaml
relations:
  - subject_ref: "knows:examples/resnet/1.0.0#stmt:a1"
    predicate: challenged_by
    object_ref: "stmt:w1"  # this review's weakness
```

---

## Examples

21 example sidecars across 14 disciplines in [`examples/`](examples/):

| Discipline | Papers | Key Feature |
|:-----------|:-------|:------------|
| CS | ResNet, DP-SGD | Quantitative benchmarks, privacy analysis |
| Biology | Watson-Crick, Mendel | Qualitative evidence, genetic ratios |
| Chemistry | Mendeleev, Pauling | Pattern recognition, bond theory |
| Physics | Einstein | Theoretical predictions |
| Economics | Akerlof | Theoretical model |
| Psychology | Kahneman | Behavioral experiments |
| Medicine | Semmelweis | Clinical observation |
| Education | Bloom, Dewey | Expert classification |
| Philosophy | Gettier, Turing | Thought experiments |
| Mathematics | Godel | Pure proof |
| Civil Eng. | Terzaghi | Lab tests + theory |
| Mech. Eng. | Reynolds | Dye experiments |
| EE | Shannon | Mathematical proofs |
| Semiconductor | Moore, Dennard | Empirical extrapolation |

---

## Tooling

### `knows-lint` — 7 validation checks
1. JSON Schema validation
2. Cross-reference integrity
3. ID uniqueness
4. ID prefix conventions (`art:`, `stmt:`, `ev:`, `rel:`)
5. Relation predicate constraints
6. Artifact discoverability
7. Optional URL liveness

Catches **100% of structural corruption**. Semantic corruption (wrong values) requires future LLM-based verification.

### `knows-gen` — LaTeX to scaffold
- Handles nested `\input{}` (recursive, up to 10 levels)
- Multi-format author parsing (acmart, NeurIPS, IEEEtran)
- Extended citation commands
- ~15 minutes to complete a scaffold for a typical conference paper

---

## Two Operating Modes

| Mode | When | How |
|:-----|:-----|:----|
| **Knows-only** | Agent-native workflow | Agent reads sidecar only. 29-83% fewer tokens. |
| **Knows+Fallback** | Retrofit existing papers | Sidecar first, PDF if insufficient. Best accuracy for 5/6 models. |

---

## Quick Start

```bash
pip install knows-sidecar

# Generate sidecar from LaTeX
knows gen paper/main.tex -o paper.knows.yaml

# Fill in TODOs (~15 min)
# Validate
knows lint paper.knows.yaml

# Your paper is now agent-ready.
```

---

## Citation

```bibtex
@misc{yu2026knowsagentnativestructuredresearch,
      title={Knows: Agent-Native Structured Research Representations}, 
      author={Guangsheng Yu and Xu Wang},
      year={2026},
      eprint={2604.17309},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2604.17309}, 
}
```

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

Copyright 2026 The Knows Authors. Licensed under the Apache License, Version 2.0.
