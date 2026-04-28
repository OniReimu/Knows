---
name: knows-sidecar-reviser
description: "Update a small whitelist of fields on an existing local sidecar — version number, status (active/superseded/retracted/draft/deprecated), freshness date, or 'replaces' link to a prior version. Triggers: 'this sidecar got replaced by a newer version', 'mark my sidecar as superseded', 'update the version number', 'bump to v1.1', 'set freshness to today', 'point this sidecar at the old one as its predecessor', 'my paper got retracted, mark it'. Whitelist-only — does NOT edit statements, evidence, or claims (those need a regenerate via sidecar-author)."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: revise_local
required_inputs:
  - target_rid                      # record_id of the sidecar being revised (used to derive output filename + provenance)
  - field_patches                   # dict of {whitelisted_field: new_value} — see whitelist below

requested_artifacts:
  - diff_and_yaml                   # unified-diff + new YAML file

# Profile contract — G7 (revising paper@1 only in v1.2; review@1 reviser v1.x+)
accepts_profiles: [paper@1]

# Quality policy — G2' (revise input record can have any quality; revision is metadata-only)
quality_policy:
  require_lint_passed: true         # must lint-pass to be revisable; broken sidecars need fixing first
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
    - partial
  min_statements: 0

# Fetch-planner — G3 (revise needs full record to construct diff)
requires_full_record: true

# emits_profile omitted — diff_and_yaml is a structural diff + revised file, not a NEW sidecar artifact in the profile sense (the profile is unchanged from input)
---

# sidecar-reviser — Whitelist-only local patcher

**Hard non-goals**:

- MUST NOT edit fields outside the whitelist `{version.record, replaces, record_status, freshness.as_of, provenance.revised_by}`.
- MUST NOT rewrite, merge, or paraphrase `statements`, `evidence`, or `relations` content.
- MUST NOT mark prior records as `superseded` or mutate any RID other than the one being authored.
- MUST NOT issue uploads or call `POST /sidecars` directly — handoff to `sidecar-author`'s gated path.
- MUST NOT produce a record whose `replaces` self-references or creates an immediate chain cycle.
- MUST NOT certify governance correctness, authority, or canonicality of the resulting record.

This is a **mechanical patcher** with value validation, not a content editor. Use `sidecar-author` to write a new sidecar from scratch.

## Whitelist + value validation

Each whitelisted field has a strict validator (per dispatch-and-profile.md §1 hard non-goals):

| Field | Validator |
|---|---|
| `record_status` | enum ∈ `{active, superseded, retracted, draft, deprecated}` |
| `freshness.as_of` | ISO-8601 date `YYYY-MM-DD` (regex `^\d{4}-\d{2}-\d{2}$`) |
| `version.record` | semver-like `^\d+\.\d+(\.\d+)?$` |
| `replaces` | syntactically valid `record_id` AND ≠ `target_rid` AND not already in current `replaces` chain (no immediate cycle) |
| `provenance.revised_by` | non-empty string ≤256 chars |

On any validation failure: abort with non-zero exit, reason to stderr, write nothing. **No partial-edit YAML ever leaves the skill.**

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_sidecar, Manifest
import re, yaml, copy, difflib

TARGET_RID = "knows:vaswani/attention/1.0.0"
PATCHES = {
    "version.record": "1.1.0",
    "freshness.as_of": "2026-04-26",
    "replaces": "knows:vaswani/attention/1.0.0",         # would actually need an OLDER rid; this is a self-ref → REJECT
    "provenance.revised_by": "Saber Yu (knows-sidecar-reviser)",
}

# 1. Dispatch tuple
decision = dispatch("revise_local", {"target_rid": TARGET_RID, "field_patches": PATCHES}, "diff_and_yaml")
assert decision["action"] == "route"

# 2. Fetch original sidecar (or load from local path if user supplies one — local-path slot v1.x)
manifest = Manifest(skill="sidecar-reviser", intent_class="revise_local",
                    dispatch_tuple="(revise_local,{target_rid,field_patches},diff_and_yaml)",
                    returned_rids=[TARGET_RID])
original = fetch_sidecar(TARGET_RID)
manifest.fetch_mode_per_rid[TARGET_RID] = "full"

