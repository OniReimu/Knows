---
name: knows-sidecar-author
description: "Generate a KnowsRecord sidecar from a PDF (multimodal LLM read), a LaTeX project (full pipeline), or a pre-extracted text blob. Triggers: 'create sidecar from this PDF', 'make a sidecar for paper.pdf', 'generate sidecar', 'extract claims from my paper', 'knows gen', 'create sidecar from this LaTeX'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: contribute
required_inputs:
  # Exactly one of the four must be supplied (4-way OR per §1.5 contribute rows).
  # Supplying any two is invalid_slot_type per §5.
  - pdf_path          # most common real-world input — multimodal LLM reads PDF directly (Path F)
  - latex_dir         # full deterministic pipeline via gen.py (Paths A / B)
  - text_blob         # pre-extracted text — wrapped in synthetic .tex for gen.py (Path E)
  - brainstorm_summary  # NEW v0.11+: from-idea path (Path C) via the `pitch-grill` stance. Fenced YAML block (schema: brainstorm-v1) carrying headline_claim / closest_related_work / falsifying_experiment / load_bearing_assumption / out_of_scope_disclaimer / target_venue. Switches the skill to CONSUME MODE — mechanical translation of the structured pitch into a `paper@1` from-idea sidecar with `venue_type: in_preparation`. See ../../stances/pitch-grill/SKILL.md for the canonical brainstorm_summary format.
requested_artifacts:
  - knows_yaml        # primary route — produces a sidecar YAML file
  - lint_report       # secondary route — runs lint without producing the full sidecar (validation-only branch)

# Profile contract — G7 (no hub consumption)
accepts_profiles: []                 # this skill does not retrieve from knows.academy; takes local input only

# Quality policy — G2'
quality_policy:
  require_lint_passed: false         # the sidecar being authored IS the output, not a prerequisite — lint runs as part of the post-gen pipeline, not as an input gate
  allowed_coverage: [exhaustive, main_claims_only, key_claims_and_limitations, partial]
  min_statements: 0                  # author is producing the record; do not pre-filter on statement count

# Fetch-planner — G3 (no API calls during generation)
requires_full_record: false

# Sidecar profile this skill writes — REQUIRED because knows_yaml is a sidecar artifact
emits_profile: paper@1
---

# sidecar-author — Generate a KnowsRecord sidecar

This sub-skill wraps the foundational generation pipeline (`scripts/gen.py` + `scripts/lint.py` + `scripts/sanitize.py` + `scripts/verify_metadata.py`) and the canonical generation prompt (`references/gen-prompt.md`) under the orchestrator's dispatch contract.

## Quick Start (agent-mediated mode, v1.0)

Per `../../SKILL.md` "v1.0 Agent-Mediated Mode" — you (the agent) execute. Two most common cases:

### Case 1: User has a PDF (Path F — most common in real world)

```bash
# 1. Dispatch tuple: (contribute, {pdf_path: "/papers/x.pdf"}, knows_yaml)
PDF_PATH="/papers/x.pdf"

# 2. Read references/gen-prompt.md — copy the system message + user template VERBATIM into your LLM call
# 3. Open the PDF using your multimodal capability:
#    - Anthropic: messages.create(model="claude-opus-4-7", system=<gen-prompt system>, messages=[{"role":"user","content":[{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":<base64>}},{"type":"text","text":<gen-prompt user>}]}])
#    - OpenAI: responses.create with file input
#    - Gemini: generate_content with Part.from_data(mime_type="application/pdf", data=...)
# 4. LLM returns YAML; sanitize and lint:
RAW="/tmp/raw.yaml"; OUT="/tmp/sidecar.knows.yaml"
# Save LLM response to $RAW first, then:
python3 ../../scripts/sanitize.py "$RAW" -o "$OUT"
python3 ../../scripts/lint.py "$OUT"                    # MUST be 0 errors; if not, ask LLM to fix and re-lint (max 3 attempts)
python3 ../../scripts/verify_metadata.py "$OUT"         # DOI/title/venue check (warnings ok, not abstain)
# 5. Set provenance.method = "extraction" in the YAML (LLM should already have set it; verify)
# 6. Manifest: {skill: sidecar-author, intent_class: contribute, dispatch_tuple: "(contribute,{pdf_path},knows_yaml)", model, metadata_warnings, abstained?}
```

