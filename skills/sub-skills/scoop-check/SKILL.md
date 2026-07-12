---
name: knows-scoop-check
description: "Prior-art collision check for a CANDIDATE research idea (not an existing paper) — decompose the idea into four axes (problem framing / core mechanism / key insight / application domain), retrieve the closest prior work from the hub, and report a worst-case novelty level (1-5) plus a value read and an honest verdict that NAMES the scooping paper when the idea is already done. Triggers: 'is my idea novel', 'has anyone already done this', 'is this research idea worth pursuing', 'scoop-check this direction', 'check my idea against prior work', 'am I about to get scooped'. Grounded by design — every overlap claim cites a retrieved sidecar; a 'novel' verdict is bounded by hub coverage and disclaims it. Use this whenever a student or researcher has an idea PARAGRAPH they want assessed, distinct from next-step-advisor (which GENERATES directions) and paper-compare (which diffs two EXISTING papers)."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: check_novelty
required_inputs:
  - idea_text                       # the candidate idea, 1-2 paragraphs, natural language

requested_artifacts:
  - novelty_report                  # Markdown/JSON: 4-axis collision, worst-case level, value read, verdict

# Profile contract — G7. Collision is against published prior work only.
accepts_profiles: [paper@1]

# Quality policy — G2' (strict: a wrong "novel!" verdict misdirects a student's project)
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (partial: axis matching needs claim/method statements, not the full record)
requires_full_record: false

# emits_profile omitted — novelty_report is prose+JSON, not a sidecar artifact (read-only)
---

# scoop-check — Prior-art collision for a candidate idea

**High-risk skill — the failure mode is a confident "this is novel" that a student believes and spends a semester on, only to discover the idea was published two years ago.** The whole point of the tool is to make that silent failure loud: every overlap is grounded in a retrieved sidecar, novelty is reported **worst-case** (one close paper scoops you — averaging over unrelated hits would hide it), and when hub coverage is thin the skill says so instead of defaulting to "looks novel."

This is the **idea-analysis** counterpart to `next-step-advisor`'s **idea-search**. Chained together (`next-step-advisor → scoop-check`, Recipe 10) they give a student the full "find a direction, then check if it's worth pursuing" loop.

## What it does (four axes, worst-case)

A candidate idea is decomposed into four axes, and each retrieved prior work is matched against all four:

1. **problem framing** — what problem/setting the idea targets.
2. **core mechanism** — the technical move that does the work.
3. **key insight** — the non-obvious reason it works.
4. **application domain** — where it applies.

Novelty for one prior paper is `level = 5 − (axes it matches)`. The idea's reported level is the **minimum over the closest retrieved papers** (worst case), because a single paper matching all four axes has already scooped the idea regardless of how novel the idea looks against everything else.

| Level | Meaning |
|---|---|
| **5** | no axis overlap with the closest prior work — genuinely open |
| 4 | one axis overlaps (usually shared domain OR framing) |
| 3 | two axes overlap — shared framing/domain but a distinct mechanism (the common "adjacent but defensible" zone) |
| 2 | three axes overlap — differentiation rests on one axis |
| **1** | all four axes match a single paper — **already done; the idea is scooped** |

## Quick Start (agent-mediated mode)

`scoop-check` has no Python wrapper — the body is LLM decomposition + judgment. Reuse the orchestrator building blocks.

