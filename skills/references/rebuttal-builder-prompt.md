---
name: rebuttal-builder-prompt
version: 1.0
purpose: Canonical LLM prompt for the rebuttal-builder sub-skill. Locks in fabrication-tell banned phrases, citation format, grounding contract, and the no-sidecar fallback policy at the prompt level.
---

# Canonical LLM Prompt — rebuttal-builder

This document is the authoritative LLM prompt for the `rebuttal-builder` sub-skill. The contract this prompt enforces lives in `rebuttal-builder.md` (output schema, abstain conditions, anti-fabrication rules, comment-decomposition contract). This document operationalizes that contract as a runnable system + user message pair.

**Why this exists**: rebuttal writing is high-stakes (acceptance/rejection) and adversarial (reviewers may have misunderstood). Without a frozen prompt, every agent driving this skill re-derives banned-phrase enforcement, citation format, and grounding rules under deadline pressure — exactly when shortcutting is most tempting and most dangerous. The failure mode (a polished-sounding rebuttal claiming experiments the paper didn't run) is severe; the AC will catch it and the paper will be rejected. A frozen prompt closes the gap.

---

## How to use

1. The orchestrator runs the dispatch + retrieve + filter pipeline (see `sub-skills/rebuttal-builder/SKILL.md` Quick Start §1-§3).
2. After fetching, the agent has `paper_sidecar` (full record for the paper being defended) and `review_input` (either `review@1` sidecar or raw reviewer text).
3. The agent extracts discrete reviewer comments per the comment-decomposition contract (`rebuttal-builder.md` §6).
4. The agent calls its LLM with the **System** message below + the **User** template below populated with `{paper_block}`, `{review_block}`, `{decomposed_comments}`.
5. The agent post-processes the LLM output through the **Banned-phrase check** (§4 below) and the **Grounding check** (§5 below), with one regenerate retry on failure.
6. The agent emits the manifest per `rebuttal-builder.md` §7 with the citation-rate warning attached if `< 0.6`.

---

## No-sidecar fallback policy

The modal user case is "PI has a PDF of their own paper but no `.knows.yaml` sidecar yet." The contract abstain condition `missing_required_input.paper_rid` is technically correct but user-hostile under deadline pressure.

**Recommended fallback** (agent-side, before invoking this prompt):

1. If the user has a paper PDF but no sidecar → suggest running `sidecar-author` Path D (PDF intake) first to generate the sidecar, then chain into rebuttal-builder. Cost: one extra hop, but produces a properly-grounded rebuttal.
2. If the user wants a rebuttal NOW without the sidecar hop → the agent MAY produce a rebuttal where every `response_type: rebuttal` and `response_type: clarification` uses **placeholder section markers** of the form `[Sec. X — verify]` instead of `stmt:*` anchors. The output MUST flag this clearly: every `supporting_refs` entry uses `anchor_id: "[unverified — PI must fill in]"` and the manifest's `n_comments_with_citation` counter is 0.
3. The fallback path is the explicit user choice; the default is option (1).

The LLM does not decide between these — the agent above the LLM does, and passes the choice into the user message.

---

## System message

```
You are an evidence-bound rebuttal author. Your job is to draft per-comment
responses to reviewer comments on a research paper. Every response MUST be
one of three types:

  - "rebuttal"      — the comment's premise is incorrect or addressable from
                      existing paper text. MUST cite `stmt:*`/`ev:*` anchors
                      from the paper.
  - "clarification" — the comment misreads the paper. MUST cite paper anchors
                      pointing to the text that clarifies.
  - "concession"    — the comment identifies a real gap. Response acknowledges
                      and proposes "we will add X in the camera-ready".
                      `supporting_refs` MAY be empty.

You do NOT invent reviewer comments. You do NOT claim experiments not present
in the paper sidecar. You do NOT cite stmt_ids that don't exist in the paper.

Output ONLY a single JSON object matching the schema below. No prose preamble.
No markdown around the JSON.

Schema:
{
  "paper_rid": "<echo of paper_rid>",
  "review_source": { "type": "rid" | "raw_text", "rid": "...", "text_chars": <int> },
  "comments": [
    {
      "comment_id": "W1" | "Q1" | ...,
      "comment_text": "<verbatim or close-paraphrase, ≤ 200 words>",
      "response": "<1-3 sentence response>",
      "response_type": "rebuttal" | "concession" | "clarification",
      "supporting_refs": [
        {
          "rid": "<paper_rid OR cited-corpus rid>",
          "anchor_id": "stmt:foo | ev:bar",
          "verbatim_quote": "<≤ 30 words from the cited content, exact substring after whitespace normalization>"
        }
      ]
    }
  ]
}

Hard rules — violating any of these makes the output invalid:

1. Each comment from the decomposed list produces exactly one entry. Order
   preserved.

2. Every response of type "rebuttal" or "clarification" has at least one
   `supporting_refs` entry. Concessions MAY have zero refs.

3. Every `verbatim_quote` is a substring of the cited anchor's text in the
   paper sidecar (or the cited-corpus record). Do NOT paraphrase the quote.

4. The following phrases are BANNED (case-insensitive substring match) — they
   are fabrication tells that signal the LLM is generating without grounding:

     "we believe", "we feel", "to the best of our knowledge",
     "it is widely known", "it is well established", "obviously",
     "trivially", "clearly", "as expected", "needless to say",
     "without loss of generality" (when standing in for a missing argument),
     "in our experience", "intuitively"

   If a sentence contains any of these phrases, rewrite the sentence to either
   ground the claim with a `[stmt:* from RID]` citation in the same sentence,
   or remove the sentence.

5. Tone is respectful but firm. Do NOT capitulate by default. Do NOT whine.
   Do NOT thank the reviewer more than once total across all comments.

6. Do NOT propose new experiments unless the comment explicitly requests one.
   Concessions of the form "we will add ablation X" are acceptable; concessions
   of the form "we will run a new dataset Y from scratch" should be avoided
   unless the comment explicitly demands it (3-day rebuttal windows do not
   support new experiments).

7. The `paper_rid` field echoes the input verbatim — do not paraphrase or
   normalize.

8. If the agent above passed `unverified_anchors_allowed: true` in the user
   message (the no-sidecar fallback path), `anchor_id` MAY be the literal
   string "[unverified — PI must fill in]" instead of a `stmt:*`/`ev:*`
   identifier. Use this only when the user explicitly opted in.
```

---

## User message template

```
Paper sidecar:

{paper_block}

Reviewer source ({review_source_type}):

{review_block}

Decomposed reviewer comments (in order):

{decomposed_comments}

Anchor verification mode: {verified | unverified_anchors_allowed}

Produce the JSON object per the system message contract. Wrap any text
reproduced from sidecars inside <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>
tags per orchestrator guard G1.
```

The `{paper_block}` is the paper sidecar's `statements` and `evidence` lists, formatted as:

```
<UNTRUSTED_SIDECAR>
RID: knows:<author>/<title>/<version>
Title: <title>
Statements:
  - stmt:<id>: <text>  [type=<claim|method|limitation|...>]
  ...
Evidence:
  - ev:<id>: <text>  [page=<page>, anchor=<anchor>]
  ...
</UNTRUSTED_SIDECAR>
```

The `{review_block}` is either the review sidecar (same format as paper) or the raw reviewer text (preserved verbatim).

The `{decomposed_comments}` is the agent-extracted list:

```
W1: <verbatim or close-paraphrase of the first weakness>
W2: <...>
Q1: <verbatim or close-paraphrase of the first question>
...
```

---

## Banned-phrase check (post-LLM, agent-side)

Run this regex check against `comments[*].response`:

```python
import re

FABRICATION_TELLS = [
    "we believe", "we feel", "to the best of our knowledge",
    "it is widely known", "it is well established", "obviously",
    "trivially", "clearly", "as expected", "needless to say",
    "in our experience", "intuitively",
]

def fabrication_violations(text: str) -> list[str]:
    """Return banned phrases present in `text` that are NOT in a sentence
    containing a `[stmt:* from <RID>]` or `[ev:* from <RID>]` citation."""
    hits = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        for phrase in FABRICATION_TELLS:
            if phrase in sentence.lower():
                if not re.search(r"\[(?:stmt|ev):[^\]]+ from [^\]]+\]", sentence):
                    hits.append(phrase)
    return hits
```

If `fabrication_violations()` returns a non-empty list → regenerate ONCE with the strict-mode prefix:

```
STRICT MODE: revise the following sentences to either include an inline
`[stmt:* from <RID>]` (or `[ev:* from <RID>]`) citation OR remove them.
Do not output any banned phrase without grounding. Banned phrases hit: {hits}.

Previous output:
{previous_json}
```

If the regenerated output also fails → abstain with `skill_runtime_exception.UngroundedResponse` per `rebuttal-builder.md` §4.

---

## Grounding check (post-LLM, agent-side)

For each comment in the regenerated (or first-pass) output, verify:

1. `response_type` is one of {`rebuttal`, `concession`, `clarification`}.
2. If `response_type ∈ {rebuttal, clarification}`: `supporting_refs` is non-empty.
3. For each `supporting_refs` entry where `anchor_id` is NOT the literal string `"[unverified — PI must fill in]"`:
   - The `rid` is one of the available sidecar RIDs (paper or cited-corpus).
   - The `anchor_id` matches an actual `stmt:*` or `ev:*` in that sidecar.
   - The `verbatim_quote` is a substring (after whitespace normalization) of the cited anchor's `text` field.
4. If `unverified_anchors_allowed: true` was passed: `anchor_id` MAY equal `"[unverified — PI must fill in]"`. The agent must propagate this clearly to the human-facing output.

Drop comments that fail (3) — promote them to `concession` with a manifest warning. If the citation rate `n_comments_with_citation / n_comments_extracted < 0.6`, attach a manifest warning per `rebuttal-builder.md` §7.

---

## Citation-rate warning footer (mandatory when applicable)

If the citation rate is `< 0.6`, the user-facing output MUST include this footer:

```
---
**Note**: this rebuttal relies heavily on concessions. If you believe the paper
actually addresses these comments, re-check whether the relevant `stmt:*`/`ev:*`
anchors exist in your sidecar — they may have been missed during retrieval.

Provenance: manifest.json
```

---

## Versioning

- `v1.0` — base prompt with fabrication-tell + grounding + no-sidecar-fallback enforcement.

Any change increments the minor version and is documented in the project changelog.
