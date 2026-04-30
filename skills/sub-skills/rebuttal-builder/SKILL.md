---
name: knows-rebuttal-builder
description: "Draft per-comment response to reviewer comments on your paper, citing supporting sidecars from your corpus. Triggers: 'rebut Reviewer 2's comment about X', 'help me respond to this review', 'draft rebuttal for paper P given review R', 'write my response letter'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: critique_respond
required_inputs:
  - paper_rid                       # the paper being defended (paper@1 sidecar)
  - reviewer_text_or_rid            # the reviewer comments — either raw text OR a review@1 record_id
optional_inputs:
  - brainstorm_summary              # OPTIONAL fenced YAML block produced by the `rebuttal-prep` stance (Type B, v0.11+). When present, the skill switches to CONSUME MODE — mechanical translation of the comment classifications (misread / valid-and-minor / valid-and-major / partial / political / out-of-scope) + response premises into rebuttal_doc Markdown, NOT a re-classification. Schema: `brainstorm-v1`. Solo path (without brainstorm_summary) is the v0.10 default behavior.

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

## Consume mode — `brainstorm_summary` chain (v0.11+, Type B → Type A)

When invoked downstream of the `rebuttal-prep` stance (Type B), rebuttal-builder receives a `brainstorm_summary` input alongside paper_rid + reviewer_text_or_rid. The skill switches from SOLO MODE (v0.10 default — agent classifies + drafts each response) to CONSUME MODE (mechanical translation of pre-classified comments into Markdown).

### Why CONSUME MODE matters here

Rebuttal-builder's solo mode classifies each reviewer comment AND drafts the response in a single LLM call. This conflates two judgment-loaded steps: (a) is this comment misread / valid / political? — author judgment territory, where the user's view dominates; (b) given the classification, what's the right response premise? — agent can help here. Rebuttal-prep separates these by having the user actively triage classifications; consume mode preserves that user judgment in the final document.

### CONSUME MODE flow

```python
if brainstorm_summary is None:
    # SOLO MODE — current v0.10 path. Agent classifies + drafts per Quick Start.
    ...
else:
    summary = parse_brainstorm_summary(brainstorm_summary)
    if summary["status"] == "abandon":
        manifest.abstained = True
        manifest.abstained_reason = "brainstorm_abandoned"
        raise SystemExit
    if summary["status"] == "needs_rework":
        return {"action": "return_to_stance", "rework_needed": summary["rework_needed"]}
    assert summary["status"] == "ready"
    assert summary["emit_chain"][-1] == "rebuttal-builder"

    # Verify each classified_comment has a defensible response_premise
    rework_needed = []
    for i, cc in enumerate(summary["classified_comments"]):
        cls = cc["class"]  # misread | valid-and-minor | valid-and-major | partial | political | out-of-scope
        # misread / partial MUST cite a paper anchor
        if cls in ("misread", "partial") and not cc.get("proposed_anchor"):
            rework_needed.append({"index": i,
                                  "reason": f"class={cls} requires proposed_anchor citation but none supplied"})
            continue
        # valid-and-minor MUST commit to a specific revision
        if cls == "valid-and-minor" and not cc.get("revision_commitment"):
            rework_needed.append({"index": i,
                                  "reason": "class=valid-and-minor requires revision_commitment"})
            continue
        # valid-and-major: stance should have flagged scope decision; emitter just verifies the field exists
        if cls == "valid-and-major" and not cc.get("revision_commitment") and not cc.get("scope_decision"):
            rework_needed.append({"index": i, "reason": "valid-and-major requires either revision_commitment or scope_decision"})
            continue
        # User confirmation
        conf = next((c for c in summary["human_confirmations"]
                     if c.get("reviewer_comment_index") == cc["reviewer_comment_index"]), None)
        if conf is None or conf.get("decision") == "drop":
            rework_needed.append({"index": i, "reason": "user did not confirm classification"})
        # Verify anchor (when present) exists in paper sidecar
        if cc.get("proposed_anchor"):
            anchor_id = cc["proposed_anchor"]["anchor_id"]
            anchor = next((s for s in kept_paper["statements"] if s["id"] == anchor_id), None)
            if anchor is None:
                rework_needed.append({"index": i,
                                      "reason": f"anchor_id {anchor_id} not in paper"})
                continue
            verbatim = cc["proposed_anchor"].get("verbatim_quote", "")
            if verbatim and normalize(verbatim) not in normalize(anchor["text"]):
                rework_needed.append({"index": i,
                                      "reason": "verbatim_quote not substring of anchor text"})

    if rework_needed:
        return {"action": "return_to_stance", "rework_needed": rework_needed}

    # Mechanical translation: per-comment Markdown blocks
    rebuttal_md = render_rebuttal_markdown(summary, kept_paper, kept_review)
    manifest["workflow_chain"] = summary["emit_chain"]   # ["rebuttal-prep", "rebuttal-builder"]
    return rebuttal_md
```

### Field mapping (brainstorm_summary → rebuttal_doc Markdown)

Each `classified_comments[i]` becomes a Markdown block:

```markdown
### Reviewer comment {i+1}: {class label, e.g. "Misread"}

> {original reviewer comment text — quoted verbatim from review@1 or raw input}

{response_premise sentence(s)}

{if class=misread/partial: cite the anchor that addresses it}
[stmt:X from <paper_rid>] — *"verbatim quote"*

{if class=valid-and-minor: revision commitment}
**Revision:** {revision_commitment text}
```

The MD output's preamble naming each class (Misread / Valid (minor) / Valid (major) / Partially valid / Reviewer preference / Out of scope) is hard-coded — agent does NOT relabel.

### `provenance.workflow_chain` (in manifest, not artifact)

rebuttal_doc is Markdown not a sidecar — workflow_chain goes into the run manifest:

```jsonc
{
  "skill": "rebuttal-builder",
  "workflow_chain": ["rebuttal-prep", "rebuttal-builder"],
  ...
}
```

### Hard abstain in consume mode

| Condition | `abstained_reason` |
|---|---|
| brainstorm_summary `schema` is not `brainstorm-v1` | `invalid_slot_type.brainstorm_summary` |
| brainstorm_summary `status` is `abandon` | `brainstorm_abandoned` |
| brainstorm_summary `status` is `needs_rework` | NOT abstain — return `action: return_to_stance` |
| Any `class=misread/partial` lacks `proposed_anchor` | `action: return_to_stance` |
| Any `class=valid-and-minor` lacks `revision_commitment` | `action: return_to_stance` |
| User did not confirm a classification | `action: return_to_stance` |
| brainstorm_summary `emit_chain` does NOT end with `rebuttal-builder` | `invalid_slot_type.brainstorm_summary` |

### Banned phrases in consume mode

The rebuttal-prep stance enforces the rebuttal-cliché banlist (we appreciate / we thank / we will address / etc.) during classification. Skip the post-LLM regex on `response_premise` text in consume mode — re-running it would be redundant and would wrongly flag stance-approved phrasings. Run the regex only on the surrounding boilerplate (intro paragraph, summary table) generated mechanically.

## Out of scope (v1.2)

- Auto-suggest experimental additions ("you should run X to address Y") — only existing-paper defenses, not new-experiment proposals.
- Reviewer-disposition modeling (was R2 hostile vs constructive?) — output stays neutral and factual.
- Multi-reviewer aggregation in one call — one `(paper, review)` pair per call; user calls multiple times for multi-reviewer rebuttals.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
