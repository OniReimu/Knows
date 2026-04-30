---
name: stance-mix
description: >
  Use-case → stance-combo dispatcher. Use when user describes a research
  use case at high abstraction without naming a specific stance or
  emitter — e.g., "I want to do a self-review of my paper", "help me
  respond to reviewer comments", "I want to publish a community
  commentary on this paper", "what should I do next on topic X". Or
  invokes /stance-mix. NOT for explicit artifact requests ("give me a
  YAML", "generate a sidecar" — those go directly to Type A) or for
  explicit stance triggers ("let's brainstorm" — those go directly to
  the named stance). Fills the gap between Q5 Rule 1 and Rule 2:
  abstract use-case statements that need interpretation.
---

# stance-mix

A meta-stance that interprets a use-case description and proposes the right combination of stance(s) + emitter(s) to invoke. Not a workflow itself — it is a 1-turn dispatcher.

## Behavior

When activated, you do EXACTLY this in one turn:

1. Restate the user's use case in your own words. ONE sentence. If you can't restate it precisely, ask the user to clarify before recommending anything.
2. Propose ONE primary chain (host stance + emitter) that fits the use case.
3. Propose 0–2 standalone stance overlays that make the chain sharper for THIS specific use case.
4. List what the user would say to activate each piece.
5. Stop. Do not run the chain yourself. The user activates explicitly.

That's the whole skill. ~30 seconds of agent time per dispatch.

## Use-case → stance-combo mapping (the lookup table)

| User says / means | Primary chain | Recommended overlays | Why these overlays |
|---|---|---|---|
| "self-review my own paper before submission" / "grill my own paper" / "find weak spots in my draft" | **draft-grill** → review-sidecar | + devils-advocate (default) | draft-grill is purpose-built for self-review — it counteracts author defensiveness in ways review-prep does NOT (review-prep assumes you're reviewing someone else's paper, where defensiveness isn't the failure mode). devils-advocate plays the reviewer escalating each weakness. |
| "let's prep a peer review for paper X (someone else's paper)" | review-prep → review-sidecar | + devils-advocate | preempt reviewer counter-arguments before submitting the review |
| "I have reviewer comments, help me respond" | rebuttal-prep → rebuttal-builder | + devils-advocate (if rebuttals are politically sensitive) | anticipate reviewer counter-rebuttal in revision round |
| "I want to publish a community-grade commentary on paper X" | paper-brainstorm → commentary-builder | + devils-advocate (if rigor is paramount) | sharper anti-overreach |
| "I want to publish a community commentary, but I don't know much about the field" | paper-brainstorm → commentary-builder | + socratic | user-led discovery — agent only asks |
| "I want to brainstorm reading notes on paper X for myself (not for hub)" | paper-brainstorm (skip emitter, stay solo or 1-shot commentary) | (none) | private notes don't need consume-mode rigor |
| "Grill my paper idea" | pitch-grill → sidecar-author | + red-team | deployment failure modes alongside originality/feasibility/scope |
| "Pre-pitch feedback on a research idea" | pitch-grill (no emitter — just grill, don't commit a sidecar yet) | + socratic | force user to articulate themselves rather than agent rephrasing |
| "Write a related-work paragraph on topic X" | survey-shape → survey-narrative | + executive-summary | also produce 3-bullet TL;DR for talks/posters |
| "Compare these N papers in a table" | survey-shape → survey-table | (none — table is already structured output) | — |
| "What should I work on next in topic X" | (no stance — direct call to next-step-advisor solo) | (none) | next-step-advisor is retrieval, not collaboration |
| "Find papers on topic X" | (no stance — direct call to paper-finder solo) | (none) | retrieval-only |
| "Argue against my plan" / "stress-test this approach" | (no chain — devils-advocate solo) | + red-team | premise critique + failure-mode mapping |
| "Find the attack surface of system X" | (no chain — red-team solo) | (none) | already specific |
| "I'm stuck and want to think through something" | (no chain — socratic solo) | (none) | dialogue-only |
| "Compress this to 3 bullets" / "TL;DR" | (no chain — executive-summary solo) | (none) | already specific |
| "I have a paper PDF and want to generate a sidecar from it locally" | (no stance — sidecar-author Path D solo) | (none) | mechanical extraction; hub upload is unavailable in v1.0 (POST /sidecars UNVERIFIED). |
| "I have a paper PDF and want to publish it on the hub" | **NOT supported in v1.0** — recommend the local-only path (above row) and tell the user that hub upload (POST /sidecars) is currently unverified per `api-schema.md`. Do NOT propose sidecar-author as a solution to "publish on the hub" — it produces local YAML only. | — | Honest scope: stance-mix MUST surface the upload gap rather than route to a workflow that can't satisfy the stated goal. |

## Output format (1-turn)

Restate + chain proposal + overlays + activation phrases. Keep it short:

```markdown
**Restated**: <one sentence — what you think the user is asking for>

**Recommended chain**: `<host-stance>` → `<emitter>` (or "no chain — `<solo-skill>` is sufficient")

**Overlays**: `<standalone>` (`reason`), `<standalone>` (`reason`)
(or "none — base chain is sufficient")

**To activate, say**:
- "<phrase that triggers the host stance>"
- (then mid-conversation, if you want overlays:) "<phrase to layer on the standalone>"

**Skip this combo if**: <one-sentence guard — when this proposal is wrong>
```

Then stop. Do NOT immediately switch into the proposed stance. The user must explicitly accept by activating.

## When to refuse / redirect

- User describes a use case for a Type A artifact directly ("give me a commentary on paper X") — redirect: this is Q5 Rule 1, route to commentary-builder solo, not through stance-mix.
- User names a specific stance ("let's brainstorm") — redirect: this is Q5 Rule 2, activate that stance directly.
- User's use case doesn't fit ANY entry in the lookup table — say so honestly. Suggest one of: rephrase the request more concretely, browse `stances/README.md` index, or describe the artifact they want at the end.

## Anti-pad rules

- **Never propose more than 1 host stance**. If two host stances fit, pick the closer one and mention the other as alternative — but don't compose two hosts (the catalog rules forbid it).
- **Cap overlays at 2**. Three+ overlays confuses the user about which is doing what.
- **Don't re-derive the lookup table per call** — use the table above. If a use case isn't in the table, surface that gap rather than improvising.

## Out of scope

- Auto-activating the proposed chain. The user must explicitly invoke. Stance-mix is advisory.
- Long-form workflow design. If user needs a design discussion, use codex-discuss instead.
- Maintaining the lookup table itself. New use cases added by editing this SKILL.md, not by stance-mix runtime decisions.

## Why stance-mix exists (Q5 gap-fill)

Q5 of the v0.11 design lock specifies: explicit Type A artifact requests bypass auto-activated stances (Rule 1); Type B activates only on explicit explore/brainstorm intent (Rule 2). What's NOT covered: **abstract use-case statements that imply a workflow but name neither an artifact nor a stance**. E.g., "self-review my paper" — the user wants the WORKFLOW (prep + emit) but hasn't said "review-sidecar" or "let's brainstorm". stance-mix fills this gap by interpreting the use case and proposing the right activation.

If users always knew which stance to invoke, stance-mix would be redundant. In practice, users describe use cases at higher abstraction; stance-mix translates that abstraction into the stance vocabulary.

Related: [`../README.md`](../README.md) (especially § "Activation precedence rule" and § "Stance composition rules") | [`../../sub-skills/`](../../sub-skills/) (Type A emitter index)
