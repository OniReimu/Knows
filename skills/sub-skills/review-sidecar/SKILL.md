---
name: knows-review-sidecar
description: "Generate a structured peer review of a paper as a `profile: review@1` sidecar — weakness and strength statements, each linked back to specific claims in the original paper via `challenged_by` relations. Triggers: 'write a peer review of this paper', 'find the weaknesses in paper X', 'critique this paper as a reviewer would', 'generate a review sidecar', 'do a structured reviewer-style critique'. Use this when the user wants to PRODUCE a review; use sidecar-reader when they want to ANSWER a question about an existing paper."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: critique_generate
required_inputs:
  - paper_rid                       # record_id of the paper@1 sidecar to review
optional_inputs:
  - brainstorm_summary              # OPTIONAL fenced YAML block produced by the `review-prep` stance (Type B, v0.11+). When present, the skill switches to CONSUME MODE — mechanical translation of the structured weaknesses/strengths/questions into review@1 YAML, NOT a re-brainstorm. Schema: `brainstorm-v1` (see ../../stances/README.md). When absent, the skill runs in SOLO MODE (the v0.10 default — agent generates the review itself per Quick Start §4).

requested_artifacts:
  - review_sidecar                  # YAML conforming to profile: review@1

# Profile contract — G7 (consumes paper@1)
accepts_profiles: [paper@1]

# Quality policy — G2' (review needs full claim/evidence structure to critique meaningfully)
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (needs full record: relations + evidence to ground critique)
requires_full_record: true

# REQUIRED — this is the canonical sidecar-emitting skill of the catalog
emits_profile: review@1
---

# review-sidecar — Generate a structured peer review

Produces a `profile: review@1` sidecar containing weakness/strength statements anchored to the original paper's claims via `challenged_by` cross-record relations. Different from `rebuttal-builder` (which **responds** to reviewer comments) — this **generates** them.

> **Reference**: `../../references/review-mode.md` is the canonical workflow + 13 example reviews live under `../../examples/*/`.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import fetch_sidecar, filter_records, Manifest, dispatch
import yaml, time, hashlib

# 1. Dispatch tuple: (critique_generate, {paper_rid: rid}, review_sidecar)
PAPER_RID = "knows:vaswani/attention/1.0.0"
decision = dispatch("critique_generate", {"paper_rid": PAPER_RID}, "review_sidecar")
assert decision["action"] == "route"

# 2. G5: fetch full paper sidecar
manifest = Manifest(skill="review-sidecar", intent_class="critique_generate",
                    dispatch_tuple="(critique_generate,{paper_rid},review_sidecar)",
                    returned_rids=[PAPER_RID])
paper = fetch_sidecar(PAPER_RID)
manifest.fetch_mode_per_rid = {PAPER_RID: "full"}

# 3. G7 + G2'
kept = filter_records([{**paper, "stats":{"stmt_count":len(paper.get("statements",[]))},
                        "coverage_statements":paper.get("coverage",{}).get("statements"),
                        "lint_passed":True, "record_id":PAPER_RID}], "review-sidecar", manifest)
if not kept:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 4. LLM call — use the canonical prompt from `../../references/review-sidecar-prompt.md`.
#    The prompt locks in: 13 banned reviewer-clichés ("the experiments are insufficient",
#    "more analysis would be helpful", etc.), critique-typology ladder (7 named patterns:
#    claim-evidence-mismatch, load-bearing-assumption, unmeasured-cost,
#    unjustified-hyperparameter, scope-overclaim, ablation-gap, baseline-conflation),
#    grounding contract (every weakness verbatim-quotes a stmt:*/ev:* anchor),
#    anti-overreach rule (don't re-present limitations the paper already acknowledges),
#    OpenReview Markdown rendering, and 1-5 confidence calibration tiers.
#    Do NOT re-derive these per agent — use the canonical prompt verbatim.
#    Run the post-LLM banned-phrase + grounding + anti-overreach checks (one regenerate retry).
#    Produces a profile: review@1 sidecar with:
#    - statements[] — strength + weakness statements (one per JSON entry)
#    - relations[] — challenged_by edges (one per weakness, cross-record into paper's stmt:*)
#    - emits_profile: review@1 (this skill's frontmatter — must match record.profile)
#    PLUS: render the OpenReview-paste-able Markdown view per the prompt template's §7.

