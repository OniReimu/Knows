---
name: commentary-builder-prompt
version: 1.0
purpose: Canonical LLM prompt for the commentary-builder sub-skill. Locks in speculation banned phrases, reflection typology, grounding contract, anti-overreach rule, and JSON output schema at the prompt level — preventing the "could explore X, promising direction Y" failure mode that destroys trust in agent-generated commentary.
---

# Canonical LLM Prompt — commentary-builder

This document is the authoritative LLM prompt for the `commentary-builder` sub-skill (sibling at `../sub-skills/commentary-builder/SKILL.md`). The contract this prompt enforces operationalizes that skill's grounding contract as a runnable system + user message pair.

**Why this exists**: reader/agent reflection has the same fabrication failure mode as peer review — the model is tempted to fall back on plausible-sounding speculation ("could explore", "promising direction") when the paper does not provide enough material to ground a reflection. Without a frozen prompt, every agent driving this skill re-derives the typology and the grounding contract, silently inviting `next-step-advisor`-style fabrication tells into the corpus. The output of this skill feeds back into `next-step-advisor`'s evidence pool — if it isn't grounded, the rot compounds.

The 9-phrase banned list is deliberately shared with `next-step-advisor-prompt.md` (single canonical list). Any change here should also propagate there.

---

## How to use

1. The orchestrator runs the dispatch + retrieve pipeline (see `sub-skills/commentary-builder/SKILL.md` Quick Start §1-§3).
2. After fetching, the agent has `paper_sidecar` (full record for the paper being reflected on).
3. The agent calls its LLM with the **System** message below + the **User** template below populated with `{paper_block}` and `{human_brief}`.
4. The agent post-processes the LLM output through the **Banned-phrase check** (§5) and the **Grounding check** (§6), with one regenerate retry on failure.
5. The agent emits the `commentary@1` YAML sidecar, mapping JSON output → schema-valid YAML following the patterns in the SKILL.md.

---

## System message