### Case 2: User has a LaTeX project (Path A — zero API key needed)

```bash
# 1. Dispatch tuple: (contribute, {latex_dir: "paper/"}, knows_yaml)
python3 ../../scripts/gen.py paper/main.tex -o /tmp/sidecar.knows.yaml         # scaffold (Path A)
# OR with LLM (Path B, requires ANTHROPIC_API_KEY):
# python3 ../../scripts/gen.py paper/main.tex --model opus -o /tmp/sidecar.knows.yaml
python3 ../../scripts/lint.py /tmp/sidecar.knows.yaml
python3 ../../scripts/verify_metadata.py /tmp/sidecar.knows.yaml
```

**For Path E (text_blob)**: write the blob to `$(mktemp -t input_XXXXX.tex)` first, then proceed as Path A. **For Path C (from-idea)**: manual curation following `../../references/yaml-template.yaml`; no `gen.py` call.

**Upload (`POST /sidecars`) is DEFERRED in v1.0** — refuse with `upload_disabled_endpoint_unverified` if user asks to publish to knows.academy.

> **No new code.** This sub-skill is a thin router on top of the existing toolkit. The operational depth (generation paths, anti-fabrication rules, lint validation, common mistakes) lives in the canonical references — see "Canonical references" below.

## Canonical references (read these, in order)

1. **`../../references/dispatch-and-profile.md`** §1.5 + §3.4 — the routing contract this skill implements
2. **`../../references/gen-prompt.md`** — single source of truth for schema rules, field enumerations, and self-check checklist when generating YAML (whether from LaTeX, raw text, or PDF)
3. **`../../references/yaml-template.yaml`** — complete YAML template; MUST read before generating
4. **`../../references/knows-record-0.9.json`** — JSON Schema v0.9 (used by `lint.py`)
5. **`../../SKILL.md`** "Mode: generate" section — operational content for the 4 generation paths (LaTeX scaffold / LLM gen from LaTeX / from-idea / from-PDF agent-mediated)

## Routes

This sub-skill owns 2 rows in `dispatch-and-profile.md` §1.5:

| `requested_artifact` | What user gets | Implementation |
|---|---|---|
| `knows_yaml` | `paper.knows.yaml` file (lint-pass + verify-pass) | LaTeX/text input → `gen.py` → `sanitize.py` → `lint.py` → `verify_metadata.py`. PDF input (Path F) → multimodal LLM read + `gen-prompt.md` → `sanitize.py` → `lint.py` → `verify_metadata.py` |
| `lint_report` | Lint pass/fail summary (no sidecar persisted) | Same as `knows_yaml` route to a tmp path → `lint.py` → return only the summary, discard the YAML |

> **Standalone lint of a pre-existing user-supplied YAML** is NOT this route — that would require a `yaml_path` slot not declared in §1.3. For ad-hoc validation of a YAML you already have on disk, call `python3 ../../scripts/lint.py <path>` directly (Foundational Utility per parent SKILL.md), bypassing the orchestrator. A future v1.x contract addition could add `(validate, {yaml_path}, lint_report)` as its own intent_class+slot.

The orchestrator routes based on `requested_artifact`. The sub-skill body branches on the same field — there is no internal heuristic.

## Workflow (knows_yaml route)

Per `../../SKILL.md` "Mode: generate" section, choose one of 4 paths based on input:

- **Path A** (deterministic LaTeX scaffold): `latex_dir` slot → `python3 ../../scripts/gen.py paper/main.tex -o paper.knows.yaml`
- **Path B** (LLM from LaTeX, requires `ANTHROPIC_API_KEY`): `latex_dir` slot → `python3 ../../scripts/gen.py paper/main.tex --model opus -o paper.knows.yaml`
- **Path C** (from-idea, no paper yet): manual generation following `../../references/yaml-template.yaml`; set `provenance.method: manual_curation`, `venue_type: in_preparation`. (No specific slot — this is a curation flow the agent runs without `gen.py`.)
- **Path E** (text_blob input): `text_blob` slot → write the blob to `mktemp -t knows_input_XXXXX.tex`, then proceed as Path A (scaffold) or Path B (LLM). The synthetic .tex wrapper allows `gen.py`'s LaTeX-input pipeline to run on pre-extracted text. Discard the tmp .tex after generation.
- **Path F** (PDF input — first-class, primary real-world route): `pdf_path` slot → multimodal LLM (Claude / GPT-4o+ / Gemini) reads the PDF natively + applies `../../references/gen-prompt.md` verbatim to produce YAML. Most users only have PDFs (papers downloaded from arXiv / publisher sites), so this is the primary contribute route. Implementation:
  1. Sub-skill body opens the PDF via the agent's multimodal capability (the exact API call differs per platform — Anthropic `messages.create` with `document` content block, OpenAI `responses.create` with file input, Gemini `generate_content` with `Part.from_data`)
  2. System message + user template come from `../../references/gen-prompt.md` — load verbatim, do not rewrite
  3. LLM produces a complete KnowsRecord YAML in one pass
  4. Sub-skill body parses the response, runs the same post-gen pipeline as Path A/B (sanitize → lint → verify_metadata)
  5. `provenance.method: extraction` (extracted from PDF, not hand-curated)

  Path F does NOT use `gen.py` (which requires LaTeX input). The dogfood example in the Knows v0.9 paper Appendix D was generated this way — Opus subagent reading the paper PDF + applying gen-prompt.md.

After generation, **always run the post-gen checklist**:

```bash
python3 ../../scripts/sanitize.py raw_output.yaml -o paper.knows.yaml   # only if YAML fails to parse
python3 ../../scripts/lint.py paper.knows.yaml                          # MUST be 0 errors
python3 ../../scripts/verify_metadata.py paper.knows.yaml               # DOI/title/venue anti-fabrication
python3 ../../scripts/verify_metadata.py --auto-enrich paper.knows.yaml # if DOI missing, search CrossRef
```

The full anti-fabrication rules (DOI / venue / year / authors / preprints / from-idea sidecars) and common-mistake table are in `../../SKILL.md` "Anti-fabrication rules" section. **Do not duplicate that content here** — read it from the monolith.

## Workflow (lint_report route)

The lint_report route accepts the **same input slots** as the `knows_yaml` route (`latex_dir` OR `text_blob` OR `pdf_path` — exactly one). Implementation branches on which slot was supplied:

```bash
TMP=$(mktemp -t knows_lint_only_XXXXX.yaml)

# Branch on slot type:
if   [ -n "${latex_dir:-}" ]; then  # Path A/B
  python3 ../../scripts/gen.py "$latex_dir/main.tex" -o "$TMP"
elif [ -n "${text_blob:-}" ]; then  # Path E
  TEX_TMP=$(mktemp -t knows_input_XXXXX.tex)
  printf '%s' "$text_blob" > "$TEX_TMP"
  python3 ../../scripts/gen.py "$TEX_TMP" -o "$TMP"
  rm "$TEX_TMP"
elif [ -n "${pdf_path:-}" ]; then   # Path F — multimodal LLM read PDF + apply gen-prompt.md
  # Agent reads $pdf_path multimodally + applies references/gen-prompt.md verbatim,
  # writes resulting YAML to "$TMP". (No bash one-liner — this is a multi-step LLM call.)
  : run-multimodal-pdf-to-yaml "$pdf_path" > "$TMP"
fi

python3 ../../scripts/lint.py "$TMP"   # only the lint summary is the artifact
rm "$TMP"
```

This route is for "I want to know if my LaTeX project / extracted text / downloaded PDF would produce a lint-passing sidecar without committing to the artifact yet" — useful in CI gates or pre-publish checks. The user does NOT supply a YAML; they supply the same input as `knows_yaml` route, but receive only the lint report.

For lint of an existing YAML on disk, see the parent SKILL.md "Mode: validate" — that is a foundational utility, not orchestrator-routed.

