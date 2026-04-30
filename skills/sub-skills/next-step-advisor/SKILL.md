---
name: knows-next-step-advisor
description: "Produce an evidence-backed next-step research brief — N candidate research questions for a topic, each grounded in retrieved sidecars' open questions, limitations, reflections, lessons, and reader-spotted gaps. Triggers: 'what should I work on next in X', 'where are the gaps in Y research', 'give me 5 thesis ideas about Z', 'what's underexplored in W'. Heuristic by design — bounded by the top-K retrieved sidecars (paper@1 + commentary@1), not a corpus-wide gap detector. v0.10: evidence pool now includes reader/agent commentary@1 reflections in addition to paper@1 author-stated open questions/limitations."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: brief_next_steps
required_inputs:
  - query_text                      # research area / topic in natural language

requested_artifacts:
  - next_step_brief                 # Markdown brief: N candidate questions, each with supporting refs

# Profile contract — G7. paper@1 is the primary evidence source; commentary@1 sidecars
# (reader/agent reflections produced by `commentary-builder`) are pulled via a SECOND fetch
# phase per Quick Start §3 below — joined in-memory because the hub /search API does not
# currently support cross-profile `reflects_on:<rid>` filtering. See api-schema.md
# "v0.10 prerequisite" callout. The skill body MUST keep paper@1 and commentary@1 hits
# in separate working sets to satisfy G7 (no profile co-mingling) — they are unioned
# only at evidence-aggregation time.
accepts_profiles: [paper@1, commentary@1]

# Quality policy — G2' (strict, since speculative synthesis is the failure mode)
quality_policy:
  require_lint_passed: true
  allowed_coverage:                 # exclude `partial` aggressively — partial coverage is exactly where speculation creeps in
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (default partial: only need question + limitation statements, not full record)
requires_full_record: false

# emits_profile omitted — next_step_brief is prose, not a sidecar artifact (read-only)
---

# next-step-advisor — Evidence-backed next-step research brief

**High-risk skill — abstain rules are strict by design.** Without them, the output degrades into plausible-sounding LLM speculation that damages user trust. The core value is **grounded** advice — each candidate question must trace to one of: paper@1 `question` / `limitation` / `reflection` / `lesson` statements, or commentary@1 `gap_spotted` / `lesson` / `scenario_extrapolation` / `method_transfer_idea` statements (commentary@1 sidecars are author-of-paper-independent reflections produced by `commentary-builder`).

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_search, fetch_partial, filter_records, Manifest

# 1. Dispatch tuple
TOPIC = "multi-path CoT in LLM reasoning"
TOP_K = 12

decision = dispatch("brief_next_steps", {"query_text": TOPIC}, "next_step_brief")
assert decision["action"] == "route"

# 2. G5 + G7 + G2': retrieve top-K paper@1 sidecars
manifest = Manifest(skill="next-step-advisor", intent_class="brief_next_steps",
                    queries=[TOPIC],
                    dispatch_tuple="(brief_next_steps,{query_text},next_step_brief)")
paper_hits_raw = fetch_search(TOPIC, sort="trending", limit=min(TOP_K * 3, 100)).get("results", [])
paper_hits = [h for h in paper_hits_raw if h.get("profile") == "paper@1"][:TOP_K]
# sort="trending" prefers community-attended papers — more likely to have outstanding limitations
# the field has noticed but not solved. Falls back to "latest" if trending data sparse on this topic.
# limit > top_k over-fetches so G2'/G7 filters have headroom; commentary@1 hits returned by /search
# are filtered out here because we want paper@1 as the seed for the two-phase fetch in §3 below.
manifest.returned_rids = [h["record_id"] for h in paper_hits]
kept_papers = filter_records(paper_hits, "next-step-advisor", manifest)
if not kept_papers:
    print({"abstained": True, "reason": "empty_working_set_after_quality_filter"}); raise SystemExit

# 3a. G3 partial fetch — paper@1 statements (now FOUR types: question, limitation, reflection, lesson)
PAPER_GAP_TYPES = ("question", "limitation", "reflection", "lesson")
contexts = []
for h in kept_papers:
    rid = h["record_id"]
    part = fetch_partial(rid, "statements")
    qs = [s for s in part.get("items", []) if s.get("statement_type") in PAPER_GAP_TYPES]
    if qs:
        contexts.append({"rid": rid, "title": h.get("title"), "profile": "paper@1",
                         "evidence_stmts": qs})
    manifest.fetch_mode_per_rid[rid] = "partial:statements"

