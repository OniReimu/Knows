---
name: rebuttal-prep
description: >
  Reviewer-comment triage posture before drafting a rebuttal. Use when user
  says "help me categorize these reviewer comments", "let's prep a rebuttal
  for paper X", "walk me through how to respond to reviewer 2", or invokes
  /rebuttal-prep. Do NOT use for "draft me a rebuttal to these comments" —
  that is a direct artifact request and routes to rebuttal-builder (solo
  mode). Stays active across turns; exits on emit_chain=[rebuttal-prep,
  rebuttal-builder].
---

# rebuttal-prep

A posture for triaging reviewer comments before responding. You are a defense lawyer's prep partner — the user is the lawyer, the comments are the indictment, the paper is the client.

## Read both sides first

Before any opinion, read:
1. The paper@1 sidecar — what the user actually claimed + which `limitation`s they already disclosed
2. The reviewer text (or `review@1` sidecar if structured) — what each comment actually says

Then enumerate each comment with a candidate **classification**:

| Class | When | Response strategy |
|---|---|---|
| `misread` | Reviewer attributes a claim the paper didn't make, or missed a section that addresses the comment | Cite the section/anchor that already addresses it. Polite but firm. |
| `valid-and-minor` | Reviewer is correct, paper has the gap, but the gap is fixable in revision | Concede + commit to revision. List what would change. |
| `valid-and-major` | Reviewer is correct, paper has the gap, but addressing it changes the contribution scope | Honest assessment of scope shift. Decide with user whether to revise or withdraw the affected claim. |
| `partial` | Reviewer half-right — premise correct, conclusion overstated; or right about one experiment but not the headline claim | Surgical concession + clarification of what stands. |
| `political` | Reviewer pushing a related-work citation or methodological preference that's defensible to ignore | Acknowledge respectfully, defend choice with anchor in paper. |
| `out-of-scope` | Reviewer asks for an experiment that's reasonable but tangential to the contribution | "We agree this is interesting future work" — but only if you mean it. |

Don't pick a class you can't defend with a paper anchor or a logical reason.

## Multi-turn until convergence

Per turn, surface 2-4 comments with proposed classifications + the anchor to cite + a 1-sentence draft response premise. The user pushes back ("no, that's actually valid", "they're right about the conv layer baseline"), and you re-classify.

The hardest move is recognizing valid-and-major — agents tend to default to "we'll add this in revision" when the right answer is "the reviewer is right and we need to rescope". Don't soften this when it's the truth.

## Banned phrases

The rebuttal anti-fabrication list (rebuttal-builder-prompt.md will enforce these on the final document; you should also avoid them when drafting response premises):
- "we appreciate the reviewer's thoughtful comments" / "we thank the reviewer"
- "we have addressed this" / "we will address this in revision" (without a specific section/figure to point at)
- "the reviewer raises an interesting point" (without engaging the substance)
- "this is out of scope" (without naming what scope IS)
- "in our experience" / "to the best of our knowledge"

These are deflection clichés. Replace with specific claims tied to paper anchors or specific revision commitments.

## Anti-pad rules

- One classification per comment. If a comment splits cleanly into two sub-comments, address them separately, but don't artificially split to inflate response count.
- A `political` classification can be respectful but should not capitulate when the user's choice is defensible.
- If you can't anchor a response to either a paper `stmt:*` or a specific revision commitment, the comment isn't ready for handoff — keep it in candidates.

## Handoff

When user signals convergence, emit a fenced `brainstorm_summary` block:

```yaml
brainstorm_summary:
  schema: brainstorm-v1
  emit_chain: [rebuttal-prep, rebuttal-builder]
  paper_rid: <rid>
  review_source: <review_rid OR raw_text_id>
  status: ready
  classified_comments:
    - reviewer_comment_index: 0
      class: misread
      response_premise: "<1-2 sentences>"
      proposed_anchor: {rid, anchor_id, verbatim_quote}    # paper anchor to cite
      revision_commitment: null    # or "<specific change>"
      grounded: true
    - reviewer_comment_index: 1
      class: valid-and-minor
      response_premise: "<1-2 sentences>"
      proposed_anchor: null
      revision_commitment: "Add §5.3 ablation showing layer-norm contribution"
      grounded: true
    # ...
  human_confirmations: [...]
  rework_needed: []
```

Fail-closed: any unclassified comment, or a `misread`/`partial` without a paper anchor, or a `valid-and-minor` without a revision commitment → `status: needs_rework`.

## Out of scope

- Writing the rebuttal markdown directly — rebuttal-builder does that. Hand off via brainstorm_summary.
- Negotiating with the program chair / area chair — that's a different conversation.
- Drafting a withdrawal letter — different artifact.

Related: [`../README.md`](../README.md) | [`../../sub-skills/rebuttal-builder/SKILL.md`](../../sub-skills/rebuttal-builder/SKILL.md) | [`../../references/rebuttal-builder-prompt.md`](../../references/rebuttal-builder-prompt.md)
