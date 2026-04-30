# Interaction Stances — Catalog (v0.11.2)

Knows has two kinds of sub-skill: **emitters** (in `../sub-skills/`) produce schema-validated artifacts; **stances** (this directory) trigger thinking/dialogue postures. Stances are short, mattpocock-style — pick one, the agent flips into that mode of working with you.

Stances optionally chain into emitters: free dialogue with the stance, then the emitter mechanically translates the agreed output into a strict YAML/Markdown artifact. **For depth on contracts, composition, frontmatter conventions, and how to author a new stance, see [`REFERENCE.md`](REFERENCE.md).** This README is just the user-facing catalog.

## Stance index

| Stance | Trigger | Pairs with (emitter) | Purpose |
|---|---|---|---|
| [`paper-brainstorm`](paper-brainstorm/SKILL.md) | "let's brainstorm gaps in paper X" | `commentary-builder` | Reader-agent collaborative reflection on a paper → grounded `commentary@1` |
| [`review-prep`](review-prep/SKILL.md) | "let's prep a review for paper X" | `review-sidecar` | Pre-critique deep-read of someone ELSE's paper → `review@1` |
| [`draft-grill`](draft-grill/SKILL.md) *(v0.11.2)* | "grill my own paper before submission" | `review-sidecar` | Self-review on YOUR OWN draft. Counteracts author defensiveness. Same emitter as review-prep, opposite cognitive framing. |
| [`rebuttal-prep`](rebuttal-prep/SKILL.md) | "help me categorize these reviewer comments" | `rebuttal-builder` | Triage reviewer comments (misread / valid / partial / political) → `rebuttal_doc` |
| [`pitch-grill`](pitch-grill/SKILL.md) | "grill my paper idea" | `sidecar-author` (from-idea path) | Stress-test originality / feasibility / scope on an idea (no draft yet) → from-idea `paper@1` |
| [`survey-shape`](survey-shape/SKILL.md) | "help me shape this survey" | `survey-narrative` / `survey-table` | Decide narrative arc / centerpieces / comparison axes → prose or table |
| [`devils-advocate`](devils-advocate/SKILL.md) | "argue against my plan" / "steelman the opposite" | (standalone — composes) | Premise critique. Different from red-team (which maps system failures). |
| [`executive-summary`](executive-summary/SKILL.md) | "compress this to 3 bullets" / "TL;DR" | (standalone — composes) | Compress long content to executive form. Parallel deliverable. |
| [`socratic`](socratic/SKILL.md) | "ask me questions instead", "Socratic mode" | (standalone — composes) | Question-driven; never directly answer. |
| [`red-team`](red-team/SKILL.md) | "find the attack surface", "red-team my plan" | (standalone — composes) | System-failure mapping. Different from devils-advocate (premise critique). |
| [`stance-mix`](stance-mix/SKILL.md) | abstract use-case w/o specific stance ("self-review my paper", "respond to reviewers") | (meta — proposes other stances) | 1-turn dispatcher: maps high-level use case → primary chain + overlays. |

Stances NOT in v0.11.2 (deferred unless demand): `eli5`, `archaeologist`, `revision-coach`, `compare-debate`.

## Activation precedence rule

Without an explicit precedence rule, prompts like *"give me a commentary on paper X"* match BOTH `commentary-builder` (artifact request) AND `paper-brainstorm` (reflective intent) via auto-activation, producing nondeterministic routing.

The locked rule:

1. **Explicit Type A artifact requests bypass auto-activated stances.** Verbs like *give me, generate, produce, make, lint, compare, analyze, summarize* → route to Type A directly. The user wants the artifact.

   **1.5. Abstract use-case statements** (neither Rule 1 nor Rule 2 applies) → activate `stance-mix`, the meta-stance dispatcher. Examples: *"self-review my paper", "respond to reviewer comments", "publish a community commentary on this paper"*. stance-mix proposes a chain + overlays for the user to explicitly activate. See [`stance-mix/SKILL.md`](stance-mix/SKILL.md).

2. **Type B activates only when user explicitly asks to think/explore.** Triggers: *let's brainstorm, help me think, walk me through, explore this, /<stance-name>* → activate the stance. The dialogue is the goal.

3. **Once a Type B stance is active, the stance decides when to hand off** by emitting a fenced `brainstorm_summary` block (canonical schema in [`REFERENCE.md`](REFERENCE.md)). Auto-activation does NOT cascade — the user being mid-brainstorm should not retrigger Type A every time they mention an emitter's keyword in conversation.

4. **Slash commands always win.** `/<skill-name>` is unambiguous and overrides any heuristic.

## How chains work (1-paragraph summary)

The stance does free dialogue across multiple turns. When convergence is reached, the stance emits a fenced `brainstorm_summary` YAML block that carries the user-confirmed reflections, weaknesses, pitch, or shape decisions (depending on the host stance). The paired emitter (Type A) consumes this block in CONSUME MODE — mechanical translation, no re-brainstorming, fail-closed if any reflection is unanchored or unconfirmed. The output sidecar's `provenance.workflow_chain` field records the chain so downstream consumers can distinguish chain-derived from solo-mode artifacts. Full schema and fail-closed semantics in [`REFERENCE.md`](REFERENCE.md).

## Stances that compose

Standalone stances (`devils-advocate`, `executive-summary`, `socratic`, `red-team`) layer on top of a host stance to sharpen output. **Cap at 2 standalone overlays per session** — past 2, composition gets noisy. The default compose recipes per host are documented in each stance's SKILL.md; the full validated recipe list and conflict-resolution rules live in [`REFERENCE.md`](REFERENCE.md).

Examples:

- `paper-brainstorm + devils-advocate` — for each candidate gap, also argue why it's NOT a gap (sharper anti-overreach)
- `draft-grill + devils-advocate` *(v0.11.2 default)* — agent grills your paper; devils-advocate plays the reviewer who escalates each weakness
- `<any chain> + executive-summary` — parallel 3-bullet TL;DR for non-technical or deadline-pressed readers

## Cross-references

- Detailed contracts and composition rules: [`REFERENCE.md`](REFERENCE.md)
- Type A emitter index: [`../sub-skills/README.md`](../sub-skills/README.md)
- Orchestrator overview: [`../SKILL.md`](../SKILL.md)
- Architectural design: [`../../docs/skill-catalog-evolution-2026-04-30.md`](../../docs/skill-catalog-evolution-2026-04-30.md)
