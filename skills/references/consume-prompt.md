---
name: consume-prompt
version: 1.1
purpose: Canonical LLM-driven Knows consumption prompt. Single source of truth for agent-consumption experiments.
---

# Canonical LLM Consumption Prompt

This document is the authoritative specification of how an LLM agent reads a Knows sidecar (or a PDF baseline) to answer a question. All Knows consumption experiments — E1 and successors — MUST derive their prompts from this document. Ad-hoc prompts embedded in `eval/` scripts are deprecated.

The prompt has two variants: **base** (free-form output, used in E1--E9) and **matched-output** (JSON schema with page-quoted evidence, used in E10 and all post-v0.9 reruns).

---

## Concepts

- **Context**: either the sidecar YAML text, or page-tagged PDF text. The consumer receives one or the other, never both (fallback is a separate, sequential consultation).
- **Condition**: `knows` (sidecar only), `pdf` (PDF only), or `knows+fallback` (sidecar first, PDF consulted when Algorithm 1 confidence fallback triggers).
- **Output form**: free-form prose (base) or JSON with page-quoted evidence (matched-output).

Both the sidecar and the PDF conditions MUST be prompted with the same system message and the same user skeleton. The only legitimate asymmetry is what appears in `{context}`.

---

## Variant 1: Base prompt (v1.0)

**Used by**: E1 through E9 (free-form prose output, keyword-overlap scoring with optional LLM-judge rescoring).

### System

```
You are a research paper analysis agent. Answer the question precisely
and concisely based ONLY on the provided context. Include exact numbers.
```

### User

```
Context:

{context}

---
Question: {question}
```

### Output contract

- Free-form prose.
- Numbers must appear verbatim when relevant.
- Keyword-overlap scoring is applied downstream; LLM-as-judge rescoring is applied separately for bias-reduction.

---

## Variant 2: Matched-output prompt (v1.1)

**Used by**: E10 and all later experiments where both conditions are required to expose evidence pointers.

### System

```
You are an evidence-bound reader.

Use only the supplied document text. Do not use prior knowledge. Every
non-abstained claim MUST include 1-2 verbatim quotes and, for PDF
contexts, the page number from which the quote was taken. Quotes MUST
appear in the supplied context; do not paraphrase.

If the context does not contain sufficient support, set status to
"abstain" (for open-ended questions) or "not_found" (for retrieval
questions). Do not invent evidence.

Output a single valid JSON object and nothing else.
```

### User skeleton

```
Task: Answer the question using only the document below.

Output schema (strict):
{
  "item_id": "<string, echo of the question id>",
  "status": "answer | partial | abstain | supported | ambiguous | not_found",
  "answer": "<string, omitted or empty for retrieval-only items>",
  "confidence": <float in [0,1]>,
  "evidence": [
    {
      "source": "paper" | "review",
      "page": <integer, 0 if context is a sidecar YAML>,
      "quote": "<verbatim string, <=20 words>",
      "support": "direct" | "indirect"
    }
  ],
  "reason": "<string, <=25 words>"
}

Document:
{context}

Question id: {question_id}
Question: {question_text}

Output:
```

### Context-specific page handling

- **PDF context**: each page is prefixed with a `[PAGE N]` tag on its own line; the consumer MUST echo the integer `N` in the `evidence[].page` field for any quote lifted from that page.
- **Sidecar context**: the YAML text has no pages; set `evidence[].page = 0` and `evidence[].source = "paper"`. The quote MUST be a verbatim substring of the sidecar YAML (a statement text, evidence summary, or qualitative observation).

### Output contract

- Exactly one JSON object. Any preamble, trailing text, Markdown fences, or natural-language commentary invalidates the response.
- `confidence` ∈ [0, 1] is used by Algorithm 1's threshold τ for the fallback decision. Calibration is not required for the tech-report; consistency across same-model runs is sufficient.
- `evidence` MUST be non-empty when `status ∈ {answer, partial, supported}`. It MAY be empty when `status ∈ {abstain, not_found}`.
- `reason` ≤ 25 words explains WHY the status was chosen (e.g., "exact figure given in Table 2 page 12").

---

## Versioning

- `v1.0` — base prompt, free-form. Frozen; used for historical comparison with published E1 numbers.
- `v1.1` — matched-output extension. Used by E10 and later.

Any change to either variant increments the minor version and MUST be documented in the project changelog.

---

## Scoring

- **Base (v1.0)**: keyword overlap with 40% phrase-match threshold; optional LLM-as-judge rescoring.
- **Matched-output (v1.1)**:
  - `status == "answer"` AND answer matches ground truth by keyword OR LLM-judge → correct.
  - `status == "partial"` → half credit.
  - `status == "abstain"` when ground truth exists → incorrect.
  - `status == "not_found"` when ground truth does not exist → correct.
  - Evidence validity is scored separately by the audit-trace rubric (see the evaluation harness).

---

## Provenance and auditability

Every experiment run MUST log, per question:

1. The full system message (verbatim).
2. The full user message (verbatim).
3. The model ID and provider (OpenRouter slug, Anthropic direct, or "subagent").
4. The raw response text before any parsing.
5. The parsed response (or parse error).
6. Wall-clock latency and token counts.

This log is the reproducibility artefact; it MUST be committed to the repository before the corresponding results table is cited in the paper.
