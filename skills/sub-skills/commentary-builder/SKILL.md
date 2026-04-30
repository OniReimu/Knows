---
name: knows-commentary-builder
description: "Generate a `profile: commentary@1` sidecar capturing reader/agent reflections on a paper — gap_spotted, scenario_extrapolation, method_transfer_idea, lesson — anchored to the paper's stmt:* via `reflects_on` relations. Triggers: 'what gaps does this paper miss', 'where could this method transfer', 'reflect on this paper for me', 'find the unaddressed assumptions', 'agent reading note for paper X'. Different from `review-sidecar` (which produces critique-flavored peer review) — this captures non-adversarial reader reflection that academic papers typically self-censor under publication pressure."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: reflection_generate
required_inputs:
  - paper_rid                       # record_id of the paper@1 sidecar to reflect on
optional_inputs:
  - brainstorm_summary              # OPTIONAL fenced YAML block produced by the `paper-brainstorm` stance (Type B, v0.11+). When present, the skill switches to CONSUME MODE — it mechanically translates the structured summary to YAML rather than re-brainstorming. Schema: `brainstorm-v1` (see ../../stances/README.md § "Canonical brainstorm_summary format"). When absent, the skill runs in SOLO MODE (the v0.10 default — agent brainstorms reflections itself from the paper sidecar).

requested_artifacts:
  - commentary_sidecar              # YAML conforming to profile: commentary@1

# Profile contract — G7 (consumes paper@1)
accepts_profiles: [paper@1]

# Quality policy — G2' (need full claim/method structure to ground reflection meaningfully)
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (needs full record for relations + evidence to ground extrapolation)
requires_full_record: true

# REQUIRED — this skill emits a sidecar artifact (commentary@1)
emits_profile: commentary@1
---

# commentary-builder — Generate a reader/agent reflection sidecar

Produces a `profile: commentary@1` sidecar containing **non-adversarial reflections** on a paper: gap_spotted, scenario_extrapolation, method_transfer_idea, lesson — each anchored to the paper's `stmt:*` via `reflects_on` cross-record relations. Different from `review-sidecar`:

| Skill | Voice | Statement types | Relation predicate |
|---|---|---|---|
| `review-sidecar` | critique (peer review) | claim/limitation/method/question (review@1) + interpreted as weakness/strength via critique typology | `challenged_by` (adversarial) |
| `commentary-builder` | non-adversarial reader reflection | gap_spotted / scenario_extrapolation / method_transfer_idea / lesson (commentary@1) | `reflects_on` (associative) |

> **Why this exists**: Academic papers under publication pressure don't disclose honest gaps, lessons learned, or transferable insights — those get sanitized out. `next-step-advisor` running on author-stated `question`/`limitation` statements alone inherits this bias. `commentary-builder` lets a reader/agent record reflections that the author was either unwilling or unable to publish, so they enter the agent-consumable corpus and can ground future advisor briefs.
>
> **High-risk skill — banned-phrase enforcement is strict.** Without it, the output degrades into "could explore X, promising direction Y" speculation that damages user trust the same way reviewer clichés damage peer-review trust.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_sidecar, filter_records, Manifest, run_sidecar_author_postgen

# 1. Dispatch tuple: (reflection_generate, {paper_rid}, commentary_sidecar)
PAPER_RID = "knows:vaswani/attention/1.0.0"
decision = dispatch("reflection_generate", {"paper_rid": PAPER_RID}, "commentary_sidecar")
assert decision["action"] == "route"

# 2. G5: fetch full paper sidecar
manifest = Manifest(skill="commentary-builder", intent_class="reflection_generate",
                    dispatch_tuple="(reflection_generate,{paper_rid},commentary_sidecar)",
                    returned_rids=[PAPER_RID])
paper = fetch_sidecar(PAPER_RID)
manifest.fetch_mode_per_rid = {PAPER_RID: "full"}

# 3. G7 + G2'
kept = filter_records(
    [{**paper,
      "stats": {"stmt_count": len(paper.get("statements", []))},
      "coverage_statements": paper.get("coverage", {}).get("statements"),
      "lint_passed": True,
      "record_id": PAPER_RID}],
    "commentary-builder", manifest)
