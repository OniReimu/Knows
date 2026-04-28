---
name: knows-review-sidecar
description: "Generate a structured peer review of a paper as a `profile: review@1` sidecar — weakness and strength statements, each linked back to specific claims in the original paper via `challenged_by` relations. Triggers: 'write a peer review of this paper', 'find the weaknesses in paper X', 'critique this paper as a reviewer would', 'generate a review sidecar', 'do a structured reviewer-style critique'. Use this when the user wants to PRODUCE a review; use sidecar-reader when they want to ANSWER a question about an existing paper."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: critique_generate
required_inputs:
  - paper_rid                       # record_id of the paper@1 sidecar to review

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

## Out of scope

- Multi-paper review (e.g. Area Chair meta-review) — single paper only.
- Auto-detection of profile contamination (paper_rid actually being a review_rid) — caught by G7 filter; explicit detection optional.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/review-mode.md`](../../references/review-mode.md) | [`../../examples/`](../../examples/) (13 gold-standard reviews) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