## Upload (DEFERRED — `POST /sidecars` UNVERIFIED)

The orchestrator does NOT enable `POST /sidecars` in v1.0. If the user asks to "publish to knows.academy", the orchestrator MUST refuse with `upload_disabled_endpoint_unverified` per `dispatch-and-profile.md` §5. Local sidecar production is fully supported; remote upload is a v1.x follow-on once the endpoint is probed.

## Abstain conditions (from §5)

This skill abstains (returns structured refusal, never silently proceeds) when:

| Condition | `abstained_reason` |
|---|---|
| Any two of `latex_dir` / `text_blob` / `pdf_path` supplied simultaneously (3-way OR violation) | `invalid_slot_type.<second-slot-name>` |
| None of `latex_dir` / `text_blob` / `pdf_path` supplied | `missing_required_input.pdf_path` (canonical primary; alternative slots noted in error detail) |
| `latex_dir` supplied but path does not exist or contains no `.tex` file | `invalid_slot_type.latex_dir` |
| `text_blob` supplied but empty / non-string | `invalid_slot_type.text_blob` |
| `pdf_path` supplied but file does not exist, is not a PDF, OR exceeds agent's PDF size limit | `invalid_slot_type.pdf_path` |
| `pdf_path` supplied but agent has no multimodal capability (text-only model) | `skill_runtime_exception.MultimodalCapabilityRequired` |
| `gen.py` raises uncaught exception (e.g. malformed LaTeX) | `skill_runtime_exception.<class>` |
| Lint fails after 3 self-correction attempts (per parent SKILL.md post-gen checklist step 5) | `skill_runtime_exception.LintFailureExceeded` |
| User requests upload to knows.academy (`POST /sidecars`) | `upload_disabled_endpoint_unverified` |

**Not abstain conditions** (return YAML + log warning, do not fail):

- `verify_metadata.py` cannot resolve DOI / `--auto-enrich` finds nothing → DOI is best-effort optional per parent SKILL.md anti-fabrication rules. Omit `identifiers.doi` from the YAML, log to manifest as `metadata_warnings: [doi_unresolved]`. Preprints, in-prep records, and freshly-published papers routinely lack resolvable DOIs.
- `verify_metadata.py` flags venue / title mismatch → return YAML, log as `metadata_warnings: [venue_mismatch | title_mismatch]`. User reviews and corrects.

## Manifest emission

Per G6, every run emits `manifest.json` in the output directory. For this skill, populated fields are:

