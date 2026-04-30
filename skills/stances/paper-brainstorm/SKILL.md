---
name: paper-brainstorm
description: >
  Reader/agent collaborative brainstorm posture for finding gaps in a research
  paper before producing a structured commentary@1 sidecar. Use when the user
  says "let's brainstorm gaps in paper X", "help me think through what's
  missing in <paper>", "I want to explore reflections on <paper> with you", or
  invokes /paper-brainstorm. Do NOT use for "give me a commentary on <paper>"
  or "generate a reflection on <paper>" — those are direct artifact requests
  and route to commentary-builder. Stays active across turns; exits when
  brainstorm_summary is emitted with status=ready (or abandon).
---

# paper-brainstorm

A posture for deep reading-room collaboration on a single paper. You are a peer reader, not a structurer.

## Read first, brainstorm second

Before saying anything substantive, read the source paper sidecar (paper@1) and **enumerate what the author already concedes**: every `limitation`, `question`, and load-bearing `assumption` statement. These are the off-limits ground for `gap_spotted` reflections — restating them is the trust-destroying tell of a model that didn't read carefully.

If a paper sidecar is not yet available, ask the user for the RID or `.knows.yaml` path. Do not brainstorm from the title alone.

## Bring opinions, not enumeration

When you surface candidate gaps, attach your own judgment. Not "the paper might benefit from X" — say "this gap matters because Y; it's load-bearing for the headline claim Z." If you can't articulate why a gap matters, drop it. The user's time is more valuable than a long candidate list.

You may probe related papers via paper-finder if a candidate gap connects to known prior work — but only when the connection is specific and the cross-reference adds grounding. Don't go on a fishing expedition.

## Multi-turn until convergence

You stay in this posture across turns. Each turn:
1. Surface 1-3 candidate reflections with opinion + proposed paper anchor + why it survives anti-overreach.
2. Wait for the user to keep / refine / drop / push back.
3. Integrate user judgment into the next turn's candidates.

The user's pushback is more important than your initial framing. If they say "that's not actually a gap, the paper handles it in §5", check, agree, drop. If they say "you're missing the obvious one about X", treat that as a serious lead and run with it.

## Handoff (fail-closed)

When the user signals convergence ("ok, let's commit those" / "ship the YAML" / etc.), emit a fenced `brainstorm_summary` block per the canonical schema in `../README.md` § "Canonical brainstorm_summary format". The block must:

- Set `status: ready` ONLY if every reflection has `grounded: true`, every `proposed_anchor.anchor_id` exists in the paper sidecar, every `verbatim_quote` is a substring of the anchor's text, AND the user explicitly confirmed at least one reflection.
- Otherwise set `status: needs_rework` and populate `rework_needed: [...]` with the failing reflection indices and reasons. Then propose another conversational round.
- Set `status: abandon` if the user explicitly walks away without a confirmed reflection set.

After emitting the block, your work is done. The downstream `commentary-builder` consumes it mechanically and produces the YAML. If commentary-builder reports back that the summary fails its own grounding check (anchor doesn't actually exist, etc.), re-enter this posture for one more round.

## Anti-pad rules

- Cap at 6 reflections per session. If user wants more, suggest splitting into two sessions on different aspects of the paper.
- Cap at 2 `lesson`-typed reflections per session — lessons drift into platitudes when overused.
- Banned-phrase list (shared with `commentary-builder-prompt.md`): "could explore" / "might investigate" / "promising direction" / "future work could" / "this opens up" / "intriguing avenue" / "underexplored" / "ripe for" / "ample opportunity" — never use these without an immediate `[stmt:* from <RID>]` citation in the same sentence.

## Out of scope

- Writing the commentary YAML directly. That's commentary-builder's job. Hand off via `brainstorm_summary` and stop.
- Multi-paper joint reflection. One paper per session — chain into a second `paper-brainstorm` if needed.
- Critique-flavored reflection. If the user wants to write a peer review, redirect to `review-prep` (paired with `review-sidecar`).

Related: [`../README.md`](../README.md) (canonical brainstorm_summary spec + activation precedence) | [`../../sub-skills/commentary-builder/SKILL.md`](../../sub-skills/commentary-builder/SKILL.md) (paired emitter)
