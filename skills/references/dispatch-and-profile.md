# Dispatch and Profile — Cross-Cutting Orchestrator Contract

**Status**: v1.0.

This is the highest-blast-radius contract in the Knows orchestrator. Every
sub-skill consumes it; the orchestrator implements it. A bug here contaminates
multiple skills simultaneously and silently. **Treat changes as breaking
unless you can prove otherwise.**

> Companion docs:
> - `api-schema.md` — verified knows.academy API endpoints + response shapes
> - `remote-modes.md` — workflow patterns + natural-language routing examples
> - `knows-record-0.9.json` — canonical sidecar schema (the source of truth for
>   `profile`, `record_status`, `replaces`, `coverage`, `provenance` enums)

---

## 1. Dispatch Tuple Grammar

The orchestrator routes user intent to a sub-skill via a typed tuple, **not**
keyword matching. Routing is deterministic given the tuple.

### 1.1 Tuple shape

```
(intent_class, required_inputs, requested_artifact) → skill
```

| Field | Type | Purpose |
|---|---|---|
| `intent_class` | enum string | Coarse-grained verb (see §1.2) |
| `required_inputs` | object | Typed slot map; keys depend on `intent_class` (see §1.3) |
| `requested_artifact` | enum string | What the user gets back (see §1.4) |

### 1.2 `intent_class` allowed values

| Value | Meaning |
|---|---|
| `discover` | Find records matching a query |
| `extract` | Answer a question from one record |
| `synthesize_prose` | Compose narrative text grounded in N records |
| `synthesize_table` | Compose comparison table grounded in N records |
| `diff` | Pairwise compare two records |
| `critique_generate` | Produce a fresh peer review of a paper record |
| `critique_respond` | Draft a response to reviewer comments on a paper |
| `brief_next_steps` | Produce an evidence-backed next-step brief |
| `contribute` | Generate a new sidecar from a source artifact |
| `inspect_lineage` | Walk one record's declared `replaces` chain backward |
| `revise_local` | Patch whitelisted fields of an existing sidecar locally |

Adding a new `intent_class` is a **breaking change** to this contract.

### 1.3 `required_inputs` slot map

Slot keys are typed. Validation runs in two phases:

- **Registration-time** (skill load): orchestrator validates the skill's
  declared `required_inputs` *schema* — slot keys exist in §1.3 below,
  declared types match the column, no unknown slot names. Failure logs
  the load error and skips registration. Any subsequent dispatch
  targeting the unloaded skill abstains with
  `skill_unregistered.<skill_name>` per §5.
- **Runtime** (per call): orchestrator validates the request's *values*
  against the registered schema — required slots present
  (`missing_required_input.<slot>` if not), values match declared types
  or contain unknown slot keys (`invalid_slot_type.<slot>` covers both —
  `<slot>` is the offending slot name, whether mistyped or unknown). All
  §5 abstain conditions for slot validation are runtime.

| Slot key | Type | Used by |
|---|---|---|
| `query_text` | string | `discover`, `synthesize_prose`, `brief_next_steps` |
| `rid` | string (record_id) | `extract`, `inspect_lineage` |
| `rid_set` | list[string] | `synthesize_prose`, `synthesize_table` |
| `rid_pair` | tuple[string, string] | `diff` (canonical; `rid_set` is NOT a valid `diff` input) |
| `paper_rid` | string | `critique_generate`, `critique_respond` |
| `reviewer_text_or_rid` | string \| record_id | `critique_respond` |
| `comparison_axes` | list[string] | `synthesize_table` |
| `latex_dir` | path | `contribute` |
| `text_blob` | string | `contribute` (LLM-mode bypass for pre-extracted text) |
| `pdf_path` | path | `contribute` (multimodal LLM reads PDF directly — most common real-world input) |
| `field_patches` | object | `revise_local` |
| `target_rid` | string (record_id) | `revise_local` (which sidecar to patch) |
| `q` | string | `extract` (the question to answer) |
| `local_path` | path | `extract` (alternative to `rid` — read local `.knows.yaml` file instead of hub fetch; canonical for "ask questions about my freshly-generated sidecar") |
| `local_path_a` | path | `diff` (alternative to first half of `rid_pair`) |
| `local_path_b` | path | `diff` (alternative to second half of `rid_pair`) |