- `skill: knows-sidecar-author`
- `intent_class: contribute`
- `dispatch_tuple: (contribute, {pdf_path|latex_dir|text_blob}, {knows_yaml|lint_report})`
- `started_at` / `ended_at`
- `model` (when Path B used; absent for Path A scaffold)
- `applied_profile_filters: []` (no hub consumption)
- `applied_quality_policy` (this skill's frontmatter)
- `excluded_*` and `quality_exclusions` arrays are empty (no records were filtered — generation is local)
- `abstained` / `abstained_reason` (set when refusing, e.g. on UNVERIFIED upload request)

`returned_rids: []` (no API hits). `fetch_mode_per_rid: {}` (no fetches).

## Smoke test

The Knows repo doesn't ship a .tex fixture, so the smoke test uses the Path E text_blob route — synthesizes a minimal .tex on the fly. The smoke test asserts **scaffold generation only** (not lint pass): `gen.py` intentionally emits TODO stubs that require manual completion before lint will pass — that is the documented contract (see parent `SKILL.md` "Mode: generate" — every Path A scaffold needs a manual-fill pass before lint). A clean-room scaffold will fail lint with `'authors' is a required property` and similar required-field gaps; that is the expected baseline, not a regression.

```bash
set -euo pipefail
TMP=$(mktemp -t knows_smoke_XXXXX.tex)
OUT=/tmp/smoke.knows.yaml
trap 'rm -f "$TMP" "$OUT"' EXIT

cat > "$TMP" << 'EOF'
\documentclass{article}
\title{Smoke Test Paper}
\author{Test Author \and Second Author}
\begin{document}
\maketitle
\begin{abstract}
This is a smoke-test paper to verify gen.py's scaffold path runs end-to-end.
\end{abstract}
\section{Introduction}
We claim that the orchestrator works. We support this with the scaffold output.
\section{Method}
Run gen.py on this file.
\section{Conclusion}
If gen.py emits a structurally valid YAML scaffold, the smoke test is green.
\end{document}
EOF

# Step 1: gen.py must exit 0 and produce a YAML file (set -e propagates failure)
python3 ../../scripts/gen.py "$TMP" -o "$OUT"
test -s "$OUT"

# Step 2: YAML must be parseable + carry the expected scaffold markers
python3 -c "
import sys, yaml
rec = yaml.safe_load(open('$OUT'))
assert rec.get('profile') == 'paper@1', 'profile mismatch'
assert rec.get('title') == 'Smoke Test Paper', 'title mismatch'
assert len(rec.get('statements', [])) >= 1, 'no statement stubs emitted'
print('OK: scaffold generated, %d statements, %d artifacts' % (len(rec['statements']), len(rec['artifacts'])))
"

# Expect: prints "OK: scaffold generated, ..."; exit 0.
# Lint will FAIL on this raw scaffold (missing authors etc.) — that is by design;
# Path A scaffolds require a manual-fill pass before lint. To exercise the full
# lint-clean pipeline, run gen.py against a real paper and complete TODOs first.
```

If gen.py crashes or emits unparseable YAML, the regression is in the underlying script, not this sub-skill wrapper. For lint-passing fixtures, see the 21 published sidecars under `../../../examples/` (PDF + sidecar pairs across 14 disciplines) — those exercise consume-mode (sidecar-reader), not contribute-mode, but they are the canonical "what a finished, lint-clean sidecar looks like" reference.

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A, from-idea path)

When invoked downstream of the `pitch-grill` stance (Type B), sidecar-author receives a `brainstorm_summary` input INSTEAD OF pdf_path/latex_dir/text_blob. This is the canonical Path C (from-idea) entry point in v0.11. The skill switches to CONSUME MODE — mechanical translation of the structured pitch fields into a `paper@1` from-idea sidecar.

### Why CONSUME MODE matters for from-idea

Path C in v0.10 was natural-language-ingested: the user describes their idea, the agent constructs the YAML. This is fine for casual use but produces uneven quality — the agent fills in placeholders for closest_related_work, hypothesizes the falsifying experiment, etc. The `pitch-grill` stance (v0.11) collects those fields explicitly through 3-axis interrogation (originality / feasibility / scope), so the brainstorm_summary carries user-confirmed answers. Consume mode preserves this — the emitter does not re-hypothesize.

### CONSUME MODE flow

```python
if pdf_path or latex_dir or text_blob:
    # PAPER-EXTRACTION PATH (A / B / E / F) — current v0.10 behavior
    ...
elif brainstorm_summary is not None:
    # FROM-IDEA PATH (C) via pitch-grill chain — fail-closed verification + mechanical translation
    summary = parse_brainstorm_summary(brainstorm_summary)
    if summary["status"] == "abandon":
        manifest.abstained = True
        manifest.abstained_reason = "brainstorm_abandoned"
        raise SystemExit
    if summary["status"] == "needs_rework":
        return {"action": "return_to_stance", "rework_needed": summary["rework_needed"]}
    assert summary["status"] == "ready"
    assert summary["emit_chain"][-1] == "sidecar-author"

    # Verify required fields are present and confirmed
    pitch = summary["pitch"]
    required_fields = ["headline_claim", "load_bearing_assumption", "falsifying_experiment",
                       "out_of_scope_disclaimer"]
    rework_needed = []
    for f in required_fields:
        conf = next((c for c in summary["human_confirmations"] if c.get("field") == f), None)
        if conf is None or conf.get("decision") == "drop":
            rework_needed.append({"field": f, "reason": "user did not confirm"})
        if not pitch.get(f):
            rework_needed.append({"field": f, "reason": "missing or empty"})
    if not pitch.get("closest_related_work"):
        rework_needed.append({"field": "closest_related_work",
                              "reason": "originality unverified — empty list"})
    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed}

    yaml_record = translate_pitch_to_paper_yaml(summary)
    # CONSUME MODE outputs MUST set $schema to 0.10 — workflow_chain is a first-class
    # field on Provenance only in 0.10. Emitting from-idea sidecars with $schema=0.9
    # would force workflow_chain into provenance.x_extensions, weakening the contract.
    yaml_record["$schema"] = "https://knows.dev/schema/record-0.10.json"
    yaml_record["knows_version"] = "0.10.0"
    yaml_record["provenance"]["workflow_chain"] = summary["emit_chain"]   # ["pitch-grill", "sidecar-author"]
    yaml_record["provenance"]["method"] = "manual_curation"               # from-idea convention
    yaml_record["venue_type"] = pitch.get("target_venue_type", "in_preparation")
else:
    # Neither extraction input nor brainstorm_summary — abstain
    raise abstain("missing_required_input.<one of pdf_path|latex_dir|text_blob|brainstorm_summary>")
```

