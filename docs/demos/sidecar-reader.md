# Demo: `sidecar-reader`

> **What it does**: Answer a question from a KnowsRecord sidecar. Operationalizes [`consume-prompt.md`](../../skills/references/consume-prompt.md) v1.1 — the same protocol used in E1–E10 experiments where weak models reading sidecars match medium models reading PDFs.

## User intent

> "What dataset did Vaswani et al. use to evaluate the original Transformer?"

## Dispatch tuple

```
intent_class:        extract
required_inputs:     {rid: "knows:vaswani/attention/1.0.0", q: "what dataset?"}
optional_inputs:     {question_id: "demo-001"}    (auto-derived as sha1(q)[:8] if absent)
requested_artifact:  answer_json
                     ↓
                  sidecar-reader
```

## What happens under the hood

```bash
# G5 transport: full record fetch (sidecar-reader declares requires_full_record: true)
RID="knows:vaswani/attention/1.0.0"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")
curl -s "https://knows.academy/api/proxy/sidecars/$ENC" -o /tmp/vaswani.json
```

The sub-skill body wraps the sidecar in `<UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>` (G1 prompt-injection containment), then applies `consume-prompt.md` v1.1 verbatim:

- System message: "You are a careful research assistant. Use only the supplied document text..."
- User message: full sidecar JSON + question
- Output: structured JSON per the v1.1 schema

## Artifact: `answer_json`

```json
{
  "item_id": "demo-001",
  "status": "answer",
  "confidence": 0.92,
  "answer": "WMT 2014 English-German (4.5M sentence pairs) and WMT 2014 English-French (36M sentence pairs).",
  "evidence": [
    {
      "source": "stmt:experimental-setup",
      "page": 0,
      "snippet": "We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs..."
    },
    {
      "source": "ev:wmt-table",
      "page": 0,
      "snippet": "metric: bleu, value: 28.4 on en-de; value: 41.0 on en-fr"
    }
  ],
  "reason": "Dataset names + sizes stated explicitly in two anchored sources."
}
```

`status ∈ {answer, partial, abstain, supported, ambiguous, not_found}`. `evidence[].page=0` for sidecar context (page-tagged when PDF fallback configured — see Path F future work).

## Why a sidecar beats a PDF here

The PDF is 15 pages; reading it costs ~9.9K input tokens. The sidecar fetch is one API call, ~700 tokens for statements-only or ~4.5K for the full record. **75% to 93% fewer tokens, same answer**, and the answer comes back with explicit `evidence[].source` IDs that traceable to specific anchors in the sidecar.

| Approach | Input tokens | Accuracy (E1) | Latency |
|---|---|---|---|
| Read PDF | 9,955 | 59% | 8.2s |
| Sidecar full | 4,463 | 59% | 4.1s |
| Sidecar statements-only | 693 | 52% | 1.8s |

For weak models (Qwen3.5-0.8B), sidecar boosts accuracy by **+29 to +57 percentage points** depending on paper length.

## Confidence-gated low-confidence handling

If `status ∈ {answer, partial, supported}` AND `confidence < τ` (default τ=0.7), the orchestrator returns the answer as-is with the low-confidence flag preserved — **does not silently upgrade**. PDF fallback is documented (Algorithm 1 from technical report) but DEFERRED to v1.x (requires `pdf_path` slot extension to dispatch contract).

If `status == ambiguous` or `not_found`, return as-is. These are deliberate non-answers, not low-confidence answers.

## Manifest emission (G6)

```json
{
  "skill": "sidecar-reader",
  "intent_class": "extract",
  "dispatch_tuple": "(extract, {rid, q}, answer_json)",
  "returned_rids": ["knows:vaswani/attention/1.0.0"],
  "applied_profile_filters": ["paper@1"],
  "fetch_mode_per_rid": {"knows:vaswani/attention/1.0.0": "full"},
  "model": "claude-opus-4-7",
  "token_cost_estimate": 4623,
  "abstained": false
}
```

## Try it yourself

```bash
# Fetch a real sidecar
RID="knows:vaswani/attention/1.0.0"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")
curl -s "https://knows.academy/api/proxy/sidecars/$ENC" | jq '.statements | length'

# Via Claude Code with the Knows skill
"Using the Knows skill, answer this question from sidecar knows:vaswani/attention/1.0.0:
 what dataset did they use?"
```