```
You are an evidence-bound reader/agent reflector. Your job is to produce
non-adversarial reflections on a research paper, where every reflection
traces to a specific stmt:* or ev:* anchor in the paper's sidecar via a
`reflects_on` relation.

You are NOT a peer reviewer. You do NOT critique the paper. You produce
reflections that are USEFUL TO A FUTURE READER who is deciding whether
to extend, transfer, or revisit this work — the kind of margin notes a
careful researcher writes during a literature review pass.

You do NOT invent gaps. You do NOT fall back on "could explore" /
"promising direction" speculation. You acknowledge the paper's own
admitted limitations rather than re-presenting them as fresh
gap_spotted reflections.

Output ONLY a single JSON object matching the schema below. No prose
preamble, no markdown fences.

Schema:
{
  "paper_rid": "<echo of paper_rid verbatim, no normalization>",
  "summary": "<1-2 sentences neutrally summarizing the paper's contribution and what it leaves open>",
  "reflections": [
    {
      "stmt_id": "stmt:<descriptive-kebab-case>",
      "statement_type": "<one of: gap_spotted | scenario_extrapolation | method_transfer_idea | lesson>",
      "label": "<short title, ≤ 8 words>",
      "argument": "<2-4 sentences explaining the reflection — what the reader noticed and why it matters>",
      "anchored_to": [
        {
          "rid": "<paper_rid>",
          "anchor_id": "stmt:<id> | ev:<id>",
          "verbatim_quote": "<≤ 30-word substring of the cited anchor's text, embedded in the reflection's argument>"
        }
      ]
    }
    /* 3-6 reflections; mix typology patterns when material allows */
  ],
  "calibration": {
    "confidence": <int 1-5>,           /* 5 = strongly grounded, paper provides ample anchors; 1 = thin grounding, agent confidence low */
    "coverage_note": "<one sentence: what the reflection set covers and what it explicitly does NOT — e.g. 'gap analysis covers methodology and assumptions; deployment-cost angle deferred to a future commentary pass'>"
  }
}

REFLECTION TYPOLOGY (every reflection MUST pick one):

  - gap_spotted               : the reader notices an unaddressed assumption,
                                missing baseline, or untested condition the
                                paper does not disclose. Different from
                                limitation: the paper does NOT concede this
                                ground itself. Anti-overreach rule below
                                applies — verify the paper isn't already
                                conceding it.

  - scenario_extrapolation    : a new application scenario the paper enables
                                but does not address. Anchor must be a
                                method/claim that supports the
                                extrapolation, not just a vague
                                "this could be used for X" speculation.

  - method_transfer_idea      : the paper's method (or a component of it)
                                could be ported to a different domain/task.
                                Anchor must point to the specific method
                                statement being transferred, with reasoning
                                grounded in structural similarity not
                                surface analogy.

  - lesson                    : a reader-distilled take-away that holds
                                beyond the paper's scope. Differs from a
                                claim: a lesson is general guidance the
                                reader extracts, not a result the paper
                                proves. Use sparingly — at most 2 lessons
                                per commentary; over-using lessons is the
                                tell of a model that ran out of grounded
                                gap_spotted material.

Hard rules — violating any of these makes the output invalid:

1. Every reflection has at least one `anchored_to` entry referencing a
   real stmt:* or ev:* in the paper sidecar (or in a cited-corpus sidecar
   if one is supplied — but that is rare in the commentary-builder
   workflow; default to anchoring within the paper sidecar).

2. Every `verbatim_quote` is a substring (after whitespace normalization)
   of the anchored anchor's `text` field. The substring should also
   appear in the reflection's `argument` so a downstream consumer can
   verify without refetching.

3. The following 9 phrases are BANNED in `summary`, every
   `reflections[*].argument`, and `calibration.coverage_note` — they are
   speculation tells that signal the model is generating without
   grounding:

     "could explore"
     "might investigate"
     "promising direction"
     "future work could"
     "this opens up"
     "intriguing avenue"
     "underexplored"
     "ripe for"
     "ample opportunity"

   If a sentence contains any of these without a `[stmt:*/ev:* from <RID>]`
   citation in the same sentence, rewrite to either (a) name a specific
   anchor + the concrete extrapolation it supports, or (b) remove the
   sentence. This list is shared with next-step-advisor-prompt.md.

4. ANTI-OVERREACH: if the paper's own `limitation` or `question`
   statements already concede the candidate ground, do NOT present it as
   a `gap_spotted` reflection. Either (a) demote it to a `lesson` that
   summarizes what the paper concedes vs leaves untested, or (b) drop it.
   The paper having a limitation:"only tested on English" forecloses the
   gap_spotted:"only tested on English" reflection — that's just
   restating, not reflecting.

5. Reflection count is 3-6. Mix typology when material allows. If the
   paper is genuinely thin and you can only ground 3 reflections, return
   3 — do NOT pad with banned-phrase speculation. If you cannot ground
   3 reflections meaningfully, abstain by returning an empty
   `reflections` array AND a `calibration.coverage_note` explaining why
   (e.g. "paper has 4 statements, all conceded as limitation; no
   uncon­ceded ground for gap_spotted at this depth"). The orchestrator
   handles the abstain at the post-LLM check.

6. Tone: professional, specific, NOT speculative. The target reader is a
   future researcher using `next-step-advisor` to find research
   directions — they will weigh the reflection by the strength of its
   anchor, not its prose. Sharp specifics signal grounded engagement;
   speculative prose signals the opposite.

7. The `paper_rid` field echoes the input verbatim — no normalization.

8. At most 2 reflections of `statement_type: lesson`. Lessons that don't
   trace to a specific paper anchor risk drifting into platitudes; the
   typology cap prevents the slide.

CALIBRATION TIERS (confidence 1-5):

  5 = "I am confident the paper's anchors strongly support every
       reflection. I noticed multiple ungrounded gaps the paper itself
       does not concede."
  4 = "I am confident in most reflections. At least one is grounded
       indirectly (anchor supports the premise but not the specific
       extrapolation)."
  3 = "I am fairly confident. The paper has enough anchors but the
       reflections lean on inference rather than direct support."
  2 = "Thin grounding. The paper has limited claim/method density;
       reflections are reasonable but the trail back to anchors is
       short."
  1 = "Very thin grounding. The reflection set is more pattern-matched
       than paper-grounded; recommend deferring this commentary until a
       denser sidecar is available."
```

---

## User message template

```
Paper sidecar:

{paper_block}

Reflection brief from human:

{human_brief}

Produce the JSON object per the system message contract. Wrap any text
reproduced from the sidecar inside <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR>
tags per orchestrator guard G1.
```

The `{paper_block}` is the paper sidecar formatted as:

```
<UNTRUSTED_SIDECAR>
RID: knows:<author>/<title>/<version>
Title: <title>
Statements:
  - stmt:<id>: <text>  [type=<claim|method|limitation|question|assumption|...>]
  ...
Evidence:
  - ev:<id>: <text>  [page=<page>, anchor=<anchor>]
  ...
Relations (limited to those that constrain reflection — limitation/question/challenged_by):
  - <subject_ref> <predicate> <object_ref>
  ...
</UNTRUSTED_SIDECAR>
```

The `{human_brief}` is the human reader's brief: focus areas if any (e.g., "I'm looking for transfer ideas to chemistry"), persona if any, deadline context. Empty brief is acceptable — the agent produces general-purpose commentary.

---

## Banned-phrase check (post-LLM, agent-side)

Run this regex check against `summary`, every `reflections[*].argument`, and `calibration.coverage_note`:

```python
import re

SPECULATION_TELLS = [
    "could explore",
    "might investigate",
    "promising direction",
    "future work could",
    "this opens up",
    "intriguing avenue",
    "underexplored",
    "ripe for",
    "ample opportunity",
]

def speculation_violations(text: str) -> list[str]:
    """Return speculation phrases present in `text` that are NOT in a
    sentence containing a `[stmt:* from <RID>]` or `[ev:* from <RID>]` citation."""
    hits = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        lower = sentence.lower()
        for phrase in SPECULATION_TELLS:
            if phrase in lower:
                if not re.search(r"\[(?:stmt|ev):[^\]]+ from [^\]]+\]", sentence):
                    hits.append(phrase)
    return hits
```

If `speculation_violations()` returns a non-empty list → regenerate ONCE with the strict-mode prefix:

```
STRICT MODE: revise the following sentences to either name a specific
anchor (stmt:* or ev:*) AND the concrete extrapolation it supports, OR
remove the sentence. Speculation phrases are banned without grounding.
Phrases hit: {hits}.

Previous output:
{previous_json}
```

If the regenerated output also fails → abstain with `skill_runtime_exception.UngroundedReflection` per `commentary-builder/SKILL.md`.

---

## Grounding check (post-LLM, agent-side)

For each reflection in the regenerated (or first-pass) output, verify:

1. `anchored_to` is non-empty.
2. `anchored_to[*].rid` equals the paper RID (or, if a cited-corpus block was supplied, one of its RIDs).
3. `anchored_to[*].anchor_id` matches an actual `stmt:*` or `ev:*` in that sidecar.
4. `verbatim_quote` is a substring (after whitespace normalization) of the cited anchor's `text`.
5. `verbatim_quote` also appears as a substring of `reflection.argument` (so the citation embedding rule is honored).
6. `statement_type` ∈ {gap_spotted, scenario_extrapolation, method_transfer_idea, lesson}.
7. Count of `statement_type == "lesson"` ≤ 2.
8. Count of reflections ∈ [3, 6] OR == 0 (legitimate abstain).
9. Anti-overreach check: for each `gap_spotted` reflection, run substring-overlap (or Jaccard ≥ 0.4 on content tokens after stop-word removal) against every `limitation`/`question` statement in the paper. If any overlap, the reflection must either (a) be demoted to `lesson` summarizing the conceded ground, or (b) be dropped. The orchestrator runs this check post-LLM and either flags for regeneration or drops the offending reflection.

If `len(reflections) == 0` after dropping → the agent emits a manifest note `"no reflections survived anti-overreach filter — paper acknowledged or precluded all candidate gaps; recommend deferring commentary"`. This is a legitimate outcome, NOT a runtime error. The downstream `next-step-advisor` will see zero commentary signal for this paper and rely on paper@1's own question/limitation/reflection statements.

---

## YAML emission

The JSON output above is mapped to the `commentary@1` YAML sidecar as follows:

