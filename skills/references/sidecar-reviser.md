# sidecar-reviser — Reference Contract

**Status**: v1.0. Whitelist-only mechanical patcher with strict per-field value validation.

> **Companion**: `sub-skills/sidecar-reviser/SKILL.md`. Contract wins on disagreement.

---

## 1. Purpose and scope

Patch a small whitelist of metadata fields on an existing `paper@1` sidecar (version bump, mark superseded, refresh `as_of`, set `replaces` edge, record reviser). Output: deterministic unified-diff + new YAML file (lint-pass guaranteed).

**Out of scope (load-bearing)**:

- Editing statement / evidence / relation **content** — that's `sidecar-author` re-write, not revision.
- Bulk patches across multiple sidecars — one rid per call.
- Auto-detection of "what should bump" — agent must specify exact patches.
- Marking prior records as `superseded` (mutating their state on the hub) — only the new record's `replaces` field is set.
- Uploading the revised sidecar — handoff to `sidecar-author`'s gated upload (DEFERRED in v1.0).
- Certifying canonicality / authority of the resulting record.

---

## 2. Whitelist (load-bearing)

ONLY these 5 dotted-path fields may be patched:

| Field | Type | Validator |
|---|---|---|
| `record_status` | enum string | ∈ `{active, superseded, retracted, draft, deprecated}` |
| `freshness.as_of` | string | matches `^\d{4}-\d{2}-\d{2}$` (ISO-8601 date) OR `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` (full ISO-8601 datetime UTC) |
| `version.record` | string | matches `^\d+\.\d+(\.\d+)?$` (semver-like, optional patch) |
| `replaces` | string (record_id) | matches `^knows:[a-z0-9_/.-]+/\d+\.\d+(\.\d+)?$` AND not equal to current record's `record_id` (no self-ref) AND not already in current record's `replaces` chain (no immediate cycle) |
| `provenance.revised_by` | string | non-empty after strip, ≤ 256 chars |

**Any patch attempting to write outside this whitelist** → `invalid_slot_type.field_patches` with detail naming the offending field.

---

## 3. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `target_rid` | record_id | yes | The sidecar being revised; orchestrator fetches via G5 |
| `field_patches` | dict[whitelist_field, value] | yes | Non-empty; 1-5 patches typical |
| `output_path` | string (file path) | no | Default: `<target_rid_slug>_revised.knows.yaml` in tmp dir |

---

## 4. Output schema

```jsonc
{
  "target_rid": "knows:author/title/1.0.0",
  "applied_patches": {
    "version.record": "1.1.0",
    "freshness.as_of": "2026-04-26",
    "provenance.revised_by": "Saber Yu (knows-sidecar-reviser)"
  },
  "diff": "--- original\n+++ revised\n@@ ... @@\n- ...\n+ ...",   // unified diff text
  "output_path": "/tmp/.../sidecar_revised.knows.yaml",
  "lint_passed": true,
  "lint_warnings": <int>,
  "manifest_path": "<path>",
  "governance_disclaimer": "Local revision only — does NOT certify canonicality, does NOT update the hub registry, does NOT mutate prior records' state. Upload handoff via sidecar-author (DEFERRED in v1.0)."
}
```

The `governance_disclaimer` is mandatory and verbatim per G4. It signals that this skill does not fulfill the "governance" role its name might imply.

---

## 5. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `target_rid` slot missing | `missing_required_input.target_rid` |
| `field_patches` slot missing or empty dict | `missing_required_input.field_patches` |
| `field_patches` is not a dict (e.g. list) | `invalid_slot_type.field_patches` |
| `field_patches` contains any non-whitelist key | `invalid_slot_type.field_patches` (detail: offending key) |
| `target_rid` 404s | `rid_not_found.<rid>` |
| Original record fails G7/G2' (e.g. lint-broken record) | `empty_working_set_after_quality_filter` |
| Any validator fails (enum / regex / self-ref / cycle / length) | `invalid_slot_type.field_patches` (detail: offending field + reason) |
| Re-lint of revised YAML fails | `skill_runtime_exception.RevisionBreaksLint` |

**Validation runs BEFORE any mutation**. If any patch fails its validator, the entire revision is aborted; no partial file is written.

---

## 6. Apply algorithm (canonical)