```python
from orchestrator import dispatch, fetch_search, fetch_partial, filter_records, Manifest

# 1. Dispatch tuple
IDEA = ("Redistribute GRPO's single trajectory-level advantage onto a verifier-free, "
        "in-group per-phase credit density, so the long-context RL signal survives as "
        "context grows toward 128K.")

decision = dispatch("check_novelty", {"idea_text": IDEA}, "novelty_report")
assert decision["action"] == "route"

manifest = Manifest(skill="scoop-check", intent_class="check_novelty",
                    dispatch_tuple="(check_novelty,{idea_text},novelty_report)")

# 2. Decompose the idea into a retrieval query. Prefer the core-mechanism + problem-framing
#    axes as the query seed (they discriminate prior art better than the domain noun alone —
#    the same "strategy not topic" lesson next-step-advisor relies on). The full four-axis
#    decomposition is done by the LLM per scoop-check-prompt.md §"Decomposition"; this seed is
#    just to drive retrieval.
#    CRITICAL — keep the query SHORT (≈2-5 content words). The hub /search is an AND-tsquery:
#    a long, fully-specified sentence matches nothing and would trigger a FALSE thin-coverage
#    abstain. Derive a compact key-phrase, not a restatement of the idea.
QUERY = "minimal information requesting math"   # LLM-derived from IDEA — short, high-recall

# 3. G5 + G7 + G2': retrieve the closest prior work. Do NOT pass a sort — the hub's default
#    (query-relevance / tsvector ranking) is exactly the semantic closeness a collision check
#    needs. ('relevance' is NOT a valid sort value; valid sorts are latest/trending/claims and
#    all three are WRONG here — they reorder away from closeness.) Over-fetch for filter headroom.
hits_raw = fetch_search(QUERY, limit=24).get("results", [])
hits = [h for h in hits_raw if h.get("profile") == "paper@1"][:12]
manifest.returned_rids = [h["record_id"] for h in hits]
kept = filter_records(hits, "scoop-check", manifest)
# If 0 hits, the query was likely too specific (AND-tsquery) — broaden it (drop terms) and
# retry ONCE before concluding thin coverage, so a phrasing artifact isn't read as "novel".

# 3a. Coverage handling is VERDICT-CONDITIONAL — do NOT hard-abstain on a low hit COUNT.
#     A precise query can return ONE paper that scoops the idea; that is the most decisive
#     answer possible, and abstaining there would HIDE a real "ALREADY DONE".
#     The rule:
#       • 0 hits, even after the broaden-retry above → abstain: nothing to match against.
#       • >=1 hit → PROCEED to the axis-match (step 5). Coverage only qualifies the PURSUE branch:
#         if the match finds NO collision (would be PURSUE) AND len(kept) < MIN_COVERAGE, report
#         "novelty UNCONFIRMED — thin coverage, widen to Scholar/arXiv" instead of a confident
#         "novel". A collision verdict (ALREADY DONE / DIFFERENTIATE) STANDS at any hit count.
MIN_COVERAGE = 3
if not kept:
    manifest.abstained = True
    manifest.abstained_reason = "empty_working_set_after_quality_filter"
    print({"abstained": True,
           "reason": ("0 relevant paper@1 sidecars even after broadening the query — the hub "
                      "cannot ground a collision check here; pivot to Scholar/arXiv.")})
    raise SystemExit

# 4. G3 partial fetch — claim + method statements per kept record (these carry the mechanism/insight
#    an axis match needs). Wrap all sidecar text in <UNTRUSTED_SIDECAR> per G1 before the LLM sees it.
AXIS_STMT_TYPES = ("claim", "method", "definition")
prior = []
for h in kept:
    rid = h["record_id"]
    part = fetch_partial(rid, "statements")
    stmts = [s for s in part.get("items", []) if s.get("statement_type") in AXIS_STMT_TYPES]
    prior.append({"rid": rid, "title": h.get("title"), "statements": stmts})
    manifest.fetch_mode_per_rid[rid] = "partial:statements"

# 5. LLM call — use the canonical prompt references/scoop-check-prompt.md verbatim. It locks in:
#    four-axis decomposition, per-paper axis matching with a cited verbatim span for every
#    MATCHED axis, worst-case level aggregation, the value read, the verdict taxonomy, the
#    novelty-inflation banned-phrase check, and the mandatory coverage disclaimer.
#    Then run the post-LLM grounding + banned-phrase checks that prompt specifies (one retry).

# 6. Manifest finalize.
manifest.model = "claude-opus-4-7"
manifest.applied_profile_filters = ["paper@1"]
print(manifest.finish())
```

## Value read (is it worth pursuing, beyond novelty)