# 5. Save + post-gen pipeline (reuses sidecar-author's pipeline):
RAW = "/tmp/raw_review.yaml"; OUT = "/tmp/paper_review.knows.yaml"
# ... write your generated YAML to RAW ...
from orchestrator import run_sidecar_author_postgen
result = run_sidecar_author_postgen(RAW, OUT, include_cited=False)  # cited enrichment N/A for reviews
assert result["ready_to_publish"], result["lint_output"]
manifest.model = "claude-opus-4-7"
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets | Implementation |
|---|---|---|
| `review_sidecar` | `<paper>_review.knows.yaml` with `profile: review@1` | Read paper, apply review-mode.md prompt + examples, generate, lint, emit |

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `paper_rid` missing | `missing_required_input.paper_rid` |
| Paper rid returns 404 | `rid_not_found.<rid>` |
| Paper fails G7 (e.g. user supplied a `review@1` rid by mistake) | `empty_working_set_after_profile_filter` |
| Paper fails G2' quality | `empty_working_set_after_quality_filter` |
| Generated review YAML fails lint after 3 retries | `skill_runtime_exception.LintFailureExceeded` |
| LLM call fails | `skill_runtime_exception.<class>` |

## Manifest emission (G6)

Per G6: `skill: review-sidecar`, `intent_class: critique_generate`, `dispatch_tuple`, `returned_rids: [paper_rid]`, `applied_profile_filters: [paper@1]`, `fetch_mode_per_rid: {paper_rid: "full"}`, `model`, `emits_profile: review@1`. Output sidecar's `provenance.method = "manual_curation"` (it's curation of the paper into a review, not extraction).

## Cross-record relation conventions

Review statements reference paper claims via fully-qualified IDs in `object_ref`:

```yaml
relations:
  - id: rel:weakness-1-challenges-paper-claim
    subject_ref: stmt:weakness-1                                # local to review sidecar
    predicate: challenged_by
    object_ref: "knows:vaswani/attention/1.0.0#stmt:positional-encoding-claim"  # cross-record
```

This makes the review sidecar **bound** to a specific version of the paper sidecar via record_id chain. If the paper's record_id bumps (replaces edge), the review's cross-refs may need re-binding (handled by `version-inspector` v1.2).

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A)

When invoked downstream of the `review-prep` stance (Type B), review-sidecar receives a `brainstorm_summary` input alongside `paper_rid`. The skill switches from SOLO MODE (v0.10 default — agent generates the full review) to CONSUME MODE (mechanical translation only — no re-brainstorm, no rewriting of arguments).

### Why CONSUME MODE matters here (v0.11 lesson)

Test 5 of the v0.11 fresh-agent validation gate showed that without a formal consume-mode contract, an improvising agent silently substituted a mid-brainstorm weakness for the user-confirmed final weakness — the YAML lint passed but the artifact carried the wrong content. Consume mode is the contract that prevents this: the emitter trusts the structured summary, not the conversation.

### CONSUME MODE flow

```python
# Frontmatter validates brainstorm_summary structure before skill body runs.
# Inside the body, after G7 + G2' filters land kept_paper:
if brainstorm_summary is None:
    # SOLO MODE — current v0.10 path. Generate review per Quick Start §4 + review-sidecar-prompt.md.
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
    assert summary["emit_chain"][-1] == "review-sidecar"  # chain must terminate here

    # Verify each weakness/strength's grounding (don't trust the stance unilaterally):
    rework_needed = []
    for collection_name in ("weaknesses", "strengths"):
        for i, item in enumerate(summary.get(collection_name, [])):
            anchor_id = item["proposed_anchor"]["anchor_id"]
            verbatim = item["proposed_anchor"]["verbatim_quote"]
            anchor = next((s for s in kept_paper["statements"] if s["id"] == anchor_id), None)
            if anchor is None:
                rework_needed.append({"collection": collection_name, "index": i,
                                      "reason": f"anchor_id {anchor_id} not in paper"})
                continue
            if normalize(verbatim) not in normalize(anchor["text"]):
                rework_needed.append({"collection": collection_name, "index": i,
                                      "reason": "verbatim_quote not substring of anchor text"})
                continue
            # Per-collection user-confirmation check
            conf = next((c for c in summary["human_confirmations"]
                         if c.get("collection") == collection_name and c.get("index") == i), None)
            if conf is None or conf.get("decision") == "drop":
                rework_needed.append({"collection": collection_name, "index": i,
                                      "reason": "user did not confirm (no keep/refine decision)"})

    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed,
                "reason": "post-receipt grounding verification failed"}

    # All checks pass — mechanical translation. NO new weaknesses/strengths added,
    # NO existing items dropped, NO LLM rewriting of arguments.
    yaml_record = translate_summary_to_review_yaml(summary, kept_paper)
    # CONSUME MODE outputs MUST set $schema to 0.10 — workflow_chain is a first-class
    # field on Provenance only in 0.10. Emitting with $schema=0.9 would force you to
    # stuff workflow_chain into provenance.x_extensions, weakening the version contract.
    # The fact that the SOURCE paper sidecar is on 0.9 does NOT propagate — review records
    # are NEW artifacts and bump to whatever schema gives them their needed fields.
    yaml_record["$schema"] = "https://knows.dev/schema/record-0.10.json"
    yaml_record["knows_version"] = "0.10.0"
    yaml_record["provenance"]["workflow_chain"] = summary["emit_chain"]   # ["review-prep", "review-sidecar"]
    yaml_record["provenance"]["method"] = "manual_curation"               # human-confirmed weaknesses/strengths
    # Calibration (confidence 1-5, recommendation) and questions go into extensions.review:
    yaml_record["extensions"]["review"] = {
        "calibration": summary["calibration"],
        "questions": summary["questions"],
    }
```

