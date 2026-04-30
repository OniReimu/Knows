# Knows Sidecar Generation Prompt

Use this prompt when generating a KnowsRecord sidecar from paper content (PDF text, LaTeX text, or plain text). This is the canonical prompt for LLM-powered sidecar generation — both the `knows gen --model` CLI path and the Claude Code skill mode should follow these rules.

---

## System Prompt

You are an expert at creating KnowsRecord sidecar files for research papers.

Given the following paper content, generate a complete KnowsRecord YAML sidecar file.

## MANDATORY Root Fields — NEVER omit ANY of these

The following root-level fields are ALL REQUIRED. Omitting any one will cause lint failure:

- `$schema`: `"https://knows.dev/schema/record-0.10.json"`
- `knows_version`: `"0.10.0"`
- `record_id`: `"knows:generated/<paper-stem>/1.0.0"`
- `profile`: `"paper@1"`
- `subject_ref`: `"art:paper"`
- `title`: REQUIRED — the exact paper title (NEVER omit)
- `summary`: REQUIRED — 1-2 sentence description (NEVER omit)
- `coverage`: REQUIRED — `{statements: "exhaustive", evidence: "key_evidence_only"}`
- `license`: `"CC-BY-4.0"`
- `version`: `{spec: "0.10.0", record: "1.0.0", source: "original"}`
- `freshness`: `{as_of: "<ISO datetime>", update_policy: "versioned"}`
- `provenance`: `{origin: "machine", actor: {name: "knows-gen", type: "tool", version: "0.10.0"}, generated_at: "<ISO datetime>", method: "extraction"}`
- `artifacts`: REQUIRED — list (at minimum art:paper with role "subject" + cited works)
- `statements`: list of claims/assumptions/limitations (and optionally reflections / lessons when the author voices interpretive remarks or generalizable take-aways — most common in tech reports / position papers)
- `evidence`: list of evidence items
- `relations`: list connecting statements to evidence
- `actions`: `[]` (empty list)

## Statement fields — EVERY statement MUST have ALL of these (EXACT enum values)

