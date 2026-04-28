# rebuttal-builder — Reference Contract

**Status**: v1.0. Multi-input skill — uses the `co_inputs` typed slot pattern from `dispatch-and-profile.md` §3.

> **Companion**: `sub-skills/rebuttal-builder/SKILL.md`. When this contract and SKILL.md disagree, **this contract wins**.
>
> **Canonical LLM prompt**: `rebuttal-builder-prompt.md`. Use that prompt verbatim — it operationalizes the contract here (anti-fabrication banned phrases, citation format, grounding, no-sidecar fallback) so individual agents do not re-derive the rules under deadline pressure and silently miss enforcement.

---

## 1. Purpose and scope

Draft per-comment responses to reviewer comments on a paper, citing supporting `stmt:*`/`ev:*` from the paper's own sidecar plus optional supporting citations from the user's corpus.

**Out of scope (load-bearing)**:

- Drafting a rebuttal from open-corpus search alone — must have an explicit `(paper, review)` pair.
- Inventing reviewer comments — if `reviewer_text_or_rid` doesn't decompose cleanly into discrete comments, abstain.
- Auto-suggesting new experiments — only existing-paper defenses.
- Reviewer-disposition modeling.

---

## 2. Input contract (typed co-input slots)

Per `dispatch-and-profile.md` §3, this skill declares typed co-input slots:

```yaml
co_inputs:
  paper:  paper@1                # paper-rid → fetched as full record
  review: review@1               # review-rid OR raw text — see §2.1
```

| Slot | Type | Required | Notes |
|---|---|---|---|
| `paper_rid` | record_id (paper@1) | yes | The paper being defended |
| `reviewer_text_or_rid` | string \| record_id | yes | Either a review@1 RID OR raw reviewer text blob (≥ 50 chars, ≤ 50000) |

### 2.1 review-input dispatch

The `reviewer_text_or_rid` slot accepts two shapes:
- **String matching `^knows:`** → treated as review@1 RID; orchestrator fetches sidecar; profile filter requires `review@1` (else `missing_co_input.review`)
- **Any other string ≥ 50 chars** → treated as raw reviewer text; review slot satisfied directly without API fetch

Empty string / whitespace-only / fewer than 50 chars → `invalid_slot_type.reviewer_text_or_rid` (too short to contain meaningful comments).

---

## 3. Output schema

```jsonc
{
  "paper_rid": "knows:author/title/version",
  "review_source": {
    "type": "rid" | "raw_text",
    "rid": "knows:reviewer/...",       // present when type==rid
    "text_chars": 1234                 // present when type==raw_text
  },
  "comments": [
    {
      "comment_id": "W1" | "W2" | "Q1" | ...,
      "comment_text": "<verbatim or close-paraphrase of reviewer's comment, ≤ 200 words>",
      "response": "<1-3 sentence response, MUST cite paper stmt:*/ev:* OR explicit concession>",
      "response_type": "rebuttal" | "concession" | "clarification",
      "supporting_refs": [
        {
          "rid": "<paper_rid OR cited-corpus rid>",
          "anchor_id": "stmt:foo | ev:bar",
          "verbatim_quote": "<≤ 30 words from cited content>"
        }
      ]
    }
    /* one entry per discrete reviewer comment */
  ],
  "manifest_path": "<path>"
}
```

### 3.1 response_type semantics

- **`rebuttal`** — the comment's premise is incorrect or addressable from existing paper; MUST cite paper `stmt:*`/`ev:*` in `supporting_refs`.
- **`concession`** — the comment identifies a real gap; response acknowledges and proposes "we will add X in the camera-ready". `supporting_refs` MAY be empty.
- **`clarification`** — the comment misreads the paper; response points to the paper text that clarifies. MUST cite paper `stmt:*`/`ev:*`.

---

## 4. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `paper_rid` slot missing | `missing_required_input.paper_rid` |
| `reviewer_text_or_rid` missing or empty | `missing_required_input.reviewer_text_or_rid` |
| Paper rid 404s | `rid_not_found.<rid>` |
| Review rid 404s (when supplied as RID) | `rid_not_found.<rid>` |
| Paper fails G7/G2' | `missing_co_input.paper` |
| Review supplied as RID but profile != review@1 | `missing_co_input.review` |
| Reviewer text decomposes to 0 discrete comments | `skill_runtime_exception.NoCommentsExtracted` |
| Any `response_type: rebuttal` or `clarification` produced without paper-cited `supporting_refs` | `skill_runtime_exception.UngroundedResponse` |

---

## 5. Anti-fabrication rules

- **NEVER invent reviewer comments**. If `reviewer_text_or_rid` doesn't decompose cleanly into discrete comments, abstain — do not LLM-imagine what the reviewer might have said.
- **NEVER claim experiments not in the paper sidecar**. Every "we did X" defense must trace to a `stmt:*` or `ev:*` in the paper.
- **NEVER cite a non-existent stmt_id**. The orchestrator post-validates every `supporting_refs[].anchor_id` against the actual paper sidecar; mismatch → regenerate (one retry) → `skill_runtime_exception.UngroundedResponse`.
- **DO** suggest "we will add Y in the camera-ready" via `response_type: concession`.

---

## 6. Comment decomposition contract

The LLM extracts discrete comments from `reviewer_text_or_rid` using these heuristics (in order):

1. Section markers like `**W1**`, `**Question 1**`, `**Major comment 2**` → use as `comment_id`.
2. Numbered/bulleted lists at top level → assign sequential `W1, W2, ...` or `Q1, Q2, ...` based on context.
3. Paragraph breaks within a flat review → each paragraph treated as one comment.
4. If review is one continuous prose blob with no markers → at most 3 comments extracted (avoid over-fragmentation).

If the heuristics yield 0 comments → abstain. If they yield > 20 comments → cap at 20 with a manifest warning.

---

## 7. Manifest emission contract

```jsonc
{
  "skill": "rebuttal-builder",
  "intent_class": "critique_respond",
  "dispatch_tuple": "(critique_respond,{paper_rid,reviewer_text_or_rid},rebuttal_doc)",
  "returned_rids": [paper_rid, review_rid_if_applicable],
  "applied_profile_filters": {              // multi-input → dict shape per §6.1
    "paper": "paper@1",
    "review": "review@1"                    // or "raw_text" sentinel for non-rid input
  },
  "fetch_mode_per_rid": {... "full"},
  "model": "<llm>",
  "n_comments_extracted": <int>,
  "n_comments_with_citation": <int>,
  "n_comments_concession": <int>
}
```

`n_comments_with_citation / n_comments_extracted` is the citation-rate signal — if < 0.6, the consumer SHOULD warn the user that "this rebuttal relies heavily on concessions; consider whether the paper actually addresses these comments".

---

## 8. Why this contract is load-bearing

Rebuttal writing is high-stakes (acceptance/rejection turns on it) and adversarial (reviewers may have misunderstood). The temptation to fabricate "we did X" is high — the cost of an unsupported rebuttal claim getting caught by the AC is severe.

The "every rebuttal claim MUST cite a paper `stmt:*` / `ev:*` anchor or be an explicit concession" rule is the entire point of this skill. Without it, the output is ungrounded text the user cannot verify under deadline pressure. With it, the skill becomes a forcing function: the user must actually re-read their paper to confirm the cited anchor before sending the rebuttal.