### Field mapping (brainstorm_summary → paper@1 from-idea YAML)

| brainstorm_summary field | paper@1 YAML location |
|---|---|
| `pitch.headline_claim` | a `claim`-typed `stmt:headline-*` with `modality: theoretical` (idea not yet measured) |
| `pitch.load_bearing_assumption` | an `assumption`-typed `stmt:load-bearing-*` |
| `pitch.falsifying_experiment` | a `method`-typed `stmt:falsifying-experiment` describing the experiment |
| `pitch.out_of_scope_disclaimer` | a `limitation`-typed `stmt:scope-*` (pre-emptive disclaimer) |
| `pitch.closest_related_work[*]` | `artifacts[*]` with `role: cited`, identifiers populated when arxiv/doi inferable |
| `pitch.target_venue` | top-level `venue` (when set; omit if "TBD") |
| `pitch.target_venue_type` | top-level `venue_type` (default `in_preparation`) |
| `emit_chain` | `provenance.workflow_chain` |
| (always) | `provenance.method: manual_curation`, `coverage: {statements: main_claims_only, evidence: partial}` |

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` field is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| brainstorm_summary `status` is `needs_rework` (pass control back to stance) | NOT abstain — return `action: return_to_stance` instead |
| `pitch.closest_related_work` is empty AND user did not explicitly confirm "I checked, nothing is close" | `action: return_to_stance` (originality unverified) |
| Any required pitch field missing or unconfirmed | `action: return_to_stance` |
| brainstorm_summary `emit_chain` does NOT end with `sidecar-author` | `invalid_slot_type.brainstorm_summary` |

### `provenance.workflow_chain` (REQUIRED in consume mode)

The output sidecar's `provenance.workflow_chain` MUST be set to the `emit_chain` from brainstorm_summary (typically `["pitch-grill", "sidecar-author"]`). Solo-mode records (PDF/LaTeX/text-blob input) do NOT set workflow_chain.

### When NOT to use consume mode

If the user has an actual paper PDF or LaTeX project, the paper-extraction paths (A/B/E/F) are correct — they extract real claims grounded in real text. Consume mode is for when the paper does not yet exist (idea stage). Routing the wrong way produces a from-idea sidecar where the headline claim is just the user's brainstorm conjecture instead of a measured-and-cited paper claim.

## Out of scope

- Generic Markdown/HTML intake — DEFERRED. Currently `text_blob` accepts pre-extracted plain text but there's no first-class `md_path` or `html_path` slot. Workaround: pre-extract to text and use `text_blob`.
- Remote PDF generation via hub `POST /generate/pdf` — DEFERRED, endpoint UNVERIFIED. Local PDF intake (Path F) is supported; only remote-side PDF→sidecar conversion is gated.
- Remote upload (`POST /sidecars`) — UNVERIFIED endpoint.
- Remote PDF generation (`POST /generate/pdf`) — UNVERIFIED endpoint.
- Multi-paper batch generation in a single dispatch call — multi-artifact composition is OUT OF SCOPE per `dispatch-and-profile.md` §7.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/gen-prompt.md`](../../references/gen-prompt.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
