# Knows Skills — What You Can Do

Knows skills give you a catalog of workflows for reading, writing, reviewing, and brainstorming research papers. Pick a workflow below by what you're trying to accomplish, not by which skill it uses.

Every workflow runs locally — most don't need internet or a hub upload. For "what is the sidecar format and why", see [`../README.md`](../README.md). For technical details on any single skill, browse [`sub-skills/`](sub-skills/) (artifact emitters) and [`stances/`](stances/) (dialogue postures).

---

## Read & query a paper

**Turn a PDF into a structured sidecar.** Hand `sidecar-author` your `.pdf` and it produces a lint-validated `paper.knows.yaml` with every claim, method, limitation, and citation extracted. Takes 2-5 minutes and the output is a queryable data structure, not a wall of prose.

**Ask grounded questions about a paper.** `sidecar-reader` answers natural-language questions ("what dataset did they use?", "where do they claim beating SOTA?") with citations to specific statements in the sidecar — no hallucinated quotes.

**Q&A your own unpublished draft.** Run `sidecar-author` on your in-progress paper, then `sidecar-reader --local` to interrogate it without uploading anything. Useful when you forgot what you claimed or want to cross-check your limitations.

---

## Self-review your own work

**Self-review your paper before submission.** The `draft-grill` stance grills your own draft as a hostile reviewer would, with built-in checks against author defensiveness ("they'll understand from context", "I'm leaving it for revision"). Stack `devils-advocate` on top and the agent also predicts the reviewer's counter-attack to your planned revisions, so you can fix them before reviewers see them.

**Pressure-test a research idea before committing.** `pitch-grill` interrogates originality, feasibility, and scope across three turns ("what's the closest paper you've actually read?"); add `red-team` to surface deployment failure modes. The surviving idea gets committed as a from-idea sidecar via `sidecar-author`.

---

## Read someone else's paper deeply

**Brainstorm gaps in a paper with reader-led reflection.** `paper-brainstorm` collaborates with you across multiple turns to surface gaps the authors didn't disclose, then `commentary-builder` produces a publishable `commentary@1` sidecar anchored to specific paper statements. Layer `socratic` on top if you want to figure out the gaps yourself with the agent only asking guiding questions.

**Prep a peer review you've been assigned.** `review-prep` finds candidate weaknesses using a 7-pattern critique typology, with anti-overreach checks against the paper's already-conceded limitations. Add `devils-advocate` and you'll also see the rebuttal authors will likely make, helping you preempt counter-arguments before submitting your review.

---

## Respond to reviewer comments

**Triage reviewer comments and draft a rebuttal.** `rebuttal-prep` classifies each reviewer comment (misread / valid-and-minor / valid-and-major / partial / political / out-of-scope) and proposes response premises tied to specific paper anchors, then `rebuttal-builder` produces a per-comment markdown rebuttal. Add `devils-advocate` to anticipate the reviewer's counter-rebuttal in the next round.

---

## Write a survey or related work

**Shape a survey before writing.** `survey-shape` walks you through arc decisions (chronological / methodological / outcome-grouped / gap-driven / consolidating) and centerpiece selection in a few turns, before any prose is written. The same shape decision feeds both `survey-narrative` (1-3 paragraph prose with `\cite{}` keys) and `survey-table` (comparison matrix), so you decide once and get multiple deliverables.

**Find related work for a topic.** `paper-finder` searches the hub by topic with filters for venue and year, ranks results by relevance, and optionally exports a clean BibTeX file. Feed the returned RIDs into `survey-narrative` or `survey-table` to skip the discovery round.

---

## Discover and navigate the literature

**Find what's been said on a topic.** `paper-finder` searches the hub by topic, filters by venue type and year, and sorts by relevance, recency, or claim density.

**Compare two papers side by side.** `paper-compare` produces a structured diff showing shared citations, divergent claims, and outright contradictions between two sidecars.

**Walk a paper's version history.** `version-inspector` traces the chain of replaced sidecars backward, useful when you want to see what changed between revision rounds.

---

## Find your next research direction

**Get a brief on open research questions.** `next-step-advisor` retrieves sidecars on your topic and surfaces grounded next-step candidates from the papers' own admitted limitations and questions, plus any reader-side reflections published in `commentary@1` sidecars. Heuristic by design — bounded by what's on the hub, not corpus-wide.

---

## Pure thinking tools (no artifact produced)

**Argue against your own plan.** `devils-advocate` steelmans the strongest case against any decision or claim you're making, until you either change your mind or successfully defend it.

**Map a system's failure modes.** `red-team` enumerates 3 specific attack vectors per turn (input space, trust boundary, state, composition, scale, etc.), ranked by likelihood × blast radius × mitigation cost. Different from devils-advocate (which questions the premise) — red-team accepts the premise and finds where it breaks.

**Think through a problem without the agent giving answers.** `socratic` mode asks at most 2 questions per turn and never directly answers, useful when you're stuck and want a thinking partner that doesn't short-circuit your reasoning.

**Compress a long output to 3 bullets.** `executive-summary` cuts any input to ≤3 bullets of ≤15 words each, with clichés banned ("key takeaways", "in essence", "moving forward"). Useful for posters, talks, or non-technical readers.

---

## Don't know which workflow to pick?

Tell the agent your use case in plain English ("I want to self-review my paper before NeurIPS submission", "help me respond to reviewer comments", "I want to publish a community commentary on this paper"). The `stance-mix` meta-skill matches the use case to the right primary chain plus standalone overlays, and shows you exactly what to say to activate each piece. You decide whether to accept the proposal — `stance-mix` doesn't auto-cascade.

---

## Where to go next

- **Pick a single skill to learn**: browse [`sub-skills/`](sub-skills/) (12 artifact emitters) or [`stances/`](stances/) (11 dialogue postures).
- **Understand the orchestrator**: read [`SKILL.md`](SKILL.md) for the dispatch contract, recipes, and architecture.
- **Author a new stance or skill**: read [`stances/REFERENCE.md`](stances/REFERENCE.md) and [`references/dispatch-and-profile.md`](references/dispatch-and-profile.md).
- **What is a sidecar**: read the project root [`../README.md`](../README.md).