### 1.4 `requested_artifact` allowed values

| Value | Skill produces |
|---|---|
| `ranked_paper_list` | Markdown table of search results |
| `bibtex` | `papers.bib` file (BibTeX entries) |
| `answer_json` | Single JSON object per `consume-prompt.md` v1.1 schema |
| `related_work_paragraph` | 1-3 paragraphs prose with `\cite{}` keys |
| `comparison_table` | Markdown + LaTeX `tabular` block |
| `diff_report` | Structured diff (shared/divergent/contradictory/relations) |
| `review_sidecar` | YAML file conforming to `profile: review@1` |
| `rebuttal_doc` | Per-comment Markdown response with citations |
| `next_step_brief` | Markdown brief with N candidate questions + supporting refs |
| `knows_yaml` | YAML file conforming to declared `profile` (default `paper@1`) |
| `lint_report` | Lint pass/fail summary |
| `version_chain_report` | Backward ancestry chain for one record |
| `diff_and_yaml` | Unified diff + new YAML file (revise_local output) |

Multiple artifacts in one request → **out of scope for v1** (see §7).

### 1.5 Routing Table (canonical, exhaustive)

This is the **canonical dispatch table**. Every legal `(intent_class,
required_inputs, requested_artifact)` tuple maps to exactly one row.
Tuples that do not match any row → `unknown_dispatch_tuple` abstain (§5).
Tuples matching >1 row → §4 clarification.

| `intent_class` | Required slots | `requested_artifact` | → skill |
|---|---|---|---|
| `discover` | `query_text` | `ranked_paper_list` | `paper-finder` |
| `discover` | `query_text` | `bibtex` | `paper-finder` |
| `extract` | `rid`, `q` | `answer_json` | `sidecar-reader` (hub-fetch mode) |
| `extract` | `local_path`, `q` | `answer_json` | `sidecar-reader` (local-file mode) |
| `synthesize_prose` | `query_text` OR `rid_set` | `related_work_paragraph` | `survey-narrative` |
| `synthesize_table` | `rid_set`, `comparison_axes` | `comparison_table` | `survey-table` |
| `diff` | `rid_pair` | `diff_report` | `paper-compare` (both-hub mode) |
| `diff` | `local_path_a`, `local_path_b` | `diff_report` | `paper-compare` (both-local mode) |
| `diff` | `rid`, `local_path_b` | `diff_report` | `paper-compare` (mixed: hub + local) |
| `critique_generate` | `paper_rid` | `review_sidecar` | `review-sidecar` |
| `critique_respond` | `paper_rid`, `reviewer_text_or_rid` | `rebuttal_doc` | `rebuttal-builder` |
| `brief_next_steps` | `query_text` | `next_step_brief` | `next-step-advisor` |
| `contribute` | `latex_dir` OR `text_blob` OR `pdf_path` | `knows_yaml` | `sidecar-author` |
| `contribute` | `latex_dir` OR `text_blob` OR `pdf_path` | `lint_report` | `sidecar-author` (lint-only branch) |
| `inspect_lineage` | `rid` | `version_chain_report` | `version-inspector` |
| `revise_local` | `target_rid`, `field_patches` | `diff_and_yaml` | `sidecar-reviser` |

Notes:

- "Required slots" entries with `OR` accept exactly one slot from the group;
  supplying any two members of the OR-group simultaneously is `invalid_slot_type`
  (§5). The `contribute` row has a 3-way OR (`latex_dir` / `text_blob` /
  `pdf_path`) — at most one may be present per request.
- `paper-finder` has two rows because the artifact differs; the skill body
  branches on `requested_artifact`.
- `sidecar-author` has two rows for the same reason: lint-only is a real
  workflow (validate without producing the full sidecar).
- `synthesize_prose` accepts either a query (skill runs `paper-finder`
  internally to retrieve) or a pre-supplied `rid_set` (skill skips
  retrieval).

---

## 2. Profile Filtering Pipeline (G7 implementation)