### Source anchors are NOT used in consume mode (load-bearing)

The review@1 record's `statements[*]` MUST NOT carry `source_anchors`. Schema check: `source_anchors[*].representation_ref` must resolve to a `rep:*` in the SAME record's `artifacts[*].representations` — but the source paper's representations (e.g. `rep:paper-pdf`) live in the paper@1 record, not in this review record. Including them triggers a hard lint failure (`anchor representation_ref 'rep:paper-pdf' not found`).

Grounding in consume mode lives ENTIRELY in the cross-record `challenged_by` / `supported_by` relations: subject_ref is the local review statement, object_ref is `<paper_rid>#<anchor_id>`. The `verbatim_quote` substring is embedded in the statement's `text` field for inline-readability, not in `source_anchors`.

This was caught by 2 independent fresh-agent E2E tests (Test 7 v0.11.2) where Sonnet defaulted to copying paper-side representation_ref into source_anchors — both runs hit the lint error and recovered by removing source_anchors entirely. The fix lives in this contract, not in agent improvisation.

### Field mapping (brainstorm_summary → review@1 YAML)

| brainstorm_summary field | review@1 YAML location |
|---|---|
| `weaknesses[*]` | `statements[*]` with `statement_type: claim`, `modality: normative` |
| `weaknesses[*].argument` | `statements[*].text` (with verbatim_quote substring embedded) |
| `weaknesses[*].typology` | `statements[*].x_extensions.review_typology` (one of the 7 critique patterns) |
| `weaknesses[*].proposed_anchor` | `relations[*]` with `predicate: challenged_by`, `subject_ref: stmt:<local>` (the local review weakness statement), `object_ref: <paper_rid>#<anchor_id>` (cross-record into the paper) — matches the canonical edge direction shown in § "Cross-record relation conventions" of this same SKILL.md |
| `strengths[*]` | `statements[*]` with `statement_type: claim`, `modality: normative` |
| `strengths[*].proposed_anchor` | `relations[*]` with `predicate: supported_by` (or `cites`), `subject_ref: stmt:<local>` (the local review strength statement), `object_ref: <paper_rid>#<anchor_id>` (cross-record into the paper) — same direction as weaknesses |
| `questions[*]` | `extensions.review.questions[*]` (questions for authors are not first-class statements) |
| `calibration.confidence` | `extensions.review.calibration.confidence` |
| `calibration.recommendation` | `extensions.review.calibration.recommendation` |
| `emit_chain` | `provenance.workflow_chain` |

### `provenance.workflow_chain` (REQUIRED in consume mode)

The output sidecar's `provenance.workflow_chain` MUST be set to the `emit_chain` from the brainstorm_summary (typically `["review-prep", "review-sidecar"]`). Solo-mode records do NOT set workflow_chain (its absence indicates solo origin).

### Banned phrases in consume mode

Skip the post-LLM banned-phrase regex check on `weaknesses[*].argument` text in consume mode — `review-prep` already enforced the reviewer-cliché list during brainstorm, and consume mode does no LLM rewriting that could re-introduce the phrases. Run the regex only on `summary` text (the top-level review record summary, derived from but not identical to the brainstorm).

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` field is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| brainstorm_summary `status` is `needs_rework` (pass control back to stance) | NOT abstain — return `action: return_to_stance` instead |
| post-receipt grounding verification fails on any item | `action: return_to_stance` with `rework_needed` populated |
| brainstorm_summary `emit_chain` does NOT end with `review-sidecar` | `invalid_slot_type.brainstorm_summary` (chain misrouted) |
| Anti-overreach re-check fails: a weakness's premise overlaps a paper-conceded `limitation`/`question` (Jaccard ≥ 0.4) | `action: return_to_stance` (the stance was supposed to enforce this; emitter double-checks) |

## Out of scope

- Multi-paper review (e.g. Area Chair meta-review) — single paper only.
- Auto-detection of profile contamination (paper_rid actually being a review_rid) — caught by G7 filter; explicit detection optional.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/review-mode.md`](../../references/review-mode.md) | [`../../examples/`](../../examples/) (13 gold-standard reviews) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4 | [`../../stances/review-prep/SKILL.md`](../../stances/review-prep/SKILL.md) (paired stance for chain mode)
