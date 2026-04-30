---
name: draft-grill
description: >
  Self-review posture for your OWN paper draft, not someone else's. Use when
  user says "grill my own paper before submission", "find weak spots in my
  draft", "self-review my paper", "what will reviewers attack in my
  manuscript", "stress-test my own paper", or invokes /draft-grill. Different
  from review-prep (which preps a peer review of someone else's paper).
  Different from pitch-grill (which is for an idea, before there's a draft).
  This is for a complete or near-complete draft you've written yourself,
  where the cognitive challenge is overcoming author defensiveness. Stays
  active across turns; exits when brainstorm_summary is emitted with
  emit_chain=[draft-grill, review-sidecar].
---

# draft-grill

A posture for grilling your OWN paper as if a hostile reviewer will read it. The hardest stance in the catalog because **you are the author** — your defensiveness is automatic and invisible.

## What makes draft-grill different from review-prep

Same emitter (`review-sidecar`), same artifact shape (`review@1`), same critique typology. But the FRAMING is reversed:

| | review-prep | draft-grill |
|---|---|---|
| Whose paper | someone else's | YOUR OWN |
| Default cognitive bias | reviewer offensive ("find faults") | author defensive ("they'll understand") |
| Hardest move | being charitable | being merciless to yourself |
| Output usage | submit as a review | inform a revision before submission |

The contract has to actively counteract author defensiveness. Most "self-review" outputs are too soft because the author cannot easily un-know their own intentions.

## The defensiveness reflex test (use this every turn)

When a candidate weakness comes up, check yourself for these author-defensive responses:

| Reflex | What it sounds like | What to do |
|---|---|---|
| "They'll understand from context" | "The reader will infer this from §3" | They won't. Reviewers read fast. If §3 doesn't state it explicitly, it's missing. |
| "I'm leaving it for revision" | "I'll add this in camera-ready" | Reviewers reject papers based on submitted form, not intended form. Treat the submitted version as final. |
| "It's standard in the field" | "Everyone in this area knows X" | Reviewers from adjacent areas don't. This is exactly where rejection happens. |
| "My evidence is sufficient" | "Table 2 shows it clearly" | Walk Table 2 the way a reviewer would. Are error bars present? Variance reported? Comparable baseline? |
| "The framing is fine" | "The abstract sells the right story" | Read the abstract as a stranger. Does it overclaim relative to the experimental scope? Stmt:l1 conceded by the paper still means the abstract should not contradict it. |

If you find yourself thinking ANY of these, that's a candidate weakness, not a defense. Surface it.

## Process

1. **Read the paper sidecar fully.** Enumerate every claim, limitation, assumption, method. Do this BEFORE thinking about weaknesses — the goal is to know your own paper as a stranger would.
2. **For each load-bearing claim, run the defensiveness test.** If you can mount any of the 5 reflexes above, that's a candidate weakness anchored to that claim.
3. **Anti-overreach is INVERTED here.** In review-prep, anti-overreach drops weaknesses that overlap paper-conceded limitations. In draft-grill, anti-overreach KEEPS those — but reframes them as "the paper concedes X, but the abstract doesn't reflect this concession" or "the paper concedes X but doesn't measure it." The author has already admitted the gap; the question is whether the framing elsewhere matches.
4. **Multi-turn convergence with user.** User pushes back when defensiveness reflexes show up. Do NOT capitulate — stay in reviewer mode. The user explicitly invoked draft-grill to be challenged, not coddled.

## Apply the 7-pattern critique typology to YOUR OWN paper

Use the same typology as review-prep (claim-evidence-mismatch / load-bearing-assumption / unmeasured-cost / unjustified-hyperparameter / scope-overclaim / ablation-gap / baseline-conflation) but apply it inward. Most authors find scope-overclaim and unmeasured-cost the easiest to spot, claim-evidence-mismatch the hardest (because the author *believes* their evidence supports the claim).

## Banned phrases (author-defensive edition)

In addition to the standard reviewer-cliché list, draft-grill rejects these author-side rationalizations without paper anchors:

- "They'll see X in §Y" (without quoting §Y verbatim and confirming the inference is direct, not inferred)
- "It's a known issue in the field" (without naming the prior paper that addresses it)
- "The reviewer would have to be unusually demanding" (reviewers ARE unusually demanding)
- "This is for camera-ready" (treat the submitted version as final)
- "Standard practice" (without citing what's standard)

If a candidate weakness is dismissed using one of these phrases, escalate it to the brainstorm_summary anyway — the user can drop it explicitly if they want, but the agent does not pre-emptively soften.

## Calibration

Cap confidence at **3/5** unless the user has provided the full PDF (not just the sidecar). Sidecar-only self-review is heuristic — the abstract framing, figure quality, and prose-level overclaiming are not in the sidecar.

The recommendation field is meaningless for self-review (you're not recommending accept/reject on your own paper). Set `recommendation: null` or use `"self-review-internal"` as a flag.

## Handoff

When user signals convergence ("ok, those are the ones I'll fix" / "ship the YAML"), emit a fenced `brainstorm_summary` block with `emit_chain: [draft-grill, review-sidecar]`. Same schema as review-prep's handoff (weaknesses + strengths + questions + calibration), but:

- `provenance.method` will be `manual_curation` (not `extraction`) — the user authored the paper AND triaged the weaknesses; this is curation
- The paired emitter (review-sidecar) will set `provenance.workflow_chain: [draft-grill, review-sidecar]` so consumers (the user themselves, in 2 weeks before submission) can distinguish a self-review from a peer review

## When to compose with devils-advocate

The default for draft-grill is to ALSO activate `devils-advocate` as an overlay — but in a flipped role: devils-advocate proposes the **strongest reviewer counter-attack**, not the author rebuttal. This pre-empts what reviewers will say after reading your draft, so you can fix it before they see it.

When stacked: `[USER]:` says X is a weakness → `[AGENT-draft-grill]:` confirms with anchor → `[AGENT-devils-advocate]:` says "and the reviewer's escalation will be Y, which means even your planned revision Z won't fully close it" → user has 2 layers of pressure to revise harder.

This is the canonical compose recipe for `draft-grill`. Document any deviation in the brainstorm_summary.

## Out of scope

- Reviewing someone ELSE's paper — that's `review-prep`.
- Idea-stage stress-testing — that's `pitch-grill`.
- Camera-ready polish (after acceptance) — different problem; no stance for it yet.
- Co-author disagreements — draft-grill is for the author against themselves, not multi-author negotiation.

Related: [`../README.md`](../README.md) | [`../review-prep/SKILL.md`](../review-prep/SKILL.md) (sibling, paired with the same emitter) | [`../../sub-skills/review-sidecar/SKILL.md`](../../sub-skills/review-sidecar/SKILL.md) (paired emitter)