**Where it lives**: orchestrator's retrieval layer, *between* the API call
and the sub-skill's working set. **Never inside the skill body.**

### 2.1 Skill-side declaration (frontmatter)

Every sub-skill declares which profiles it accepts in its `SKILL.md`
frontmatter. Multi-profile skills declare typed co-input slots.

```yaml
# Single-profile skill
accepts_profiles: [paper@1]

# Multi-profile skill (rebuttal-builder)
co_inputs:
  paper: paper@1
  review: review@1
```

### 2.2 Orchestrator filter (pseudocode)

For single-input skills, hits are filtered as one pool. For
multi-input skills with `co_inputs`, each typed slot is filtered
independently and the result is a `dict[slot_name, list[record]]`.
Profile-drop and quality-drop are tracked separately so the abstain
reason in §5 is accurate.

```python
def filter_pool(records, allowed_profiles, quality_policy, manifest):
    """Filter ONE pool against profile + quality. Returns (kept, dropped_profile, dropped_quality)."""
    kept, dropped_profile, dropped_quality = [], [], []
    for h in records:
        prof = h.get("profile")  # may be None
        prof_reason = profile_filter_reason(h, allowed_profiles)  # None if OK
        if prof_reason is not None:
            dropped_profile.append({
                "rid": h.get("rid", "?"),
                "raw_profile": prof,
                "reason": prof_reason,  # missing | malformed | not_in_allowed
            })
            continue
        q_reason = quality_filter_reason(h, quality_policy)  # None if OK; else dict {policy_field, actual}
        if q_reason is not None:
            dropped_quality.append({
                "rid": h.get("rid", "?"),
                "policy_field": q_reason["policy_field"],
                "actual": q_reason["actual"],
            })
            continue
        kept.append(h)
    manifest.add_exclusions(dropped_profile, dropped_quality)  # populates §6 fields
    return kept, dropped_profile, dropped_quality


def build_working_set(skill, hits_or_slot_hits, manifest):
    """Filter retrieval hits against skill's profile + quality policy.
    Called BEFORE the skill body sees any record."""
    if skill.is_multi_input:  # has co_inputs declaration
        result = {}
        for slot_name, slot_profile in skill.co_inputs.items():
            slot_hits = hits_or_slot_hits[slot_name]  # already split per-slot upstream
            kept, _, _ = filter_pool(
                slot_hits, allowed_profiles={slot_profile},
                quality_policy=skill.quality_policy, manifest=manifest)
            if not kept:
                # Multi-input skill: ANY empty slot is a missing_co_input case,
                # regardless of underlying cause (profile vs quality vs no hits).
                # The §4 clarification flow runs at the abstain handler, not here.
                abstain(skill, reason=f"missing_co_input.{slot_name}", manifest=manifest)
            result[slot_name] = kept
        return result

    # Single-input skill: distinguish profile-drop from quality-drop.
    # Tie-breaker rule: if ANY record was dropped on profile grounds, the
    # working set is reported as profile-empty (more fundamental violation).
    # Quality reason only fires when ALL drops are quality-only.
    kept, prof_drop, qual_drop = filter_pool(
        hits_or_slot_hits, allowed_profiles=set(skill.accepts_profiles),
        quality_policy=skill.quality_policy, manifest=manifest)
    if not kept:
        if prof_drop:
            abstain(skill, reason="empty_working_set_after_profile_filter", manifest=manifest)
        elif qual_drop:
            abstain(skill, reason="empty_working_set_after_quality_filter", manifest=manifest)
        else:
            # No hits returned by API at all (search yielded nothing)
            abstain(skill, reason="empty_working_set_after_profile_filter", manifest=manifest)
    return kept
```

Both abstain reasons in §5 (`empty_working_set_after_profile_filter` and
`empty_working_set_after_quality_filter`) are reachable from this pseudocode.

**Rule (multi-input)**: any empty slot raises `missing_co_input.<slot_name>` —
the cause (profile-drop vs quality-drop vs no-hits) is recorded in the manifest
exclusion lists, but the abstain reason is uniform. §3.3 / §4 then run a single
clarification turn before final refusal.

