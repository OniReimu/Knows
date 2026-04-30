# Stances — Reference (v0.11.2)

This document covers everything **stance authors and chain implementers** need: handoff schema, composition rules, frontmatter conventions, contract details. The user-facing index is in [`README.md`](README.md) — read that first if you're trying to pick a stance to invoke.

## How a stance hands off to its paired emitter

The stance does free dialogue. When convergence is reached, the stance MUST emit a fenced `brainstorm_summary` block. The paired emitter consumes the summary and refuses to emit if `status != ready`. This preserves the emitter's grounding contract — the emitter trusts the structured summary, not the conversation.

### Canonical `brainstorm_summary` format

````markdown
```yaml
brainstorm_summary:
  schema: brainstorm-v1
  emit_chain: [<stance-name>, <emitter-name>]
  paper_rid: knows:examples/<paper>/<version>     # or other Type A primary input
  status: ready                                    # ready | needs_rework | abandon
  reflections:                                     # or weaknesses / pitches / shape_decisions etc.
    - typology: gap_spotted                        # one of the emitter's admissible types
      label: "<short title, ≤8 words>"
      argument: "<2-4 sentences>"
      proposed_anchor:
        rid: knows:examples/<paper>/<version>
        anchor_id: stmt:<id>                       # MUST exist in the paper sidecar
        verbatim_quote: "<≤30 words substring of anchor's text>"
      grounded: true                               # MUST be true for status: ready
  human_confirmations:
    - reflection_index: 0
      decision: keep                               # keep | refine | drop
  rework_needed: []                                # populate ONLY when status: needs_rework
```
````

### Fail-closed semantics

If ANY of these conditions hold, the stance MUST set `status: needs_rework` and populate `rework_needed`:

- A reflection has `grounded: false`
- A `proposed_anchor.anchor_id` does not exist in the source artifact
- A `verbatim_quote` is not a substring (after whitespace normalization) of the anchored text
- The user did not explicitly confirm at least one reflection (no decision: keep / refine present)

When the emitter sees `status: needs_rework`, it refuses to emit and reports back to the stance with the reasons. The stance runs another conversational round with the user. When the user explicitly abandons the chain, the stance sets `status: abandon` and the emitter cleanly closes without producing an artifact.

### Output `$schema` — MUST be 0.10 (load-bearing)

Emitters that produce sidecar artifacts (commentary-builder, review-sidecar, sidecar-author) in CONSUME MODE MUST set the output's `$schema` to `https://knows.dev/schema/record-0.10.json` and `knows_version` to `0.10.0`. Reason: `provenance.workflow_chain` is a first-class field on Provenance only in 0.10. If the output declares `$schema: record-0.9.json`, schema validation either rejects `workflow_chain` or forces it into `provenance.x_extensions`, weakening the version contract that downstream hub consumers rely on to distinguish chain-derived from solo-mode artifacts.

The fact that the SOURCE artifact (the paper@1 sidecar being reviewed/reflected on) is on 0.9 does NOT propagate to the output — the output is a NEW artifact and bumps to whatever schema gives it the fields it needs. This is a common point of confusion in fresh-agent runs; the consume-mode segments in each emitter's SKILL.md repeat this explicitly.

Emitters that produce non-sidecar artifacts (rebuttal-builder → markdown rebuttal_doc, survey-narrative → markdown paragraph, survey-table → markdown+latex table) record `workflow_chain` in the run manifest (a JSON sidecar to the artifact, not subject to KnowsRecord schema). For those emitters, no `$schema` choice is required at the artifact level.

## Stance frontmatter convention

Type B SKILL.md files use ONLY two frontmatter fields:

```yaml
---
name: <stance-name>
description: <one paragraph: trigger phrases + what posture this enables + when NOT to use>
---
```

No `intent_class`, no `accepts_profiles`, no `quality_policy`, no `emits_profile`. Stance auto-activation is purely description-matching by Claude Code's standard skill discovery.

The body is direct instructional prose — typically 5-50 lines, mattpocock convention. Add structure (Persistence rules, Examples, Auto-Clarity Exception) only when actually load-bearing. Length by need, not by template.

## How to add a new stance

1. Create `<stance-name>/SKILL.md` here.
2. Frontmatter: `name` + `description` only. Description must include trigger phrases AND the negative case ("do NOT use when ...").
3. Body: define the posture in instructional prose. If pairing with a Type A emitter, document the chain handoff explicitly (which emitter, what brainstorm_summary fields).
4. Update the stance index table in [`README.md`](README.md).
5. If the stance pairs with an emitter, the EMITTER's SKILL.md MAY add a brief reference to the paired stance under "Related" — but the emitter's contract MUST stay 100% functional standalone (a user who skips the brainstorm can still call the emitter directly).

## Hard rules for stance authors

