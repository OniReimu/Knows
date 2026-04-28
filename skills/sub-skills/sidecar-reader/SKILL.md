---
name: knows-sidecar-reader
description: "Answer a question about a paper using its KnowsRecord sidecar — grounded in the sidecar's statements and evidence, with explicit confidence/abstain when the answer isn't there. Triggers: 'what does paper X claim about Y', 'tell me about this paper', 'extract the methodology from this sidecar', 'what accuracy did they report', 'answer this question using sidecar', 'is X discussed in this paper'. Use this for any sidecar-grounded Q&A — do NOT use review-sidecar (that one generates a peer review, this one reads a paper)."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: extract
required_inputs:
  - rid                 # record_id of the sidecar to read — PLAIN string, not URL-encoded. The G5 transport layer URL-encodes when calling GET /api/proxy/sidecars/<rid>. Encoding here would double-encode and 404.
  - q                   # the question to answer
optional_inputs:
  - question_id         # echoed back as `item_id` in the answer_json. If omitted, sub-skill derives a deterministic id via SHA-1(q)[:8].
requested_artifacts:
  - answer_json         # single JSON object per consume-prompt.md v1.1 schema (status / answer / confidence / evidence / reason)

# Profile contract — G7 (single-input, paper@1 only)
accepts_profiles: [paper@1]

# Quality policy — G2'
quality_policy:
  require_lint_passed: true            # do not consume from broken sidecars; their evidence anchors may be invalid
  allowed_coverage:                    # exclude `partial` — answers from partial coverage have unbounded recall failure
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5                    # too few statements → high abstain rate; not worth the API call

# Fetch-planner — G3 (consume-prompt.md v1.1 needs full record for evidence anchoring)
requires_full_record: true

# emits_profile omitted — answer_json is not a sidecar artifact (read-only skill)
---

# sidecar-reader — Answer a question from a KnowsRecord sidecar

This sub-skill operationalizes the canonical downstream consume contract — the same one used by the Knows technical report E1-E10 experiments. It is the **highest-spec-leverage** sub-skill in v1.0 because the LLM call, JSON schema, and confidence-gated PDF fallback are all defined verbatim in `references/consume-prompt.md` v1.1.

## Quick Start (agent-mediated mode, v1.0)

Per `../../SKILL.md` "v1.0 Agent-Mediated Mode" — you (the agent) execute. End-to-end for "what dataset did paper X use, given rid Y":

```bash
# 1. Dispatch tuple: (extract, {rid: "Y", q: "what dataset?"}, answer_json); auto-derive question_id = sha1(q)[:8]
RID="Y"; Q="what dataset?"
QID=$(python3 -c "import hashlib;print(hashlib.sha1(b'$Q').hexdigest()[:8])")
ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")

# 2. G5 transport: fetch full sidecar (requires_full_record: true)
curl -s "https://knows.academy/api/proxy/sidecars/$ENC" -o /tmp/sidecar.json

# 3. G7: confirm record.profile == "paper@1" (abstain otherwise with empty_working_set_after_profile_filter)
# 4. G2': confirm lint_passed + coverage + stmt_count (abstain otherwise)
# 5. G1: wrap sidecar JSON in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>
# 6. LLM call using consume-prompt.md v1.1:
#    - Read ../../references/consume-prompt.md, find "v1.1" section
#    - System message + user template are literally in that file (look for "system:" and "user:" headings)
#    - User template includes {sidecar_json}, {q}, {question_id}
#    - Call your LLM (Claude/GPT/Gemini) with these as messages
#    - LLM returns JSON matching the v1.1 output schema
# 7. Parse JSON, validate status ∈ {answer, partial, abstain, supported, ambiguous, not_found}
# 8. If status ∈ {answer,partial,supported} AND confidence >= 0.7: return as authoritative
#    Else: return as-is, do NOT silently upgrade (PDF fallback is DEFERRED v1.x)
# 9. Manifest: {skill, intent_class, dispatch_tuple, returned_rids: [RID], fetch_mode_per_rid: {RID:"full"}, model, abstained?}
```