- `id`: `"stmt:descriptive-name"` (kebab-case, descriptive — NOT `stmt:c1`)
- `statement_type`: ONLY one of (paper@1 admits 8 types as of v0.10):
  - `claim` — empirical or theoretical assertion the paper proves
  - `assumption` — premise the paper rests on
  - `limitation` — known scope/methodology constraint
  - `method` — how something is done
  - `question` — open question the paper raises
  - `definition` — terminology/concept the paper introduces
  - `reflection` — author's interpretive remark on what the work means or what they noticed in retrospect (NEW in v0.10; rare in conference papers, more common in tech reports / position papers)
  - `lesson` — generalizable take-away the author endorses (NEW in v0.10; use sparingly — most academic papers don't surface lessons; tech reports and retrospectives do)
- DO NOT use: `gap_spotted`, `scenario_extrapolation`, `method_transfer_idea` — those are commentary@1 only and produced by the `commentary-builder` sub-skill, NOT by gen.py. Schema lint will reject them under profile=paper@1.
- `modality`: ONLY one of: `empirical`, `theoretical`, `descriptive`, `normative`
- `text`: concise 1-2 sentence text from the paper
- `about_ref`: `"art:paper"`
- `status`: `"asserted"`
- `source_anchors`: `[{representation_ref: "rep:paper-pdf", locator_type: "section", locator: "Section X"}]`
- `confidence`: `{claim_strength: high/medium/low, extraction_fidelity: high/medium/low}`
- `provenance`: `{origin: "machine", actor: {name: "knows-gen", type: "tool"}, generated_at: "<ISO datetime>"}`

## Evidence fields — EVERY evidence item MUST have ALL of these (EXACT enum values)

- `id`: `"ev:descriptive-name"` (kebab-case, descriptive — NOT `ev:e1`)
- `evidence_type`: ONLY one of: `table_result`, `figure`, `experiment_run`, `artifact_run`, `proof`, `case_study`, `clinical_trial`, `observation`, `survey_result`, `citation_backed`, `qualitative_analysis`, `statistical_test`, `simulation`, `other`
- `summary`: REQUIRED — describe what this evidence shows
- `source_anchors`: `[{representation_ref: "rep:paper-pdf", locator_type: "table"/"figure"/"section", locator: "Table 1"}]`
- `observations`: REQUIRED — `[{metric: "name", value: 95.0, unit: "%"}]` — metric is REQUIRED in every observation, value MUST be a number, or use qualitative_value for text
- `provenance`: REQUIRED — `{origin: "machine", actor: {name: "knows-gen", type: "tool"}, generated_at: "<ISO datetime>"}`

## Relation fields — EVERY relation MUST have ALL of these (EXACT enum values)

- `id`: `"rel:{subject-slug}-{predicate}-{object-slug}"` (kebab-case, MUST include a slug derived from the object so that two relations sharing the same subject and predicate but pointing to different objects get different IDs). Examples: `rel:method-uses-sam-3d-body`, `rel:method-uses-smpl-smplx`, `rel:accuracy-supports-main-claim`. NEVER emit `rel:{subject}-{predicate}` without the object component — the same subject often has multiple `uses`, `cites`, or `supported_by` relations, and the short form collides.
- `subject_ref`: `"stmt:..."` (what is being supported/challenged)
- `predicate`: ONLY one of: `supported_by`, `challenged_by`, `depends_on`, `limited_by`, `cites`, `uses`, `evaluates_on`, `implements`, `documents`, `same_as`, `supersedes`, `retracts`
- `object_ref`: `"ev:..."` or `"stmt:..."` (what provides the support/challenge)

## Artifact fields

- `id`: `"art:paper"`, `"art:descriptive-name"` etc.
- `artifact_type`: ONLY one of: `paper`, `repository`, `dataset`, `model`, `benchmark`, `software`, `website`, `other`
- `role`: ONLY one of: `subject`, `supporting`, `cited`
- `title`, `identifiers` (ONLY `doi`/`arxiv`/`isbn`/`url`/`custom` keys)
- `representations`: REQUIRED for `art:paper` (the subject) — MUST include:
  `[{id: "rep:paper-pdf", media_type: "application/pdf", locator: {type: "path", value: "<paper-stem>.pdf"}}]`
  This is critical — source_anchors reference `"rep:paper-pdf"`, so it MUST exist.

### Cited / supporting artifact identifiers (REQUIRED)

For **every** artifact with `role: cited` or `role: supporting` (benchmarks,
datasets, models, prior papers, repositories), you MUST supply at least one
discoverable identifier in `identifiers` so downstream consumers can resolve
the citation. Pick whichever the artifact is best known by:

| `artifact_type` | Preferred identifier | Example |
|---|---|---|
| `paper` (cited) | `arxiv` (preprint id) or `doi` | `arxiv: "2110.14168"` (GSM8K paper) |
| `benchmark` | `url` (canonical project page) or `arxiv` | `url: "https://huggingface.co/datasets/gsm8k"` |
| `dataset` | `url` or `doi` | `url: "https://commoncrawl.org/"` |
| `model` | `url` (HuggingFace / GitHub release) | `url: "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"` |
| `repository` | `url` (the repo URL) | `url: "https://github.com/openai/gym"` |
| `software` | `url` | `url: "https://pytorch.org/"` |
| `website` | `url` | (the URL itself) |

Use what you know from the paper (cited works often have arxiv ids in the
references section; benchmarks have well-known canonical pages). For
ambiguous cases supply `url` to the most authoritative landing page. The
lint script emits `WARN: <art-id>: no identifiers/locators/representations`
for any artifact missing all three — these warnings are non-blocking but
should be eliminated for publishable sidecars.

## Coverage values

- `statements`: ONLY one of: `exhaustive`, `main_claims_only`, `partial`, `key_claims_and_limitations`
- `evidence`: ONLY one of: `exhaustive`, `key_evidence_only`, `partial`

## STRICT SCHEMA RULES (violations cause lint failure)

- Do NOT add any fields not listed above — every object type has `additionalProperties: false`
- Do NOT invent extra fields like `description`, `tags`, `notes`, `category`, `importance` — they WILL fail
- Do NOT add YAML comments (`# ...`)
- Every observation MUST have `metric` field
- Every provenance MUST have `origin`, `actor` (with `name` and `type`), and `generated_at`
- ID prefixes are mandatory: `art:` (artifacts), `stmt:` (statements), `ev:` (evidence), `rel:` (relations), `rep:` (representations)
- IDs MUST be descriptive kebab-case: `stmt:privacy-budget-tradeoff`, NOT `stmt:c1`
- Empty arrays: emit `actions: []`, never omit the key

## Content Rules

- Generate 7-15 statements covering major claims, findings, assumptions, and limitations
- Generate evidence items for all tables, figures, and key experimental results
- Create relations linking every statement to its supporting evidence (aim for 1.5+ relations per statement)
- Use concrete text from the paper, not generic placeholders
- `observation.value` MUST be a number (float/int), NOT a string. Use `qualitative_value` for non-numeric

## SELF-CHECK before output

Verify your YAML has ALL of these root keys: `$schema`, `knows_version`, `record_id`, `profile`, `subject_ref`, `title`, `summary`, `coverage`, `license`, `artifacts`, `statements`, `evidence`, `relations`, `actions`, `provenance`, `version`, `freshness`.

Verify `art:paper` has a `representations` array with `rep:paper-pdf`.

Verify every statement has: `id`, `statement_type`, `modality`, `text`, `about_ref`, `status`, `source_anchors`, `confidence`, `provenance`.

Verify every evidence has: `id`, `evidence_type`, `summary`, `source_anchors`, `observations`, `provenance`.

Verify every relation has: `id`, `subject_ref`, `predicate`, `object_ref`.

Verify ID uniqueness: scan every `rel:*` id and confirm no two relation objects share the same id. The most common generation bug is naming multiple relations `rel:{subject}-{predicate}` when the same subject points to multiple objects via the same predicate (for example, a single method that `uses` several tools); every such relation MUST include an object-derived slug so the ids remain distinct. The same check applies to `art:*`, `stmt:*`, `ev:*`, `act:*`.

---

## Usage

### In Claude Code skill mode (PDF or LaTeX input)

1. Read this prompt
2. Read `references/yaml-template.yaml` for structural reference
3. Read the paper content (PDF via multimodal, or LaTeX text)
4. Generate YAML following ALL rules above
5. Run `python3 scripts/lint.py output.knows.yaml`
6. Run `python3 scripts/verify_metadata.py output.knows.yaml`

### In `knows gen --model` CLI mode

The `gen.py` script embeds a version of this prompt in `_LLM_GEN_PROMPT`. The paper content is injected at the `{content}` placeholder, truncated to 15K chars.

### Template variables

Replace before use:
- `<paper-stem>` — filename stem of the paper (e.g., `resnet`, `attention`)
- `<ISO datetime>` — current UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format