# 3. VALIDATE every patch BEFORE applying any
RECORD_STATUS_ENUM = {"active", "superseded", "retracted", "draft", "deprecated"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")
RID_RE = re.compile(r"^knows:[a-z0-9_/.-]+/\d+\.\d+(\.\d+)?$")
WHITELIST = {"record_status", "freshness.as_of", "version.record", "replaces", "provenance.revised_by"}

for path, new_val in PATCHES.items():
    if path not in WHITELIST:
        print({"abstained": True, "reason": f"invalid_slot_type.field_patches",
               "detail": f"field '{path}' not in whitelist"}); raise SystemExit
    if path == "record_status" and new_val not in RECORD_STATUS_ENUM:
        raise SystemExit(f"INVALID record_status: {new_val}")
    if path == "freshness.as_of" and not DATE_RE.match(str(new_val)):
        raise SystemExit(f"INVALID date: {new_val}")
    if path == "version.record" and not SEMVER_RE.match(str(new_val)):
        raise SystemExit(f"INVALID semver: {new_val}")
    if path == "replaces":
        if not RID_RE.match(str(new_val)):
            raise SystemExit(f"INVALID rid: {new_val}")
        if new_val == TARGET_RID:
            raise SystemExit(f"INVALID: replaces == target_rid (self-ref)")
        if new_val in (original.get("replaces"),):
            raise SystemExit(f"INVALID: would create immediate cycle")
    if path == "provenance.revised_by":
        if not isinstance(new_val, str) or not new_val.strip() or len(new_val) > 256:
            raise SystemExit(f"INVALID provenance.revised_by")

# 4. Apply patches to a copy (deep) — set nested keys
revised = copy.deepcopy(original)
def set_path(d, dotted, val):
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = val
for path, val in PATCHES.items():
    set_path(revised, path, val)

# 5. Render unified diff + new YAML
orig_yaml = yaml.dump(original, sort_keys=False)
rev_yaml = yaml.dump(revised, sort_keys=False)
diff = "\n".join(difflib.unified_diff(orig_yaml.splitlines(), rev_yaml.splitlines(),
                                        fromfile="original", tofile="revised", lineterm=""))
out_path = f"/tmp/{TARGET_RID.replace(':','_').replace('/','_')}_revised.knows.yaml"
with open(out_path, "w") as fp: fp.write(rev_yaml)

# 6. Re-lint to confirm patches preserved validity
from orchestrator import run_sidecar_author_postgen
result = run_sidecar_author_postgen(out_path, out_path, include_cited=False)
assert result["lint_passed"], result["lint_output"]

print({"diff": diff, "output_path": out_path, "manifest": manifest.finish()})
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `diff_and_yaml` | Unified diff (original → revised) + path to new YAML file (`*_revised.knows.yaml`); both lint-pass guaranteed |

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `target_rid` or `field_patches` slot missing | `missing_required_input.<slot>` |
| `field_patches` is not a dict / contains non-whitelisted key | `invalid_slot_type.field_patches` |
| `target_rid` 404s | `rid_not_found.<rid>` |
| Original record fails G7/G2' (e.g. lint-broken) | `empty_working_set_after_quality_filter` |
| Any validator fails (enum / regex / self-ref / cycle) | `invalid_slot_type.field_patches` (with detail naming the offending field) |
| Re-lint of revised YAML fails | `skill_runtime_exception.RevisionBreaksLint` (extremely unlikely given whitelist scope, but possible if value injection breaks YAML parsing) |

## Upload handoff

Sidecar-reviser does NOT upload. After producing the new YAML, the user explicitly invokes `sidecar-author` (with `latex_dir` or appropriate input) to publish the revision via `POST /sidecars`. **In v1.0 the upload step is DEFERRED** (`upload_disabled_endpoint_unverified`).

## Manifest emission

Per G6 + G4: `skill: sidecar-reviser`, `intent_class: revise_local`, `dispatch_tuple`, `returned_rids: [target_rid]`, `fetch_mode_per_rid: {target_rid: "full"}`, plus skill-specific `applied_patches: [field_names]`, `governance_disclaimer: "Local revision only — does NOT certify canonicality or update the hub registry"`.

## Out of scope (locked, never)

- Editing statement/evidence/relation content — that's `sidecar-author` re-write, not revision.
- Bulk patches across multiple sidecars — one rid per call.
- Auto-detect "what should bump" (e.g. "did this evidence change since v1.0?") — agent must specify exact patches.
- Marking prior records as `superseded` (mutating their state) — only the new record's `replaces` field is set; old record is unchanged on hub.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