# 3b. SECOND FETCH PHASE — commentary@1 sidecars reflecting on these papers.
# The hub /search API has NO `reflects_on:<rid>` filter (api-schema.md §"v0.10 prerequisite").
# Workaround: keyword-search commentary@1 by paper title (Weight A in tsvector ranking),
# then filter in-memory by the `reflects_on` relations that resolve to one of our paper RIDs.
# This is the documented two-phase fallback. When the hub adds a relation-typed filter,
# the second phase collapses into a single targeted query.
COMMENTARY_GAP_TYPES = ("gap_spotted", "lesson", "scenario_extrapolation", "method_transfer_idea")
# IMPORTANT: seed Phase 2 from EVERY kept paper, NOT just from those that already had
# author-stated gap-bearing statements (the `contexts` subset). The whole reason
# commentary@1 exists is to recover gaps for AUTHOR-SILENT papers — papers that
# survived G2' but have zero question/limitation/reflection/lesson statements
# because publication pressure stripped them. If we seeded from `contexts` only,
# those exact papers (the v0.10 main use case) would get skipped before the
# commentary join. So seed_rids and the title-query loop both walk `kept_papers`.
seed_rids = {h["record_id"] for h in kept_papers}
commentary_candidates = []
for h in kept_papers:
    title_query = h.get("title")
    if not title_query:
        continue  # title is the AND-tsquery key; without it Phase 2 cannot recall reliably
    com_hits = fetch_search(title_query, limit=20).get("results", [])
    for ch in com_hits:
        if ch.get("profile") != "commentary@1":
            continue
        commentary_candidates.append(ch)
manifest.returned_rids.extend([h["record_id"] for h in commentary_candidates])
kept_commentary = filter_records(commentary_candidates, "next-step-advisor", manifest)
for ch in kept_commentary:
    rid = ch["record_id"]
    part_stmts = fetch_partial(rid, "statements")
    part_rels = fetch_partial(rid, "relations")
    # In-memory join: keep only commentary statements whose reflects_on points into seed_rids
    refl_targets = {r["object_ref"].split("#")[0]
                    for r in part_rels.get("items", [])
                    if r.get("predicate") == "reflects_on"}
    if not (refl_targets & seed_rids):
        continue  # commentary record reflects on a different paper — not relevant
    com_stmts = [s for s in part_stmts.get("items", []) if s.get("statement_type") in COMMENTARY_GAP_TYPES]
    if com_stmts:
        contexts.append({"rid": rid, "title": ch.get("title"), "profile": "commentary@1",
                         "evidence_stmts": com_stmts,
                         "anchored_to": list(refl_targets & seed_rids)})
    manifest.fetch_mode_per_rid[rid] = "partial:statements+relations"

# 4a. HARD ABSTAIN (numeric): total evidence statements across the union (paper@1 + commentary@1) < 3 → refuse
total_evidence = sum(len(c["evidence_stmts"]) for c in contexts)
if total_evidence < 3:
    manifest.abstained = True
    manifest.abstained_reason = "empty_working_set_after_quality_filter"
    print({"abstained": True,
           "reason": "too few gap-bearing statements (paper@1 q/l/r/l + commentary@1 g/l/s/m) to ground a brief — try a more specific topic OR run commentary-builder on the top papers first"})
    raise SystemExit

# 4b. HARD ABSTAIN (topical, §4.1): for intersection queries (A × B), require ≥ 1
#     statement that names BOTH sides. Without this precheck, the LLM can stitch a
#     statement about A onto a statement about B — speculation by composition.
from orchestrator import parse_intersection_query, topical_grounding_count
intersection = parse_intersection_query(TOPIC)
if intersection:
    a, b = intersection
    all_stmts = [s for c in contexts for s in c["evidence_stmts"]]
    n_topical = topical_grounding_count(all_stmts, a, b)
    if n_topical < 1:
        manifest.abstained = True
        manifest.abstained_reason = "empty_working_set_after_quality_filter"
        print({"abstained": True,
               "reason": f"intersection query '{a}' × '{b}': 0 statements name both — gap-bearing count was {total_evidence} (paper@1 + commentary@1 union) but none span the intersection. Pivot retrieval source (Scholar/arXiv) before committing."})
        raise SystemExit

# 5. LLM call — use the canonical prompt from `references/next-step-advisor-prompt.md`.
#    The prompt locks in: banned-phrase enforcement (15 speculation tells), grounding contract
#    (every candidate must cite stmt:* + verbatim_quote substring), banned candidate categories
#    (replication, generic apply-to-domain, improve-by-N%, vacuous combinations), JSON output
#    schema, and the mandatory heuristic disclaimer. Do NOT re-derive these rules per agent —
#    use the canonical prompt verbatim, then run the post-LLM banned-phrase + grounding checks
#    that document specifies (with one regenerate retry on failure).
# Output: structured JSON per the prompt's schema, plus the disclaimer footer in the
# user-facing prose.

