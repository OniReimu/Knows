# Demo: `sidecar-author`

> **What it does**: Generate a KnowsRecord sidecar from your paper. Accepts **PDF** (multimodal LLM, most common real-world input), **LaTeX project** (deterministic pipeline), or **pre-extracted text blob** (LLM-mode).

## User intent (3 typical entry points)

> "Make a sidecar for `vaswani-attention.pdf`."  ← Path F (most common)
> "Generate a sidecar from my LaTeX project at `paper/`."  ← Path A or B
> "Here's the abstract + intro — make me a draft sidecar."  ← Path E

## Dispatch tuple

```
intent_class:        contribute
required_inputs:     {pdf_path: "/papers/vaswani-attention.pdf"}     # or latex_dir, or text_blob — exactly one
requested_artifact:  knows_yaml                                       # or lint_report (validation-only)
                     ↓
                  sidecar-author  →  paper.knows.yaml
```

## What happens under the hood — Path F (PDF input)

The most common real-world workflow. Knows v0.9 paper Appendix D was generated this way (Opus subagent reading the paper PDF + applying `gen-prompt.md`).

```
1. Sub-skill body opens vaswani-attention.pdf via multimodal LLM
   - Anthropic: messages.create with document content block
   - OpenAI: responses.create with file input
   - Gemini: generate_content with Part.from_data
2. System message + user template come from references/gen-prompt.md (load verbatim)
3. LLM produces complete KnowsRecord YAML in one pass
4. Post-gen pipeline:
   sanitize.py raw_output.yaml -o vaswani.knows.yaml      # clean LLM artifacts
   lint.py vaswani.knows.yaml                              # 0-error gate
   verify_metadata.py vaswani.knows.yaml                   # DOI/title/venue check
   verify_metadata.py --auto-enrich vaswani.knows.yaml     # fill missing DOI
5. Provenance: provenance.method = "extraction"
```

## What happens — Path A (LaTeX project, deterministic)

```bash
# Zero API key required
python3 skills/scripts/gen.py paper/main.tex -o vaswani.knows.yaml

# Or with --dense for richer scaffolds
python3 skills/scripts/gen.py paper/main.tex --dense -o vaswani-dense.knows.yaml
```

## What happens — Path B (LaTeX + LLM)

```bash
# Requires ANTHROPIC_API_KEY
python3 skills/scripts/gen.py paper/main.tex --model opus -o vaswani.knows.yaml
# Cost: ~$0.15 per sidecar with Opus, ~$0.01 with Haiku 4.5 (E7 says: Haiku 4.5 = best value)
```

## Artifact: `vaswani.knows.yaml` (truncated)

```yaml
$schema: https://knows.dev/schema/record-0.9.json
knows_version: 0.9.0
profile: paper@1
record_id: knows:vaswani/attention/1.0.0
title: "Attention Is All You Need"
venue: "NeurIPS"
year: 2017
authors:
  - {name: "Ashish Vaswani", affiliation: "Google Brain", role: first}
  - {name: "Noam Shazeer",   affiliation: "Google Brain", role: contributor}
  # ...

statements:
  - id: stmt:transformer-architecture
    statement_type: method
    text: "We propose the Transformer, a model architecture eschewing recurrence..."
    modality: theoretical
  - id: stmt:wmt-en-de-result
    statement_type: claim
    text: "Achieves 28.4 BLEU on WMT 2014 English-to-German..."
    modality: empirical
    confidence: {claim_strength: high, extraction_fidelity: high}
  # ... 14-25 statements total

evidence:
  - id: ev:wmt-table
    evidence_type: table_result
    observations:
      - {metric: bleu, value: 28.4, unit: ""}     # en-de
      - {metric: bleu, value: 41.0, unit: ""}     # en-fr
  # ...

relations:
  - {id: rel:1, subject_ref: stmt:wmt-en-de-result, predicate: supported_by, object_ref: ev:wmt-table}
  # ... typically ratio relations/statements ≥ 1.5

provenance:
  origin: machine
  method: extraction          # PDF Path F
  actor: {type: tool, name: "claude-opus-4-7"}
  generated_at: 2026-04-26T02:30:00Z
```

## Artifact: `lint_report` (when `requested_artifact: lint_report`)

```
✓ Schema validation: PASS (31 root fields, 23 entity defs)
✓ Cross-reference integrity: PASS
✓ ID uniqueness: PASS (47 ids, 0 duplicates)
✓ ID prefix conventions: PASS
✓ citation_intent pairing: PASS
✓ Artifact discoverability: PASS

0 errors, 0 warnings — sidecar is publishable.
```

The lint_report route generates the YAML to a tmp file, runs lint, returns only the summary, discards the YAML. Useful for CI gates and pre-publish checks.

## Quality model selection (E7 results)

| Model | Lint Pass | Consumption Acc (20 papers) | Cost/sidecar |
|---|---|---|---|
| **Opus 4.6** | 100% | **88.6%** | ~$0.15 |
| Sonnet 4.6 | 100% | TBD | ~$0.05 |
| **Haiku 4.5** (dense mode) | 100% | 72.9% | ~$0.01 (best value) |

Non-Claude models (GPT, Gemini) currently have lint pass <20% — schema enum compliance is the hardest part. They work via Path F if the multimodal step is them but generation step routes to Claude.

## Upload to knows.academy (DEFERRED)

`POST /sidecars` is UNVERIFIED in v1.0. The orchestrator refuses upload requests with `upload_disabled_endpoint_unverified` per `dispatch-and-profile.md` §5. Local sidecar production is fully supported; remote upload is a v1.x follow-on once the endpoint is probed.

## Manifest emission (G6)

```json
{
  "skill": "sidecar-author",
  "intent_class": "contribute",
  "dispatch_tuple": "(contribute, {pdf_path}, knows_yaml)",
  "returned_rids": [],
  "applied_profile_filters": [],
  "applied_quality_policy": {
    "require_lint_passed": false,
    "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"],
    "min_statements": 0
  },
  "model": "claude-opus-4-7",
  "metadata_warnings": [],
  "abstained": false
}
```

## Try it yourself

```bash
# Path A — zero API key
python3 skills/scripts/gen.py path/to/your/paper/main.tex -o sidecar.knows.yaml
python3 skills/scripts/lint.py sidecar.knows.yaml

# Path F — via Claude Code with the Knows skill
"Make a Knows sidecar for /Users/me/papers/vaswani-attention.pdf"
```