| JSON field | YAML location |
|---|---|
| `paper_rid` | recorded in commentary's `provenance.derived_from: ["<paper_rid>"]` |
| `summary` | top-level `summary` |
| `reflections[*].stmt_id` | `statements[*].id` |
| `reflections[*].statement_type` | `statements[*].statement_type` |
| `reflections[*].label` | NOT directly persisted — used as the human-readable title in the SKILL.md Quick Start UI; not a schema field |
| `reflections[*].argument` | `statements[*].text` (with the embedded verbatim_quote substring) |
| `reflections[*].anchored_to[0]` | `relations[*]` row with `predicate: reflects_on`, `subject_ref: stmt:<id>`, `object_ref: "<paper_rid>#<anchor_id>"` |
| `calibration.confidence` | embedded in `extensions.commentary_calibration.confidence` (since `confidence` at the record level isn't a schema field; per-statement `confidence` exists but the calibration is record-level) |
| `calibration.coverage_note` | top-level `summary` continuation OR `extensions.commentary_calibration.coverage_note` |

The commentary record's `subject_ref` is the LOCAL artifact entry that wraps the paper being reflected on — typically `art:reflected-paper`, with `artifact_type: paper`, `role: cited`, and identifiers pointing to the original paper. This keeps schema-validation cross-references working without forcing the commentary record to embed the paper's full identifier set.

### REQUIRED top-level fields for two-phase retrieval

Commentary records MUST set the following top-level fields so `next-step-advisor`'s Phase 2 keyword fallback (`/search?q=<source paper title>`) can rediscover them. The hub uses tsvector AND-logic, so every token of the source paper's title must appear somewhere in the commentary's Weight-A/B/C fields.

| Field | Required content | Why |
|---|---|---|
| `title` | Free — typically `"Reader commentary on <source short title>"` | Weight A in tsvector but typically does NOT carry the source's full title verbatim (the prefix word "Reader" leaks tokens). Don't rely on `title` alone. |
| `keywords` | MUST include (1) the source paper's full title VERBATIM as one entry, (2) the source's short name / project name if any, (3) `<last_author> et al. <year>` as a separate entry. Then add the commentary's own classifying terms. | Weight C, but enough tokens here that AND-tsquery on the source title resolves. |
| `coverage.statements` | MUST be `key_claims_and_limitations` (NOT `partial`) when 3-6 reflections cover the paper's key gap-bearing anchors | Without this, `next-step-advisor`'s G2' quality_policy filters the entire commentary set out before Phase 2 aggregation |
| `coverage.evidence` | `partial` is acceptable (commentary typically has empty `evidence: []`) | — |
| `subject_ref` artifact | A local `art:reflected-paper` (or similar) entry with `role: cited` AND `identifiers: {doi: ...}` or `{arxiv: ...}` pointing to the source | Provides DOI-grounded traceability when the search-token fallback is ambiguous |

Example keywords block from `examples/cs/resnet_commentary.knows.yaml`:

```yaml
keywords:
- Deep Residual Learning for Image Recognition   # source title VERBATIM
- ResNet                                          # source short name
- He et al. 2016                                  # source author + year
- residual learning                               # commentary classifier
- image recognition                               # commentary classifier
- agent commentary                                # commentary classifier
- gap analysis
- method transfer
```

This convention is load-bearing — without it, well-formed commentary records become invisible to the agent that's supposed to consume them.

---

## Consume mode (v0.11+) — when `brainstorm_summary` is supplied

This prompt is the SOLO MODE prompt — used when the agent brainstorms reflections from the paper sidecar alone.

When the user has gone through a `paper-brainstorm` (Type B stance) session first and the orchestrator dispatches with `(reflection_generate, {paper_rid, brainstorm_summary}, commentary_sidecar)`, the LLM is NOT invoked for substantive brainstorming. Instead the skill body does:

1. Validate brainstorm_summary against `schema: brainstorm-v1` (per `../stances/README.md`).
2. Refuse to emit if `status != ready`.
3. Verify each reflection's grounding: anchor exists in paper sidecar; verbatim_quote is a substring of anchor's text; user-confirmed.
4. Mechanically translate the structured summary to commentary@1 YAML — no LLM rewriting of arguments, no added/dropped reflections.
5. Set `provenance.workflow_chain` to the `emit_chain` from the summary.
6. Run lint + post-receipt grounding regex on `summary` text only (banned-phrase regex on argument text is skipped — the stance already enforced it during brainstorm).

Consume mode does NOT use this prompt. The full mechanical-translation logic lives in `../sub-skills/commentary-builder/SKILL.md` § "Consume mode". This prompt's contract still applies to consume mode for the top-level `summary` text generation only.

## Versioning

- `v1.0` — base prompt with 9-phrase banned list (shared with next-step-advisor + paper-brainstorm) + 4-pattern reflection typology + grounding contract + anti-overreach + calibration.
- `v1.1` (v0.11) — consume mode pointer added; existing v1.0 contract still governs solo mode end-to-end.

Any change to the banned-phrase list MUST propagate to `next-step-advisor-prompt.md` AND `../stances/paper-brainstorm/SKILL.md`. Any change to the typology MUST propagate to the schema (`knows-record-0.10.json` Statement.statement_type enum + commentary@1 conditional rule) AND to the brainstorm-v1 summary spec in `../stances/README.md`.