**Tie-breaker (single-input)**: profile-drop dominates quality-drop. If any
record was excluded for profile reasons, the abstain reason is
`empty_working_set_after_profile_filter` even when other records were also
quality-dropped. Quality reason fires only when all drops are quality-only.

### 2.3 Edge-case defaults (registration-time vs runtime)

| Condition | Default | Manifest entry |
|---|---|---|
| Record has missing `profile` field | Exclude with reason; UNLESS skill declares `accepts_profiles: [unknown]` (explicit opt-in) | `excluded_missing_profile: [<rid>, ...]` |
| Record has malformed `profile` value (does not match `^[a-z_]+@\d+$`) | Exclude with reason; never coerce | `excluded_malformed_profile: [{rid, raw_value}, ...]` |
| Skill frontmatter `accepts_profiles` is missing/malformed/non-list | **Skill registration error** — orchestrator refuses to load the skill at startup. Not a runtime fallback. | (registration log, not run manifest) |
| Multi-input skill receives empty typed `co_input` slot (e.g. `review` slot empty for `rebuttal-builder`) | Single-turn clarification per §4; if unresolved, **abstain** with explicit refusal | `abstained_reason: missing_co_input.<slot_name>` |
| Working set empty after profile filter (every hit excluded) | Abstain with refusal naming the empty slot and the profile filter applied | `abstained_reason: empty_working_set_after_profile_filter` |

**No silent profile coercion or defaulting anywhere in the dispatch path.**

---

## 3. Typed Co-Input Slots (multi-profile skills)

Some skills require records of two different profiles in one call. The
canonical example is `rebuttal-builder`, which needs both the paper being
rebutted (`paper@1`) and the review being responded to (`review@1` or raw
text).

### 3.1 Frontmatter schema

```yaml
co_inputs:
  <slot_name>: <profile@version>
  <slot_name>: <profile@version>
```

- `<slot_name>` is a string identifier the skill body uses to reference the
  slot (e.g. `paper`, `review`).
- `<profile@version>` matches the same `^[a-z_]+@\d+$` pattern as record
  profiles. The literal sentinel `unknown` is **reserved** and exempt
  from this pattern — it may appear in a skill's `accepts_profiles` list
  to opt the skill into receiving records with missing `profile` fields
  (per §2.3). `unknown` is NOT a valid profile value on records
  themselves.
- Slots are filtered independently against the API result set.
- A skill body NEVER sees a mixed-profile pool; each slot receives only
  records matching its declared profile.

### 3.2 Registration-time validation

Orchestrator validates frontmatter at skill load time:
- `co_inputs` is a non-empty object → required for any skill that declares it
- Each value matches the profile regex → reject otherwise
- Slot names are unique within the skill → reject duplicates
- Slot names are valid identifiers (`^[a-z_][a-z0-9_]*$`) → reject otherwise

Failure to validate is a **skill registration error**: the orchestrator
refuses to load the skill, logs the reason, and continues without it.

### 3.3 Runtime: empty slot handling

If a `co_inputs` slot is empty after profile filtering (no matching
records), orchestrator:
1. Emits the §4 clarification turn naming the empty slot.
2. If reply does not provide the missing input, **abstains** with
   `abstained_reason: missing_co_input.<slot_name>`.
3. **Never** silently degrades to a single-input mode by dropping the empty
   slot.

### 3.4 Full registration schema (frontmatter fields beyond profile)

The fields in §3.1 (`accepts_profiles` / `co_inputs`) cover G7 (Profile
Discipline) only. Each sub-skill's frontmatter MUST also declare the fields
below to bind the orchestrator's other guards. The full schema is
authoritative; SKILL.md summaries that drift from this section lose.

**Required for every sub-skill:**

```yaml
quality_policy:               # G2' enforcement; orchestrator filters on these BEFORE the skill body sees the working set
  require_lint_passed: true   # bool, REQUIRED — when true, drop records with lint_passed=false
  allowed_coverage:           # list[enum], REQUIRED, non-empty — record's coverage.statements must be in this set
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5           # int, REQUIRED, ≥0 — drop records with fewer statements than this
```

