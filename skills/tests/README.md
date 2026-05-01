# Knows Orchestrator Integration Tests

English | [中文](./README.zh.md)

Three fixtures exercise orchestration plumbing that the v1.0 public sub-skills don't touch directly. **CI green on all three is a hard prerequisite for v1 release** per `../references/dispatch-and-profile.md` §7.5.

## Fixtures

### `fixture_mixed_profile_retrieval/`

Exercises **G7 — Profile Discipline** and §3 (typed co-input slots).

**Synthetic corpus** (in `run.py`): `paper@1` records + `review@1` records + records with malformed `profile` field + records with missing `profile` field.

**Skills exercised**: any single-input skill declaring `accepts_profiles: [paper@1]` (e.g. `paper-finder` smoke); a multi-input skill declaring `co_inputs: {paper: paper@1, review: review@1}` (e.g. `rebuttal-builder` smoke).

**Asserts**:
- A `paper@1`-only skill never sees a `review@1` record in its working set.
- Records with missing/malformed `profile` are excluded by default (unless skill opts into `accepts_profiles: [unknown]`).
- Manifest contains correct `excluded_missing_profile` and `excluded_malformed_profile` entries.
- Multi-input skill's `paper` and `review` slots filtered independently; empty slot raises `missing_co_input.<slot_name>`.

### `fixture_quality_exclusion_logging/`

Exercises **G2' — Skill-declared Quality Policy** and §6 (manifest visibility).

**Synthetic corpus** (in `run.py`): records with mixed `lint_passed: true/false`, varying `coverage.statements` enum values, varying `coverage.evidence` enum values, varying statement counts (some <5, some ≥5).

**Skills exercised**: a skill declaring strict `quality_policy: {require_lint_passed: true, allowed_coverage: [exhaustive, main_claims_only], min_statements: 5}`.

**Asserts**:
- Records failing `require_lint_passed` are excluded.
- Records with `coverage.statements` outside `allowed_coverage` are excluded.
- Records with statement count `< min_statements` are excluded.
- Manifest's `quality_exclusions` enumerates every dropped record with `policy_field` (which check failed) and `actual` (the record's actual value).
- Skill body never sees an excluded record.

### `fixture_dispatch_clarify_and_abstain/`

Exercises **§4 (Clarification Protocol)** and **§5 (Abstain Conditions)**.

**Synthetic queries** (4 paths):
1. **Unique-tuple path**: tuple matches exactly one §1.5 row → routes correctly to single skill.
2. **Ambiguous-clarify path**: tuple matches >1 row → orchestrator emits one clarification turn enumerating candidates.
3. **Ambiguous-abstain path**: ambiguous tuple + non-resolving reply → orchestrator abstains with `ambiguous_dispatch_unresolved_after_clarification`, manifest's `abstained_reason` populated.
4. **Ambiguous-resolve path**: ambiguous tuple + resolving reply (names skill+artifact) → routes correctly.

**Asserts**:
- No silent default-route ever fires (path 3 must abstain, never silently pick most-read-only).
- Path 2 emits exactly one clarification message; no recursive clarification chain.
- Path 4's reply must uniquely identify one row (single-row skill name OR multi-row skill name + artifact).
- Manifest `abstained_reason` populated only on path 3.

## Running

```bash
bash skills/tests/run_all.sh                                       # all three
python3 skills/tests/fixture_dispatch_clarify_and_abstain/run.py   # one fixture
```

Each fixture is self-contained in its own directory with a `run.py` runner. `run_all.sh` invokes all three and exits non-zero if any fail.