**Key gotcha**: `consume-prompt.md` is the single source of truth for the prompt. Don't paraphrase or "improve" the system message — copy verbatim, fill in the templated values only.

> **No new prompt design.** The system message, user message, JSON schema, and Algorithm 1 confidence threshold are all already in `consume-prompt.md`. This sub-skill is a wrapper that wires `GET /sidecars/<rid>` (or local file) → consume-prompt.md → JSON parse → return.

## Canonical references (read these, in order)

1. **`../../references/dispatch-and-profile.md`** §1.5 + §3.4 — the routing contract this skill implements
2. **`../../references/consume-prompt.md`** v1.1 — **load-bearing**. The system message, user message template, JSON output schema, and confidence-gated PDF fallback rules are all here. **Use verbatim.**
3. **`../../references/api-schema.md`** — for `GET /sidecars/<rid>` shape and URL-encoding rules
4. **`../../references/knows-record-0.9.json`** — full sidecar schema (referenced by the LLM's reasoning when interpreting evidence anchors)

## Routes

This sub-skill owns 1 row in `dispatch-and-profile.md` §1.5:

| `requested_artifact` | What user gets |
|---|---|
| `answer_json` | Single JSON object matching `consume-prompt.md` v1.1 schema: `{item_id, status, answer, confidence, evidence[], reason}` where `status ∈ {answer, partial, abstain, supported, ambiguous, not_found}` and `item_id` echoes the input `question_id` |

## Workflow

```
1. Validate inputs (orchestrator already did §1.3 runtime validation; sub-skill body trusts the slot map)
   - rid: string matching record_id pattern, URL-encoded for transport
   - q: non-empty string

2. Fetch full sidecar (G3 requires_full_record: true)
   - `rid` is a plain record_id (e.g. `knows:vaswani/attention/1.0.0`). Orchestrator's G5 transport layer URL-encodes it once and calls `GET /api/proxy/sidecars/<encoded>`. Sub-skill body MUST NOT pre-encode — the contract slot value is the unencoded form.
   - Profile filter (G7) already applied by orchestrator — sub-skill body trusts that record.profile == "paper@1"
   - Local-file-path input is NOT supported in v1 (would require a new `local_path` slot in §1.3)
   - Resolve `question_id`: if provided in input, use as-is; if absent, derive `question_id = sha1(q).hexdigest()[:8]` so each call has a stable id even without explicit user input

3. Wrap sidecar content in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR> per G1 (orchestrator may do this transparently — verify via manifest)

4. Construct LLM call using consume-prompt.md v1.1 verbatim:
   - System message: from consume-prompt.md §"v1.1 system"
   - User message: from consume-prompt.md §"v1.1 user template", filled with sidecar JSON + question q
   - Output: structured JSON per consume-prompt.md §"v1.1 output schema"

5. Parse LLM response as JSON. Validate against canonical schema (consume-prompt.md v1.1):
   - status ∈ {answer, partial, abstain, supported, ambiguous, not_found}
   - confidence ∈ [0.0, 1.0]
   - evidence[] MUST be non-empty when status ∈ {answer, partial, supported}; MAY be empty when status ∈ {abstain, not_found}; semantics for `ambiguous` follow consume-prompt.md
   - evidence[].page = 0 for sidecar context (page-tagged when PDF fallback is configured)
   - reason ≤ 25 words

6. Confidence-gated PDF fallback (Algorithm 1 from technical report):
   - "Sufficient" status set: status ∈ {answer, partial, supported}
   - If status ∈ sufficient AND confidence ≥ τ (default τ = 0.7): return as-is
   - If status == ambiguous OR status ∈ sufficient with confidence < τ: PDF fallback IF configured (see "PDF fallback strict mode" below)
   - If status ∈ {abstain, not_found}: do not trigger fallback — these are deliberate non-answers, not low-confidence answers
   - PDF fallback path: re-run consume-prompt.md v1.1 with the PDF text (page-tagged) as context, replace answer_json with PDF result
   - If no PDF available: return the original answer_json with status + confidence preserved (do NOT silently upgrade)

7. Emit manifest (G6) and return answer_json
```

## PDF fallback — out of scope

PDF fallback is documented in `consume-prompt.md` Algorithm 1 but is **NOT routed through this sub-skill** in v1.0. The dispatch contract (`dispatch-and-profile.md` §1.3) does not declare a `pdf_path` slot for `extract`, so the orchestrator cannot accept a PDF as part of the extract tuple.

This skill operates on sidecar context only:
- If status ∈ {answer, partial, supported} with confidence ≥ τ → return as authoritative
- If status ∈ {answer, partial, supported} with confidence < τ OR status == ambiguous → return as-is with the low-confidence/ambiguous status preserved; **do not silently upgrade** confidence
- If status ∈ {abstain, not_found} → return as-is (deliberate non-answer)

The user can chain a separate manual PDF read on the returned low-confidence answer if needed.

## Manifest emission

Per G6, every run emits manifest with these fields populated:

- `skill: knows-sidecar-reader`
- `intent_class: extract`
- `dispatch_tuple: (extract, {rid, q}, answer_json)`
- `returned_rids: [rid]` (the one record fetched)
- `applied_profile_filters: [paper@1]`
- `applied_quality_policy` (this skill's frontmatter)
- `fetch_mode_per_rid: {<rid>: "full"}` (G3 requires_full_record: true)
- `model` (LLM used for the consume-prompt.md call)
- `token_cost_estimate` (best-effort total)
- `abstained` / `abstained_reason` (when applicable — see Abstain conditions below)

## Abstain conditions (from §5)

This skill abstains (returns structured refusal, never silently proceeds) when:

| Condition | `abstained_reason` |
|---|---|
| `rid` slot missing or wrong type | `missing_required_input.rid` / `invalid_slot_type.rid` |
| `q` slot missing or empty | `missing_required_input.q` / `invalid_slot_type.q` |
| Hub returns 404 for `rid` | `rid_not_found.<rid>` |
| Record's `profile` filtered out by G7 (e.g. user supplied `review@1` rid) | `empty_working_set_after_profile_filter` |
| Record fails `quality_policy` (lint not passed / coverage not allowed / too few statements) | `empty_working_set_after_quality_filter` |
| Hub API malformed JSON | `upstream_response_malformed` |
| LLM call fails or returns invalid JSON | `skill_runtime_exception.<class>` |

## Smoke test

```bash
# Use a real published sidecar from knows.academy
RID="knows:vaswani/attention/1.0.0"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")
curl -s "https://knows.academy/api/proxy/sidecars/$ENC" -o /tmp/smoke_sidecar.json

# Or use the CLI wrapper:
python3 scripts/orchestrator.py sidecar-reader "knows:foo/bar/1.0.0" "what is the main result"
```

## Implementation

CLI wrapper available: `python3 scripts/orchestrator.py sidecar-reader <rid_or_local_path> "<question>"`. The wrapper fetches the sidecar (or reads a local `.knows.yaml` file with `--local`), applies `consume-prompt.md` v1.1 verbatim, and returns the JSON answer payload. Agent-mediated mode (LLM agent reads this SKILL.md and runs the steps directly) is also supported.

## Out of scope

- Multi-question batches in one call → single artifact per request (§7).
- Cross-sidecar retrieval ("answer this from any of N sidecars") → that is `synthesize_prose` or `synthesize_table`, not `extract`.
- Generating new evidence the sidecar doesn't have → consume-prompt.md is grounded retrieval; if evidence absent, return `status: not_found`.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/consume-prompt.md`](../../references/consume-prompt.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