# 6. Manifest finalize: explicitly mark as heuristic (not corpus-wide):
manifest.model = "claude-opus-4-7"
manifest.applied_profile_filters = ["paper@1", "commentary@1"]
print(manifest.finish())
# The output prose MUST also include this disclaimer footer (G4 governance gap):
#   "This brief is heuristic, not corpus-wide. Recall is bounded by the top-K retrieved
#    paper@1 sidecars (here K=12), their `question`/`limitation`/`reflection`/`lesson`
#    coverage, and the commentary@1 sidecars that reflect on them. A gap not surfaced
#    here may still exist in the broader literature, especially if no commentary@1
#    sidecars exist yet for the seed papers — running `commentary-builder` first on
#    the top papers will deepen the evidence pool."
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `next_step_brief` | Markdown brief: 3-5 grounded questions, evidence inventory, heuristic disclaimer |

## Hard abstain rules (this skill is unusual — extra strict)

| Condition | `abstained_reason` |
|---|---|
| `query_text` missing or empty | `missing_required_input.query_text` |
| Working set empty after G7/G2' | `empty_working_set_after_profile_filter` / `_quality_filter` |
| **< 3 gap-bearing statements** across the union of paper@1 (q/l/r/l) + commentary@1 (g/l/s/m) | `empty_working_set_after_quality_filter` (insufficient grounding evidence) |
| LLM tries to output > 5 candidate questions | abort + retry; cap at 5 |
| LLM outputs a candidate without ≥1 stmt:* citation | abort + retry; if 2 retries fail → abstain `skill_runtime_exception.UngroundedSpeculation` |

## Banned phrases (compile-time check)

If the LLM output contains any of these without a `[stmt:* from RID]` citation in the same sentence, regenerate:
- "could explore" / "might investigate" / "promising direction"
- "future work could" / "this opens up" / "intriguing avenue"
- "underexplored" / "ripe for" / "ample opportunity"

These are the speculation tells that damage user trust. Either back the claim with a sidecar reference or omit it.

> **Shared list.** `commentary-builder-prompt.md` uses the same 9 phrases. Any change here MUST propagate there — they are deliberately one canonical list because both skills produce the same fabrication failure mode.

## Manifest emission

Per G6 + G4: `skill: next-step-advisor`, `intent_class: brief_next_steps`, `dispatch_tuple`, `queries: [TOPIC]`, `returned_rids` (paper@1 + commentary@1 unioned), `fetch_mode_per_rid` (paper rows `partial:statements`, commentary rows `partial:statements+relations`), `applied_profile_filters: [paper@1, commentary@1]`, `model`, plus skill-specific `evidence_inventory: {n_questions, n_limitations, n_reflections, n_lessons_paper, n_gap_spotted, n_scenario_extrapolation, n_method_transfer, n_lessons_commentary, n_kept_paper_records, n_kept_commentary_records}`. The output MUST embed the heuristic disclaimer (G4 governance-gap) AND a note about commentary coverage (e.g. "0 commentary@1 sidecars found for the seed papers — evidence pool is paper@1-only; running `commentary-builder` first would deepen the pool").

## Out of scope (v1.2)

- Cross-conference temporal analysis ("after ICLR 2026 ended, what's still open?") — would need date-filtered search, currently best-effort.
- Funding-feasibility scoring — pure research-direction signal only.
- LLM-judged "novelty score" per candidate — too noisy without human review.
- Multi-topic blending ("multi-path CoT AND federated learning") — single topic only in v1.2.
- Auto-running `commentary-builder` on paper@1 sidecars whose commentary count is 0 — surfaces as a recommendation in the brief but the user must trigger the secondary skill explicitly.

## Hub-search dependency (v0.10)

The two-phase fetch in §3 above is a workaround for a missing hub feature: cross-profile relation-typed filtering (`reflects_on:<rid>`). Once the hub adds either:
- a `?relation=reflects_on&target_rid=<rid>` query parameter on `/search`, OR
- a dedicated `/relations` endpoint that returns `commentary@1` RIDs whose `relations[*].predicate==reflects_on AND object_ref starts with <paper_rid>`,

the second fetch phase collapses to a single targeted call per seed paper. Until then, the title-keyword fallback works but pulls extra noise that gets filtered in-memory. See `api-schema.md` "v0.10 prerequisite" callout for the request schema we expect.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4 | [`../commentary-builder/SKILL.md`](../commentary-builder/SKILL.md) (upstream producer of commentary@1 sidecars consumed by this skill) | [`../../references/commentary-builder-prompt.md`](../../references/commentary-builder-prompt.md) (shared 9-phrase banned list)