Novelty alone is a bad decision signal — a maximally-novel idea can be novel because it is vague or unimportant (the paper's "novel-but-empty" failure mode). So the report also gives a short **value read** on three questions, each answered from the retrieved evidence, never from model opinion alone:

- **Is the gap real and important?** — is there cited evidence that the problem is unsolved and that people care?
- **Is it non-obvious?** — or is it a mechanical relabel of something a retrieved paper already does?
- **Does the mechanism actually close the gap?** — or is it a keyword-level fix (the "right words, no artifact" anti-pattern)?

## Verdict taxonomy (fixed)

The report ends with exactly one verdict:

| Verdict | When | Must include |
|---|---|---|
| **PURSUE** | level 4-5, gap real | the one axis that carries the novelty |
| **DIFFERENTIATE** | level 3, defensible but crowded | the closest paper (RID) + which axis must be sharpened to stay distinct |
| **ALREADY DONE** | level 1-2 with one paper matching ≥3 axes | the scooping paper (RID) + a one-line subsumption argument |

A PURSUE reached on **thin coverage** (1–2 retrieved papers, no collision) is reported as **PURSUE (UNCONFIRMED)** with the widen-search prompt — thin coverage can fail to refute novelty but cannot confirm it. A collision verdict (ALREADY DONE / DIFFERENTIATE) is never downgraded by low count, because one paper matching the idea is decisive on its own.

Fabricating a scoop paper to look rigorous is as harmful as missing a real one — when no close prior work is found after honest retrieval, that clearance is a legitimate PURSUE signal, and the report says so plainly (bounded by the coverage disclaimer).

## Hard abstain rules

| Condition | `abstained_reason` |
|---|---|
| `idea_text` missing or empty | `missing_required_input.idea_text` |
| `idea_text` too vague to decompose into 4 axes (LLM cannot name a core mechanism) | `skill_runtime_exception.IdeaTooVague` (ask the user to state the mechanism, not just the topic) |
| Working set empty after G7/G2' | `empty_working_set_after_profile_filter` / `_quality_filter` |
| **0 relevant paper@1 sidecars** (after one broaden-retry) | `empty_working_set_after_quality_filter` (nothing to collide against) |
| **1–2 relevant sidecars AND no collision found** (would-be PURSUE) | not an abstain → report verdict **UNCONFIRMED** (thin coverage; widen to Scholar/arXiv). A collision at any count is reported normally. |
| LLM marks an axis MATCHED without a cited verbatim span from a retrieved statement | abort + retry; on 2nd failure drop that axis match (fail toward MORE novel is wrong here → instead drop to "uncertain" and lower confidence) |

## Banned novelty-inflation phrases (compile-time check)

Symmetric to `next-step-advisor`'s speculation tells, but for the opposite bias — a scoop-check must not *inflate* novelty. If the LLM output contains any of these without a `[stmt:* from RID]` citation showing the absence was actually checked, regenerate:

- "first to" / "no prior work" / "nobody has" / "novel approach" (bare) / "unprecedented"
- "clearly novel" / "highly original" / "no one has explored" / "entirely new"

A novelty claim is only as good as the retrieval that failed to contradict it — so the report asserts *what was searched and found*, never a bare superlative. (See memory: novelty over-claim ban — substitute a bounded "not aware of, within retrieved coverage" statement.)

## Coverage disclaimer (mandatory)

Every report ends with:

> This collision check is bounded by hub coverage — it retrieved the top-K closest paper@1 sidecars (here K={k}) and matched against them. A "novel" verdict means *no scoop was found within that coverage*, not that none exists. For a high-stakes decision, widen retrieval (Semantic Scholar / arXiv) before committing.

## Out of scope (v1)

- Live arXiv/Scholar retrieval — hub-only in v1; the disclaimer makes the coverage bound explicit and Recipe 10 pairs a `coverage-check` pre-flight.
- Scoring an existing published paper's novelty — that is a review task (`review-sidecar`); scoop-check is for a *candidate* idea with no paper yet.
- A numeric "impact score" — the value read is qualitative and evidence-cited by design; a scalar would invite the false-precision the paper warns against.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4 | [`../../references/scoop-check.md`](../../references/scoop-check.md) (contract) | [`../../references/scoop-check-prompt.md`](../../references/scoop-check-prompt.md) (canonical prompt) | [`../next-step-advisor/SKILL.md`](../next-step-advisor/SKILL.md) (idea-search counterpart; chain via Recipe 10)