> **Removed v1.0**: an earlier draft of `quality_policy` included
> `allow_unverified_metadata`, but the canonical `knows-record-0.9.json` schema
> exposes no field that records whether `verify_metadata.py` was run, so the
> filter could not be applied deterministically. Re-add the field only after
> the schema gains a `metadata_verified` flag (or equivalent). Until then,
> `verify_metadata.py` remains a sub-skill-internal utility, not an
> orchestrator-level filter.

**Optional for every sub-skill:**

```yaml
requires_full_record: false   # bool, OPTIONAL, default false. When true, G3 fetch-planner uses GET /sidecars/<rid> for every record instead of partial fetch. Use only when the skill body genuinely needs the full record (e.g. paper-compare needs relations, sidecar-reader may need evidence).
```

**Conditional (REQUIRED iff ANY of the skill's routed artifacts is a sidecar):**

```yaml
emits_profile: paper@1        # profile@version, REQUIRED whenever ANY row in §1.5 mapping to this skill has a sidecar-typed requested_artifact (knows_yaml, review_sidecar, or diff_and_yaml). Skills with mixed routes — e.g. sidecar-author maps to both knows_yaml AND lint_report — declare emits_profile once at skill level, applying to the sidecar route(s) only; non-sidecar routes ignore it.
                              # Allowed values: any value matching ^[a-z_]+@\d+$ that the orchestrator recognizes; literal `unknown` is NOT permitted here (it is reserved for accepts_profiles only).
                              # Read-only skills (every routed artifact is non-sidecar) MUST omit this field.
```

**Validation rules** (registration-time, per §3.2 mechanics):

| Field | Validation | Failure → |
|---|---|---|
| `quality_policy` | Must be present + object-typed | `skill_unregistered.<skill_name>` |
| `quality_policy.require_lint_passed` | Must be present + bool | `skill_unregistered.<skill_name>` |
| `quality_policy.allowed_coverage` | Must be present + non-empty list, every value ∈ canonical schema's `coverage.statements` enum (`exhaustive`, `main_claims_only`, `key_claims_and_limitations`, `partial`) | `skill_unregistered.<skill_name>` |
| `quality_policy.min_statements` | Must be present + int + ≥0 | `skill_unregistered.<skill_name>` |
| `requires_full_record` | If present, must be bool | `skill_unregistered.<skill_name>` |
| `emits_profile` | If ANY of the skill's §1.5 routes has a sidecar-typed `requested_artifact` (`knows_yaml`, `review_sidecar`, `diff_and_yaml`), MUST be present, match `^[a-z_]+@\d+$`, NOT be `unknown` | `skill_unregistered.<skill_name>` |
| `emits_profile` | If NONE of the skill's §1.5 routes are sidecar-typed (i.e. read-only skills), MUST be absent | `skill_unregistered.<skill_name>` |

**Cross-section invariants:**

- `quality_policy.allowed_coverage` enum values are tied to the canonical
  schema (`knows-record-0.9.json`'s `coverage.statements` enum). Any value
  not in that enum is a registration error — orchestrator does not invent
  coverage levels.
- `requires_full_record: true` triggers a manifest field
  `fetch_mode_per_rid` (per §6.2) where every entry is `"full"` for that
  skill's working set. With default false, entries are `"partial:<section>"`.
- `emits_profile` is the inverse of `accepts_profiles` for a producer:
  the value declared here SHOULD be present in some downstream consumer's
  `accepts_profiles` list. Orchestrator does not enforce this end-to-end
  (consumer skills may not yet exist), but registration logs a warning
  if no registered consumer accepts the declared `emits_profile`.

**Worked example — `sidecar-author` (writes `paper@1` on `knows_yaml` route + emits `lint_report` on lint-only route):**

```yaml
accepts_profiles: []                  # does not consume from hub; takes latex_dir|text_blob input
quality_policy:
  require_lint_passed: false          # the artifact being authored is the OUTPUT, not a prerequisite
  allowed_coverage: [exhaustive, main_claims_only, key_claims_and_limitations, partial]
  min_statements: 0
requires_full_record: false
emits_profile: paper@1                # required because at least one §1.5 route emits a sidecar (knows_yaml); applies only to that route
```

**Worked example — `sidecar-reader` (reads `paper@1`, produces `answer_json` — read-only):**

```yaml
accepts_profiles: [paper@1]
quality_policy:
  require_lint_passed: true
  allowed_coverage: [exhaustive, main_claims_only, key_claims_and_limitations]
  min_statements: 5
requires_full_record: true            # consume-prompt v1.1 needs full record for evidence anchoring
# emits_profile omitted — every routed artifact (answer_json) is non-sidecar
```

**Worked example — `rebuttal-builder` (multi-input, produces `rebuttal_doc` — read-only):**

```yaml
co_inputs:
  paper: paper@1
  review: review@1
quality_policy:
  require_lint_passed: true
  allowed_coverage: [exhaustive, main_claims_only, key_claims_and_limitations]
  min_statements: 5
requires_full_record: false
# emits_profile omitted — every routed artifact (rebuttal_doc) is non-sidecar
```

---

## 4. Clarification Protocol

When the dispatch tuple does not uniquely select a row in §1.5's routing
table, the orchestrator does NOT guess and does NOT default. It clarifies
once, then either routes or abstains.

### 4.1 Clarification format

A single-turn message to the user enumerating:
1. The candidate skills that could match
2. The input-contract gap that prevents disambiguation
3. The minimal additional input needed to resolve

Example for "what are the weaknesses of paper X?":

```
This query is ambiguous. Candidate skills:
(a) extract weaknesses already stated in paper X's sidecar [sidecar-reader]
(b) generate a fresh peer review of paper X [review-sidecar]
(c) compare X's weaknesses against paper Y [paper-compare, requires Y]
(d) draft a response to a reviewer who criticized X [rebuttal-builder, requires reviewer text]

Please specify whether you want extraction, fresh review, pairwise diff,
or response draft.
```

### 4.2 What counts as a resolving reply

A reply resolves the ambiguity iff it provides enough information to
deterministically select **exactly one row** from §1.5's routing table.
Specifically:
- Names a skill that has **only one row** in §1.5 (e.g. `sidecar-reader`,
  `version-inspector`); skills with multiple rows (e.g. `paper-finder` with
  two artifact branches, `sidecar-author` with knows_yaml vs lint_report)
  require the reply to ALSO name the `requested_artifact`, OR
- Specifies an `intent_class` value from §1.2 sufficient to pick one row
  given the original `required_inputs` and `requested_artifact`, OR
- Provides the missing `required_inputs` slot that uniquely identifies one
  candidate, OR
- Provides the missing `requested_artifact` value that uniquely identifies
  one candidate among rows sharing the same `intent_class` + slots

Anything else (vague text, repeating the original query, off-topic reply,
or naming a multi-row skill without specifying the artifact) **does not
resolve** the ambiguity.

### 4.3 Abstain on unresolved clarification

If the user's reply does not resolve the tuple to a single row, the
orchestrator emits a structured refusal:

```
{
  "abstained": true,
  "abstained_reason": "ambiguous_dispatch_unresolved_after_clarification",
  "candidates": ["sidecar-reader", "review-sidecar", "paper-compare", "rebuttal-builder"],
  "unresolved_field": "intent_class",
  "manifest_path": "/path/to/manifest.json"
}
```

**There is no "most-read-only default."** Ambiguity is a refusal condition,
not a routing condition. Re-asking from the user is a separate call.

### 4.4 Bounded clarification

The orchestrator clarifies **exactly once** per dispatch attempt. No
recursive clarification chains. If the user wants to issue a new clarified
query, that is a fresh dispatch from their side.

---

## 5. Abstain Conditions (Exhaustive)

The orchestrator MUST abstain (emit structured refusal, never silently
proceed) on every condition listed below. This list is exhaustive: any
condition not listed proceeds to the skill.

| Condition | `abstained_reason` |
|---|---|
| Dispatch tuple maps to no row in §1.5 routing table | `unknown_dispatch_tuple` |
| Dispatch tuple maps to >1 row AND clarification unresolved | `ambiguous_dispatch_unresolved_after_clarification` |
| User requested >1 artifact in one call (multi-artifact composition) | `multi_artifact_request_rejected` |
| `required_inputs` missing one or more declared slots | `missing_required_input.<slot_name>` |
| `required_inputs` slot value has wrong type (string where list expected; both `OR` slots supplied; OR request contains unknown slot key not declared by skill) | `invalid_slot_type.<slot_name>` |
| `co_inputs` slot empty after profile filtering | `missing_co_input.<slot_name>` |
| API returned ZERO hits before any filter (e.g. search query too narrow) | `upstream_zero_hits` |
| Working set empty after profile filter (API returned hits but every one had wrong/missing profile) | `empty_working_set_after_profile_filter` |
| Working set empty after quality filter (every hit failed quality_policy) | `empty_working_set_after_quality_filter` |
| Skill not registered (frontmatter validation failed at startup) | `skill_unregistered.<skill_name>` |
| Skill declared `requires_full_record: true` but API returned only partial | `partial_record_unavailable_for_full_fetch_skill` |
| User-supplied `rid` does not exist on hub (API returns 404) | `rid_not_found.<rid>` |
| `POST /sidecars` (upload) called while `KNOWS_API_KEY` unset OR endpoint UNVERIFIED | `upload_disabled_endpoint_unverified` |
| API response is malformed JSON / fails schema validation | `upstream_response_malformed` |
| API call exhausted retries (G5 backoff budget) | `upstream_unavailable_retries_exhausted` |
| Skill body raises uncaught exception during execution | `skill_runtime_exception.<exception_class>` |

Every abstain emits a manifest pointer (see §6).

---

## 6. Manifest Schema

Every multi-record run emits a `manifest.json` file. The path is
referenced from the produced artifact (e.g. as a Markdown footnote, a
`provenance.manifest_ref` field on a generated sidecar, or a CLI stderr
line). Without manifest, runs are not reproducible.

### 6.1 Required fields (writers documented inline)

Every required field has at least one writer in the documented control
flow. If a writer doesn't exist for an MVP-scope skill, the field is
optional with default `null` or `[]`.

```jsonc
{
  "knows_api_version":     "0.9.0",            // WRITER: G5 transport layer pins this from /jobs/stats on first call
  "skill":                 "paper-finder",      // WRITER: orchestrator dispatch entry
  "started_at":            "2026-04-25T22:30:00Z",   // WRITER: orchestrator dispatch entry
  "ended_at":              "2026-04-25T22:30:42Z",   // WRITER: orchestrator dispatch exit (success OR abstain)
  "queries":               ["diffusion + privacy"],   // WRITER: §1.5 router populates from required_inputs.query_text; [] if no search step
  "returned_rids":         ["knows:foo/1.0"],   // WRITER: G5 transport layer, every API hit before filter
  "applied_profile_filters": ["paper@1"],      // WRITER: orchestrator. Single-input skill: list[profile] from skill.accepts_profiles. Multi-input skill: dict[slot_name, profile] from skill.co_inputs (preserves slot identity), e.g. {"paper": "paper@1", "review": "review@1"}.
  "applied_quality_policy": {                  // WRITER: orchestrator from skill.quality_policy frontmatter
    "require_lint_passed": true,
    "allowed_coverage": ["exhaustive", "main_claims_only"],
    "min_statements": 5
  },
  "excluded_missing_profile":   ["knows:bar/1.0"],   // WRITER: §2.2 filter_pool dropped_profile (reason=missing)
  "excluded_malformed_profile": [{"rid": "...", "raw_value": "weird"}],  // WRITER: §2.2 dropped_profile (reason=malformed)
  "quality_exclusions":         [{"rid": "...", "policy_field": "min_statements", "actual": 2}],  // WRITER: §2.2 dropped_quality
  "abstained":                  false,         // WRITER: §5 abstain() function
  "abstained_reason":           null           // WRITER: §5 abstain() function; non-null iff abstained=true
}
```

### 6.2 Optional fields (no MVP writer)

These fields are reserved in the manifest schema but have no writer in
v1 — present as `null` or empty until G5/G6 implementations land in v1.x:

| Field | Type | Future writer (when) |
|---|---|---|
| `fetch_mode_per_rid` | `dict[rid, "partial:<section>" \| "full"]` | G5 transport layer (v1.0 ships) |
| `truncation_flags` | `list[rid]` | G5 transport layer (v1.0) |
| `cache_hits` | `list[rid]` | G5 cache layer (v1.0) |
| `dispatch_tuple` | `(intent_class, slots, artifact)` | Orchestrator dispatch entry (v1.0) |
| `clarification_emitted` | `bool` | §4 clarification path (v1.0) |
| `clarification_resolved` | `bool` | §4 reply handler (v1.0) |
| `model` | `string` | Skill body (skill-specific) |
| `token_cost_estimate` | `int` | Skill body / LLM call wrapper (v1.x) |
| `runtime_exception_class` | `string` | §5 exception handler (v1.0) |

### 6.3 Manifest path convention

- CLI runs: `<output_dir>/manifest.json` alongside the produced artifact
- Library calls: returned as a field on the response object
- Generated sidecars: `provenance.manifest_ref` field on the YAML record

---

## 7. MVP Scope Boundary

This section is **load-bearing**. Every contributor must read it before
extending the orchestrator.

### 7.1 v1 supports exactly one atomic artifact per request

The dispatch tuple `(intent_class, required_inputs, requested_artifact)`
carries a single `requested_artifact` value. v1 does NOT support compound
requests like:

> "Find the top 8 papers on diffusion privacy, give me a related-work
> paragraph, and a comparison table of datasets and metrics."

That request needs at least three skills (`paper-finder` →
`survey-narrative` + `survey-table`) plus shared working-set propagation
between them. That is a **planner/decomposer layer**, not a router.

### 7.2 Multi-artifact planner is out of scope

Planning across skills, sharing a working set, and composing artifacts
from chained sub-skill outputs is **explicitly out of scope for v1**.

When a user issues a compound request:
- Orchestrator detects the multi-artifact shape
- Emits a structured refusal: `multi_artifact_request_rejected`
- Logs to manifest
- Suggests the user decompose into sequential single-artifact calls

This is not a feature gap to apologize for. It is an architectural
decision: planner-layer correctness requires its own contract (planning
semantics, partial-failure handling, working-set propagation), and we
explicitly defer it to v2 to ship v1 honestly.

### 7.3 What v1 validates

v1 validates the **executor shell**:
- Dispatch tuple → skill routing
- Profile filtering pipeline
- Quality policy enforcement
- Manifest emission
- Single-skill artifact production

### 7.4 What v1 does NOT validate

- Multi-artifact composition (deferred to v2)
- Cross-skill working-set propagation (deferred to v2)
- Long-running async dispatch (deferred to v2)
- POST endpoints (`/sidecars` upload, `/generate/pdf`) — UNVERIFIED upstream

### 7.5 Integration test fixtures (required for v1 ship)

Three fixtures land in the same sprint as v1 public skills, exercising
plumbing not covered by the public skill surface:

1. `tests/fixture_mixed_profile_retrieval/` — G7 + §2 + §3 enforcement
2. `tests/fixture_quality_exclusion_logging/` — G2' + §6 manifest visibility
3. `tests/fixture_dispatch_clarify_and_abstain/` — §4 + §5 routing semantics

CI green on all three is a **hard prerequisite** for tagging v1 release.

---

## 8. Versioning of This Contract

This document is the orchestrator's load-bearing contract. Changes to it
are versioned and reviewed.

- **Patch version** (clarifications, typo fixes, additional examples): no
  backward-compat impact, no skill changes required.
- **Minor version** (new optional fields, new `intent_class` value, new
  abstain condition): backward-compatible additions; existing skills
  continue to work without changes.
- **Major version** (changes to existing tuple semantics, removal of
  fields, change of default behavior): **breaking**. All sub-skills must
  be re-validated against the new version before the orchestrator is
  bumped.

Any PR touching this file MUST:
1. Re-run all three integration test fixtures (§7.5) and confirm green
2. State the version bump category in the PR description