```python
WHITELIST = {"record_status", "freshness.as_of", "version.record", "replaces", "provenance.revised_by"}

# 1. Validate every patch BEFORE mutation
for path, value in field_patches.items():
    if path not in WHITELIST:
        return abstain("invalid_slot_type.field_patches", f"{path} not in whitelist")
    validate(path, value, original_record)   # raises on validator failure

# 2. Apply patches to a deep copy
revised = copy.deepcopy(original_record)
for path, value in field_patches.items():
    set_dotted_path(revised, path, value)    # creates intermediate dicts as needed

# 3. Write new YAML
with open(output_path, "w") as fp:
    yaml.dump(revised, fp, sort_keys=False, allow_unicode=True, default_flow_style=False)

# 4. Re-lint to ensure validity preserved
lint_result = lint(output_path)
if not lint_result.passed:
    return abstain("skill_runtime_exception.RevisionBreaksLint", lint_result.errors)

# 5. Compute unified diff
orig_yaml = yaml.dump(original_record, ...)
rev_yaml = yaml.dump(revised, ...)
diff = unified_diff(orig_yaml.splitlines(), rev_yaml.splitlines(),
                    fromfile="original", tofile="revised")

# 6. Return result
```

**Determinism**: YAML output uses `sort_keys=False` (preserves field order) and `default_flow_style=False` (block style, no inline). Same input + patches → byte-identical output.

---

## 7. Specific validator rules

### 7.1 `record_status` enum

```
ALLOWED = {"active", "superseded", "retracted", "draft", "deprecated"}
```

These match `knows-record-0.9.json`'s `record_status` enum. Any change to the canonical schema enum requires a synchronized update to this validator (versioned event).

### 7.2 `freshness.as_of` date format

Two acceptable shapes (per canonical schema):
- Date-only: `^\d{4}-\d{2}-\d{2}$` (e.g. `2026-04-26`)
- Full datetime UTC: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` (e.g. `2026-04-26T03:00:00Z`)

Date-with-non-UTC-offset (e.g. `2026-04-26T03:00:00+10:00`) is REJECTED — orchestrator normalizes to UTC.

### 7.3 `version.record` semver-like

```
^\d+\.\d+(\.\d+)?$
```

Patch component optional. Examples accepted: `1.0`, `1.0.0`, `2.13.42`. Rejected: `v1.0`, `1.0.0-beta`, `1`.

### 7.4 `replaces` cycle / self-ref check

```
new_replaces = patch_value
if new_replaces == original_record["record_id"]:
    REJECT  # self-reference
if new_replaces == original_record.get("replaces"):
    REJECT  # immediate cycle (would repoint to current parent)
```

The check is shallow — it does not walk the full ancestry chain (that's `version-inspector`'s job). Deep-cycle detection requires fetching the proposed `replaces` rid and walking its chain, which is out of scope for a mechanical patcher.

### 7.5 `provenance.revised_by` content

```
isinstance(value, str) and value.strip() and len(value) <= 256
```

Empty-string / whitespace-only / over-long → REJECT. The field is meant to identify the human or tool performing the revision (e.g. `"Saber Yu (knows-sidecar-reviser)"`).

---

## 8. Manifest emission contract

```jsonc
{
  "skill": "sidecar-reviser",
  "intent_class": "revise_local",
  "dispatch_tuple": "(revise_local,{target_rid,field_patches},diff_and_yaml)",
  "returned_rids": [<target_rid>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* frontmatter */ },
  "fetch_mode_per_rid": {<target_rid>: "full"},
  /* skill-specific */
  "applied_patches": [<list of patched field names>],
  "patches_attempted": [<all input patch field names, in case some were skipped>],
  "lint_passed_after_revision": <bool>,
  "lint_warnings_after_revision": <int>,
  "governance_disclaimer": "<verbatim G4 string above>"
}
```

---

## 9. Why this contract is load-bearing

Sidecar revisions are metadata operations that look mundane but have downstream consequences. A revised record with the wrong `replaces` value can break `version-inspector`'s ancestry walk for everyone who tries to query it. A `record_status` change to `retracted` without proper authority signals to consumers that the science is invalidated.

The whitelist + per-field validators + abort-on-violation make the skill safe by construction:

- No content edits → no risk of corrupting claims or evidence.
- No upload → no risk of polluting the hub.
- Validators catch all the obvious cycle/format errors before they reach the YAML.
- Re-lint after revision catches any second-order schema breaks.
- Deterministic diff lets users audit the change.

The skill is intentionally under-powered relative to a "general sidecar editor", because general editing is what `sidecar-author` is for (full re-generation).