if not kept:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"})
    raise SystemExit

# 4. LLM call — use the canonical prompt from `../../references/commentary-builder-prompt.md`.
#    The prompt locks in:
#      - 9 banned speculation tells (shared with next-step-advisor):
#        "could explore" / "might investigate" / "promising direction" /
#        "future work could" / "this opens up" / "intriguing avenue" /
#        "underexplored" / "ripe for" / "ample opportunity"
#      - reflection typology (4 patterns matching the 4 statement_types)
#      - grounding contract: every commentary statement verbatim-quotes a
#        stmt:*/ev:* anchor in the paper sidecar (the thing it reflects_on)
#      - anti-overreach rule: don't restate what the paper already concedes
#      - JSON output schema, post-LLM check protocol with one regenerate retry
#    Do NOT re-derive these per agent — use the canonical prompt verbatim.

# 5. Save + post-gen pipeline (reuses sidecar-author's lint pipeline):
RAW = "/tmp/raw_commentary.yaml"
OUT = "/tmp/paper_commentary.knows.yaml"
# ... write your generated YAML to RAW ...
result = run_sidecar_author_postgen(RAW, OUT, include_cited=False)  # cited enrichment N/A for commentary
assert result["ready_to_publish"], result["lint_output"]
manifest.model = "claude-opus-4-7"
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets | Implementation |
|---|---|---|
| `commentary_sidecar` | `<paper>_commentary.knows.yaml` with `profile: commentary@1` | Read paper, apply commentary-builder-prompt.md grounding + typology, generate, lint, emit |

## Hard abstain rules

| Condition | `abstained_reason` |
|---|---|
| `paper_rid` missing | `missing_required_input.paper_rid` |
| Paper rid returns 404 | `rid_not_found.<rid>` |
| Paper fails G7 (e.g. user supplied a `commentary@1` rid by mistake) | `empty_working_set_after_profile_filter` |
| Paper fails G2' quality | `empty_working_set_after_quality_filter` |
| **< 3 statements** in the paper to anchor reflections to | `empty_working_set_after_quality_filter` (insufficient grounding evidence) |
| LLM tries to output > 6 candidate reflections | abort + retry; cap at 6 |
| LLM outputs a reflection without ≥1 `stmt:*` citation in `reflects_on` | abort + retry; if 2 retries fail → abstain `skill_runtime_exception.UngroundedReflection` |
| Generated commentary YAML fails lint after 3 retries | `skill_runtime_exception.LintFailureExceeded` |
| LLM call fails | `skill_runtime_exception.<class>` |

## Banned phrases (compile-time check, shared with next-step-advisor)

If the LLM output contains any of these without a `[stmt:* from <RID>]` citation in the same sentence, regenerate:

- "could explore" / "might investigate" / "promising direction"
- "future work could" / "this opens up" / "intriguing avenue"
- "underexplored" / "ripe for" / "ample opportunity"

These are the speculation tells. Either back the claim with a paper anchor or remove the sentence.

## Reflection typology (every commentary statement MUST pick one)

Each generated statement maps to one of 4 patterns:

| Pattern | statement_type | When to use | Example |
|---|---|---|---|
| **gap_spotted** | `gap_spotted` | Reader notices an unaddressed assumption, missing baseline, or untested condition the paper does not disclose. | "The paper assumes IID test data but the deployment scenario it motivates has covariate shift; this assumption is load-bearing for the headline ECE number but not measured." |
| **scenario_extrapolation** | `scenario_extrapolation` | A new application scenario the paper enables but does not address. | "The retrieval-augmentation method as described would allow private corpus indexing under DP, an application class not in the experiments." |
| **method_transfer_idea** | `method_transfer_idea` | The paper's method could be ported to a different domain/task. | "The cross-attention bottleneck used here is structurally identical to the one Barron 2022 used for graph-pooling; transferring the gating term should compose." |
| **lesson** | `lesson` | A reader-distilled take-away that holds beyond the paper's scope. | "Dense ablation tables are dominated by the strongest single baseline; adding a 5th seed before adding a 4th method tends to be the higher-information move." |

## Grounding contract

Every commentary statement MUST:

1. Have a corresponding `relation` with `predicate: reflects_on`, `subject_ref` pointing to the commentary statement's local `stmt:*` ID, and `object_ref` cross-record into the paper's RID + `#stmt:<id>` (e.g. `"knows:vaswani/attention/1.0.0#stmt:positional-encoding-claim"`).
2. Embed a `verbatim_quote` substring (≤ 30 words after whitespace normalization) of the anchored paper statement's `text` field, surfaced inside the commentary statement's `text` so a downstream consumer can verify the anchor without refetching the paper.
3. Anti-overreach: if the paper's own `limitation` or `question` statements already concede the same ground, demote the reflection to either (a) a `lesson` summarizing what the paper concedes vs leaves untested, or (b) drop the reflection entirely. Never re-present author-acknowledged limitations as fresh `gap_spotted` reflections — that's the same anti-trust tell as a peer reviewer rehashing limitations the paper already lists.

## Manifest emission (G6)

Per G6: `skill: commentary-builder`, `intent_class: reflection_generate`, `dispatch_tuple`, `returned_rids: [paper_rid]`, `applied_profile_filters: [paper@1]`, `fetch_mode_per_rid: {paper_rid: "full"}`, `model`, `emits_profile: commentary@1`. Output sidecar's `provenance.method = "manual_curation"` (it's curation of the reading experience, not extraction from the paper).

The output sidecar's `provenance.actor` records the agent identity (e.g., `{name: "claude-opus-4-7", type: "tool"}`) so consumers downstream of `next-step-advisor` can weigh agent-generated commentary differently from human reading notes.

## Cross-record relation conventions

Commentary statements anchor to paper claims via cross-record `reflects_on` predicates:

```yaml
relations:
  - id: rel:gap-spotted-1-reflects-paper-claim
    subject_ref: stmt:gap-iid-assumption                                  # local to commentary sidecar
    predicate: reflects_on                                                 # NEW IN 0.10
    object_ref: "knows:vaswani/attention/1.0.0#stmt:positional-encoding-claim"   # cross-record
```

This makes the commentary sidecar **bound** to a specific version of the paper sidecar via record_id chain. If the paper's record_id bumps (replaces edge), the commentary's cross-refs may need re-binding (handled by `version-inspector` v1.2).

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A)

When invoked downstream of the `paper-brainstorm` stance (Type B), commentary-builder receives a `brainstorm_summary` input alongside `paper_rid`. The skill switches from SOLO MODE (v0.10 default — brainstorm + emit) to CONSUME MODE (mechanical translation only).

### CONSUME MODE flow

