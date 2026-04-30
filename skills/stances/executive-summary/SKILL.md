---
name: executive-summary
description: >
  Compression posture. Use when user says "compress this to 3 bullets",
  "executive summary please", "give me the TL;DR", "what's the bottom
  line", "summarize for a busy reader", or invokes /executive-summary.
  Standalone — does not chain into a Type A emitter. Composes with any
  task-bound stance or after any Type A artifact is produced (compress
  the artifact's prose for non-technical or deadline-pressed readers).
  Stays active until user says "stop summary mode" or "give me the
  full version".
---

# executive-summary

A posture for ruthless compression. You produce 3 bullets, max 5, each ≤ 15 words. The reader has 15 seconds.

## What survives compression

In order of priority:
1. **The bottom line** — what should the reader DO or KNOW after these 15 seconds? (One bullet.)
2. **The load-bearing reason** — the strongest single piece of evidence or reasoning. (One bullet.)
3. **The most important caveat** — the gotcha that, if missed, leads to a wrong decision. (One bullet.)

If you have room (4-5 bullets), add: a numeric anchor, OR a comparison to a baseline the reader knows, OR the next decision point.

## What gets cut

- Justification of the structure ("This summary is organized as...")
- Prefixes ("In summary," / "To recap," / "The key takeaways are:")
- Hedges ("It seems that," / "Generally," / "In some cases,")
- Articles where they're optional in compressed form (this is the caveman trick — but apply it lightly here unless user explicitly asks for caveman+executive-summary)
- Any sentence that starts with "I" or "we"

## Format

```
- <bottom line, ≤ 15 words>
- <load-bearing reason, ≤ 15 words>
- <most important caveat, ≤ 15 words>
```

That's it. No headers, no preambles, no follow-up questions. If the user wants follow-up, they'll ask.

## Composes with other stances

This stance stacks naturally:

- **paper-brainstorm + executive-summary** → after brainstorm convergence, before emitting brainstorm_summary, give the user the 3-bullet version of the agreed reflections so they can sanity-check at a glance.
- **review-prep + executive-summary** → after the weakness/strength set is locked, give the user a 3-bullet summary they can paste into the review form's overall recommendation field.
- **<any Type A output> + executive-summary** → take the artifact (commentary, review, rebuttal_doc, related-work paragraph) and produce a 3-bullet compression for the busy reader.

When stacked, this stance OVERRIDES the host's natural verbosity but does not affect the host's handoff or output format. The 3 bullets are a parallel deliverable, not a replacement.

## Edge cases

- **Topic genuinely needs more than 3 bullets**: push back. Tell the user "this doesn't compress to 3 — what's the 1-bullet version of which axis they care about, and we'll go from there." Don't pad to 6 just because the topic is rich.
- **Topic too thin to fill 3 bullets**: 1 or 2 is fine. Don't invent bullets.
- **User asks for "executive summary" of something that's already short** (e.g., a 2-paragraph artifact): the right move is "this is already short — what's the further-compressed version you actually want?" or compress to 1 bullet.

## Banned filler

These are the standard executive-summary clichés to avoid:
- "key takeaways" (just give them, don't label them)
- "high-level overview"
- "deep dive" / "comprehensive look"
- "in essence" / "fundamentally" / "ultimately"
- "moving forward" / "going forward"

Drop. They eat the 15-word budget.

## Exit conditions

You're done when:
1. User explicitly exits ("stop summary mode" / "give me the full version" / "expand bullet 2")
2. User accepts the bullets and moves to the next task

If user says "expand bullet 2", you DO expand — exit summary mode for that one bullet, then re-enter.

Related: [`../README.md`](../README.md) | composes with any host stance or any Type A artifact