- A stance NEVER produces a schema-validated artifact directly. If it needs to, it's a Type A skill — put it under `../sub-skills/`.
- A stance MUST NOT bypass its paired emitter's grounding contract by writing the artifact YAML itself. Always go through the emitter via `brainstorm_summary` handoff.
- A stance SHOULD respect the activation precedence rule (see [`README.md`](README.md)) — describe trigger phrases that match exploratory intent, not artifact-request intent.
- A stance MAY remain active across multiple turns (like `caveman` in mattpocock's catalog). If so, document the persistence + exit conditions explicitly in the SKILL.md body.

## Stance composition rules

mattpocock's `caveman` showed that a stance can stay active across turns and compose with whatever else is happening. Knows v0.11.x has paired stances and standalone stances. Composition needs to be predictable, not lottery. The rules below make it so.

### Three roles in a composed session

At any moment, a session has at most three concurrent layers:

1. **Host stance** — the task-bound stance that owns the workflow toward an emitter handoff. Examples: `paper-brainstorm`, `review-prep`, `draft-grill`, `pitch-grill`, `survey-shape`, `rebuttal-prep`. AT MOST ONE host stance is active at a time. (You don't review-prep and pitch-grill simultaneously — they target different emitters with incompatible brainstorm_summary schemas.)
2. **Standalone stance(s)** — postural overlays that do not chain to an emitter on their own. Examples: `devils-advocate`, `executive-summary`, `socratic`, `red-team`. UP TO THREE standalone stances can stack on top of a host (or run alone), but composition gets noisy past two — **respect the cap of 2 in routine use**.
3. **Caveman/format overrides** — output-format stances (currently only `caveman` from mattpocock would be one if Knows imported it). These adjust HOW the output reads but not what it says.

The host owns handoff format (the brainstorm_summary block). Standalone stances modify what enters that block but cannot change its schema.

### Conflict resolution between stances

When two stances have conflicting tendencies, use this precedence:

| Tendency | Winner | Rationale |
|---|---|---|
| Host stance wants to enumerate; `socratic` wants to ask back | **socratic** wins on conversational moves; host wins on the brainstorm_summary structure | The dialogue style adjusts; the artifact contract doesn't |
| `devils-advocate` says "drop this candidate"; host stance has user-confirmed it | **host** wins | User confirmation is contract-level; devil's-advocate is exploration |
| `red-team` surfaces 5 attack vectors; host has typology cap (e.g., 6 reflections in paper-brainstorm) | **host cap** wins | Capacity limits exist for cognitive reasons; ignore would defeat them |
| `executive-summary` wants 3 bullets; host wants full transcript | **both** — executive-summary produces a parallel deliverable, NOT a replacement of the host's normal output | Documented in executive-summary/SKILL.md "Composes with other stances" |
| Standalone A says X is critical; standalone B says X is fine | User adjudicates explicitly — neither standalone wins by default | Standalones are exploration aids, not authorities |

### Empirical compose recipes (validated patterns)

These are the patterns we've built and / or fresh-agent-tested:

- **`paper-brainstorm + devils-advocate`** — for each candidate gap_spotted, also argue why it's NOT a gap. Sharpens anti-overreach.
- **`paper-brainstorm + red-team`** — for each candidate gap, map the deployment failure mode it implies.
- **`paper-brainstorm + socratic`** — replace agent-led enumeration with user-led discovery. Validated in fresh-agent Test 8 — works under pressure.
- **`review-prep + devils-advocate`** — for each candidate weakness, also propose the rebuttal authors would make. Helps the user pre-empt counter-arguments. Validated in Test 7.
- **`review-prep + red-team`** — for each candidate weakness, map the system failure it implies.
- **`draft-grill + devils-advocate`** — DEFAULT compose recipe for draft-grill. devils-advocate proposes the strongest reviewer counter-attack to your planned revision, so you can fix BEFORE submission.
- **`pitch-grill + socratic`** — exposes whether the user has done the literature review or is bluffing.
- **`pitch-grill + red-team`** — after originality/feasibility/scope, hit deployment failure modes hard.
- **`rebuttal-prep + devils-advocate`** — for each comment, anticipate the reviewer's counter-rebuttal in revision round. Validated in Test 9 (with red-team dropped per cap).
- **`<any chain> + executive-summary`** — after the chain produces an artifact, compress to 3 bullets. Parallel deliverable.
- **`<any host> + socratic`** — Q-A-Q-A dialogue, structured fields populated by user answers.

### Rules for stance authors (composition)

When writing a new stance:

1. **Declare composability**. Top of SKILL.md should say either "Standalone — composes with X / Y" or "Task-bound — pairs with Z emitter". Don't be vague.
2. **Define exit conditions explicitly**. "Stays active until X" tells the orchestrator when this stance leaves the layer. Without this, stacks accumulate.
3. **Don't override host's handoff schema**. If you're a standalone, you contribute thoughts; the host stance writes brainstorm_summary. If you need to write artifacts, you're a host — put the SKILL.md under sub-skills/.
4. **Document at least one valid compose recipe** in the stance's body. If you can't think of one, the stance is probably orphaned in the catalog.

### Activation precedence + composition

Activation precedence (Q5) is documented in [`README.md`](README.md). For STACKED Type B stances (host + standalone), the user activating the second one does NOT deactivate the first. Standalones layer; they do not replace.

## Cross-references

- User-facing index: [`README.md`](README.md)
- Architectural design: [`../../docs/skill-catalog-evolution-2026-04-30.md`](../../docs/skill-catalog-evolution-2026-04-30.md)
- Type A index: [`../sub-skills/README.md`](../sub-skills/README.md)
- Orchestrator overview: [`../SKILL.md`](../SKILL.md)
- Dispatch contract (Type A only): [`../references/dispatch-and-profile.md`](../references/dispatch-and-profile.md)