```python
# Frontmatter validates brainstorm_summary structure before skill body runs.
# Inside the body, after G7 + G2' filters land kept_paper:
if brainstorm_summary is None:
    # SOLO MODE — current v0.10 path. Brainstorm 3-6 reflections per Quick Start §4.
    ...
else:
    # CONSUME MODE — fail-closed verification, then mechanical translation.
    summary = parse_brainstorm_summary(brainstorm_summary)  # validates schema: brainstorm-v1
    if summary["status"] == "abandon":
        manifest.abstained = True
        manifest.abstained_reason = "brainstorm_abandoned"
        raise SystemExit
    if summary["status"] == "needs_rework":
        # Pass control back to the stance — do NOT emit.
        return {"action": "return_to_stance", "rework_needed": summary["rework_needed"],
                "reason": "brainstorm_summary status is needs_rework"}
    assert summary["status"] == "ready"
    # Slot-type validation: ensure this brainstorm_summary was actually authored
    # for THIS emitter. A summary produced by a different stance/emitter pair
    # (e.g., review-prep → review-sidecar) must NOT reach commentary-builder's
    # translation. Same gate that review-sidecar/sidecar-author/rebuttal-builder/
    # survey-narrative/survey-table all enforce.
    if summary["emit_chain"][-1] != "commentary-builder":
        manifest.abstained = True
        manifest.abstained_reason = "invalid_slot_type.brainstorm_summary"
        raise SystemExit
    assert summary["emit_chain"][-1] == "commentary-builder"

    # Verify each reflection's grounding ourselves (don't trust the stance unilaterally):
    rework_needed = []
    for i, refl in enumerate(summary["reflections"]):
        anchor_id = refl["proposed_anchor"]["anchor_id"]
        verbatim = refl["proposed_anchor"]["verbatim_quote"]
        # Look up the anchor in the paper sidecar
        anchor = next((s for s in kept_paper["statements"] if s["id"] == anchor_id), None)
        if anchor is None:
            rework_needed.append({"index": i, "reason": f"anchor_id {anchor_id} not in paper"})
            continue
        # Whitespace-normalized substring check
        if normalize(verbatim) not in normalize(anchor["text"]):
            rework_needed.append({"index": i, "reason": f"verbatim_quote not substring of anchor text"})
            continue
        # Check user confirmed it (decision must be keep or refine, not drop)
        conf = next((c for c in summary["human_confirmations"] if c["reflection_index"] == i), None)
        if conf is None or conf["decision"] == "drop":
            rework_needed.append({"index": i, "reason": "user did not confirm (no keep/refine decision)"})

    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed,
                "reason": "post-receipt grounding verification failed"}

    # All checks pass — mechanical translation. NO LLM rewriting of arguments,
    # NO new reflections added, NO existing reflections dropped.
    yaml_record = translate_summary_to_commentary_yaml(summary, kept_paper)
    # CONSUME MODE outputs MUST set $schema to 0.10 — workflow_chain is a first-class
    # field on Provenance only in 0.10. Emitting with $schema=0.9 forces workflow_chain
    # into provenance.x_extensions, weakening the version contract.
    yaml_record["$schema"] = "https://knows.dev/schema/record-0.10.json"
    yaml_record["knows_version"] = "0.10.0"
    yaml_record["provenance"]["workflow_chain"] = summary["emit_chain"]   # ["paper-brainstorm", "commentary-builder"]
    yaml_record["provenance"]["method"] = "manual_curation"               # human-confirmed reflections
    # Provenance.actor lists the stance's actor first, then commentary-builder's:
    # [{name: "claude-...", type: "tool"}, {name: "commentary-builder", type: "tool"}]
    # If the stance dialogue had a human author, that record is added by the stance, not here.
```

### Why CONSUME MODE doesn't re-brainstorm

The grounding contract (every reflection traces to a real `stmt:*` + verbatim_quote) is the load-bearing trust property of `commentary@1`. If commentary-builder re-brainstorms in consume mode, it can introduce reflections the user never confirmed and cannot anchor honestly. Consume mode keeps the LLM out of the substantive loop — it only does YAML mechanics + post-receipt grounding verification. The stance did the substantive work.

### Source anchors are NOT used in consume mode (load-bearing)

The commentary@1 record's `statements[*]` MUST NOT carry `source_anchors`. Schema check: `source_anchors[*].representation_ref` must resolve to a `rep:*` in the SAME record's `artifacts[*].representations` — but the source paper's representations (e.g. `rep:paper-pdf`) live in the paper@1 record, not in this commentary record. Including them triggers a hard lint failure (`anchor representation_ref 'rep:paper-pdf' not found`).

Grounding in consume mode lives ENTIRELY in the cross-record `reflects_on` relations: subject_ref is the local commentary statement, object_ref is `<paper_rid>#<anchor_id>`. The `verbatim_quote` substring is embedded in the statement's `text` field for inline-readability, not in `source_anchors`.

The commentary record's `evidence: []` is also empty — commentary records never carry standalone evidence rows, only references to paper-side anchors via `reflects_on`.

This was caught by fresh-agent E2E tests (Test 1 / Test 4 / Test 8 across v0.10–v0.11.2) where Sonnet defaulted to copying paper-side representation_ref into source_anchors — runs that did this hit the lint error and recovered by removing source_anchors entirely. The fix lives in this contract, not in agent improvisation.

### `provenance.workflow_chain` (REQUIRED in consume mode)

The output sidecar's `provenance.workflow_chain` MUST be set to the `emit_chain` from the brainstorm_summary (typically `["paper-brainstorm", "commentary-builder"]`). Solo-mode records do NOT set workflow_chain (its absence indicates solo origin). Hub consumers use this to weigh epistemic provenance — chained records carry user-confirmed grounding, solo records are single-LLM output.

### Banned phrases in consume mode

