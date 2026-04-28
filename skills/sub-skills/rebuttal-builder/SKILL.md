---
name: knows-rebuttal-builder
description: "Draft per-comment response to reviewer comments on your paper, citing supporting sidecars from your corpus. Triggers: 'rebut Reviewer 2's comment about X', 'help me respond to this review', 'draft rebuttal for paper P given review R', 'write my response letter'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: critique_respond
required_inputs:
  - paper_rid                       # the paper being defended (paper@1 sidecar)
  - reviewer_text_or_rid            # the reviewer comments — either raw text OR a review@1 record_id

requested_artifacts:
  - rebuttal_doc                    # Markdown response per comment with citations

# Profile contract — G7 (multi-input via co_inputs)
co_inputs:
  paper: paper@1
  review: review@1                  # accepts review@1 if reviewer_text_or_rid is a RID; raw-text input bypasses this slot

# Quality policy — G2'
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (need full paper record for evidence; review record for cross-refs)
requires_full_record: true

# emits_profile omitted — rebuttal_doc is prose, not a sidecar artifact (read-only)
---

# rebuttal-builder — Per-comment response with citations

Different from `review-sidecar` (generates reviews). This **responds** to reviewer comments. Multi-input: needs both the paper being defended AND the reviewer text/sidecar.

> Strict: refuses to draft a rebuttal from open-corpus search alone — must have explicit `(paper, review)` pair. Anti-spec: agent must NOT make up reviewer comments.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_sidecar, filter_records, Manifest

# 1. Dispatch tuple — multi-input
PAPER_RID = "knows:vaswani/attention/1.0.0"
REVIEW_INPUT = "knows:reviewer-2/attention-review/1.0.0"   # OR raw text string of review

decision = dispatch("critique_respond",
                    {"paper_rid": PAPER_RID, "reviewer_text_or_rid": REVIEW_INPUT},
                    "rebuttal_doc")
assert decision["action"] == "route"

# 2. G5 + G7: fetch both records (review may be raw text — skip fetch in that case)
manifest = Manifest(skill="rebuttal-builder", intent_class="critique_respond",
                    dispatch_tuple="(critique_respond,{paper_rid,reviewer_text_or_rid},rebuttal_doc)",
                    returned_rids=[PAPER_RID])
paper = fetch_sidecar(PAPER_RID)
manifest.fetch_mode_per_rid[PAPER_RID] = "full"

if isinstance(REVIEW_INPUT, str) and REVIEW_INPUT.startswith("knows:"):
    review = fetch_sidecar(REVIEW_INPUT)
    manifest.returned_rids.append(REVIEW_INPUT)
    manifest.fetch_mode_per_rid[REVIEW_INPUT] = "full"
    review_text_blob = "\n".join(s.get("text","") for s in review.get("statements",[]))
else:
    review_text_blob = REVIEW_INPUT  # raw text mode
    review = None  # no review@1 sidecar

# 3. G7: paper slot must be paper@1; review slot (if RID) must be review@1
#    Apply per-slot filter; abstain missing_co_input.review if review slot empty after filter
#    (co_inputs slots are independently filtered per dispatch-and-profile.md §3.3)
paper_kept = filter_records([{**paper, "stats":{"stmt_count":len(paper.get("statements",[]))},
                              "coverage_statements":paper.get("coverage",{}).get("statements"),
                              "lint_passed":True, "record_id":PAPER_RID}], "rebuttal-builder", manifest)
if not paper_kept:
    print({"abstained": True, "reason": "missing_co_input.paper"}); raise SystemExit

# 4. Decompose review_text_blob into discrete reviewer comments per `rebuttal-builder.md` §6
#    (W1, W2, ..., Q1, Q2, ...). Cap at 20.

# 5. LLM call — use the canonical prompt from `references/rebuttal-builder-prompt.md`.
#    The prompt locks in: fabrication-tell banned phrases ("we believe", "obviously", etc.),
#    response_type taxonomy (rebuttal | concession | clarification), citation format
#    ([stmt:* from RID]), grounding contract (every rebuttal/clarification claim must cite
#    a real paper anchor), tone register (respectful but firm, no whining), and the
#    no-sidecar fallback policy. Do NOT re-derive these rules per agent — use the
#    canonical prompt verbatim, then run the post-LLM banned-phrase + grounding checks
#    that document specifies (with one regenerate retry on failure).

# 6. Output: structured JSON per the prompt's schema. Render to Markdown for the user
#    with the citation-rate footer attached if `n_comments_with_citation / n_comments_extracted < 0.6`.

# 7. Manifest finalize
manifest.model = "claude-opus-4-7"
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `rebuttal_doc` | Markdown rebuttal: per-comment response with stmt:* refs to paper + `\cite{}` keys to corpus |

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `paper_rid` slot missing | `missing_required_input.paper_rid` |
| `reviewer_text_or_rid` slot missing or empty | `missing_required_input.reviewer_text_or_rid` |
| Paper rid 404s | `rid_not_found.<rid>` |
| Review rid 404s (when supplied as RID) | `rid_not_found.<rid>` |
| Paper fails G7/G2' | `missing_co_input.paper` (multi-input slot empty after filter) |
| Review supplied as RID but profile != review@1 | `missing_co_input.review` |
| Reviewer text decomposes to 0 discrete comments | `skill_runtime_exception.NoCommentsExtracted` |

## Anti-fabrication rules

- **NEVER invent reviewer comments**. If `reviewer_text_or_rid` doesn't decompose cleanly, abstain — do not LLM-imagine what the reviewer might have said.
- **NEVER claim experiments not in the paper sidecar**. Every "we did X" defense must trace to a `stmt:*` or `ev:*` in the paper.
- **DO** suggest "we will add Y in the camera-ready" when reviewer asks for missing analysis — that's an honest concession, not fabrication.

## Manifest emission

Per G6: `skill: rebuttal-builder`, `intent_class: critique_respond`, `dispatch_tuple`, `returned_rids: [paper, review_if_rid]`, `applied_profile_filters: {paper: paper@1, review: review@1}` (dict shape per §6.1 multi-input writer rule), `fetch_mode_per_rid: {... "full"}`, `model`, plus skill-specific `n_comments_extracted` and `n_comments_with_citation`.

## Out of scope (v1.2)

- Auto-suggest experimental additions ("you should run X to address Y") — only existing-paper defenses, not new-experiment proposals.
- Reviewer-disposition modeling (was R2 hostile vs constructive?) — output stays neutral and factual.
- Multi-reviewer aggregation in one call — one `(paper, review)` pair per call; user calls multiple times for multi-reviewer rebuttals.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