Skip the post-LLM banned-phrase regex check in consume mode — the stance's `paper-brainstorm/SKILL.md` already enforces the same 9-phrase list during brainstorm, and consume mode does no LLM rewriting that could re-introduce the phrases. Run the regex only on `summary` text (the top-level commentary record summary, derived from but not identical to the brainstorm).

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` field is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| brainstorm_summary `status` is `needs_rework` (pass control back to stance) | NOT abstain — return `action: return_to_stance` instead |
| post-receipt grounding verification fails on any reflection | `action: return_to_stance` with `rework_needed` populated |
| brainstorm_summary `emit_chain` does NOT end with `commentary-builder` | `invalid_slot_type.brainstorm_summary` (chain misrouted) |

## Out of scope (v1.0)

- Multi-paper commentary (e.g. "compare papers A and B and reflect on the joint gap") — single paper only. Use `paper-compare` first, then commentary-builder on each.
- Commentary on a `review@1` sidecar — review records are critique, not subjects of reflection. Reflect on the underlying `paper@1` instead.
- Auto-classification of which of the 4 typology patterns applies — the LLM picks via the canonical prompt; no separate classifier.
- Persona-conditioned commentary (e.g., "reflect as a security researcher") — skill produces general-purpose commentary; persona conditioning is left to the caller's prompt prefix.

## Profile-conditioned validation note

`commentary@1` admits ONLY the 4 statement types listed above. The 0.10 schema enforces this via top-level `allOf` rules (see `../../references/knows-record-0.10.json`). A commentary record carrying `claim` or `limitation` will fail lint at the schema layer — by design, so reader reflections cannot pose as author-stated content. This addresses the codex-review Issue 1 finding (per-profile enum partition).

## Coverage convention (load-bearing — required for downstream consumability)

Commentary records that ship 3-6 reflections covering the key gap-bearing anchors of a paper MUST set:

```yaml
coverage:
  statements: key_claims_and_limitations
  evidence: partial
```

**Why `key_claims_and_limitations` and NOT `partial`**: `next-step-advisor`'s G2' quality_policy whitelists `[exhaustive, main_claims_only, key_claims_and_limitations]` and excludes `partial` because partial coverage is exactly where speculative synthesis creeps in. If commentary records are honestly labeled `partial`, the orchestrator drops the entire commentary set BEFORE Phase 2 — silently collapsing the v0.10 expansion back to paper@1-only. The semantic interpretation is correct: 3-6 reflections that anchor to all the paper's key claims and limitations IS `key_claims_and_limitations` coverage from the reader's perspective, even though the commentary is sparse relative to a hypothetical exhaustive reflection set. Use `partial` ONLY for draft/exploratory commentary that the author does not want next-step-advisor to consume.

Evidence stays `partial` because commentary records typically have an empty `evidence: []` array — the grounding is in cross-record `reflects_on` relations, not in local evidence rows.

## Source-paper-title persistence (required for two-phase retrieval)

Because hub `/search` does not currently support cross-profile relation-typed filtering (see `../../references/api-schema.md` v0.10 prerequisite), `next-step-advisor`'s Phase 2 retrieves commentary records by keyword-searching `/search?q=<source paper title>`. The hub uses tsvector AND-logic across query tokens, so EVERY token of the source paper's title MUST appear in some Weight-A/B/C field of the commentary record (`title` / `keywords` / `summary` / `discipline` / `author`).

**Convention**: the commentary builder MUST persist the source paper's full title VERBATIM as a `keywords` entry. Optionally also include the source's last-author surname + year as a separate keyword. The shipped `examples/cs/resnet_commentary.knows.yaml` demonstrates this — `keywords` includes `"Deep Residual Learning for Image Recognition"` (the source title) AND `"ResNet"` (the source's common short name) AND `"He et al. 2016"` (author + year), so a `/search?q=<source title>` query reliably surfaces the commentary.

Without this convention, the two-phase fallback fails on real commentary records whose own `title` would otherwise be something like "Reader commentary on X" — semantically correct but tsvector-invisible to the source paper's title query.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4 | [`../../references/commentary-builder-prompt.md`](../../references/commentary-builder-prompt.md) | [`../next-step-advisor/SKILL.md`](../next-step-advisor/SKILL.md) (downstream consumer of commentary@1)
