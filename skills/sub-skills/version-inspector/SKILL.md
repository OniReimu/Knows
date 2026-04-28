---
name: knows-version-inspector
description: "Walk a sidecar's `replaces` chain backward to show the full version history — each ancestor's version number, status (active/superseded/retracted/etc.), and freshness date. Triggers: 'what's the version history of this sidecar', 'show the lineage of this paper's record', 'has this sidecar been superseded', 'is this the current version of X', 'what versions came before this one', 'trace the predecessors of this record'. Backward-only — does NOT discover newer versions or sibling records (the `replaces` field only links to predecessors)."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: inspect_lineage
required_inputs:
  - rid                             # the record_id whose declared `replaces` chain to walk

requested_artifacts:
  - version_chain_report            # backward chain table with cycle / break detection

# Profile contract — G7 (paper@1 only in v1.2; review@1 lineage v1.x+)
accepts_profiles: [paper@1]

# Quality policy — G2' (lineage tracing doesn't need rich content; only chain-walk fields)
quality_policy:
  require_lint_passed: true
  allowed_coverage:
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
    - partial                        # lineage works on partial-coverage records too
  min_statements: 0                  # don't filter by content count for inspection

# Fetch-planner — G3 (need full record per hop to get `replaces` field; partial doesn't expose it)
requires_full_record: true

# emits_profile omitted — version_chain_report is structured text, not a sidecar artifact (read-only)
---

# version-inspector — Backward ancestry tracer

**Hard non-goals**:

- MUST NOT discover forward `superseded_by` from `GET /search`. Forward view is `unavailable`.
- MUST NOT infer "latest / newest / canonical" via heuristic ranking on `version.record`, `freshness.as_of`, or any timestamp. Latest-status asserted only by an explicit `replaces` edge from a successor.
- MUST NOT perform reverse-link discovery via corpus scan, brute-force `GET /search` enumeration, or pagination crawl.
- MUST NOT enumerate "siblings" of a record (records replacing the same parent).
- MUST NOT silently follow chains containing cycles or missing-link RIDs — emit `chain_break` / `chain_cycle` markers and stop.

This is an **ancestry tracer**, not a "lineage inspector" in the broad sense. The `forward_view: unavailable` field in the output explicitly disclaims what is NOT computed.

## Quick Start (agent-mediated mode, v1.0)

```python
from orchestrator import dispatch, fetch_sidecar, NotFoundError, Manifest

# 1. Dispatch tuple
RID = "knows:vaswani/attention/2.0.0"
decision = dispatch("inspect_lineage", {"rid": RID}, "version_chain_report")
assert decision["action"] == "route"

# 2. Walk replaces backward
manifest = Manifest(skill="version-inspector", intent_class="inspect_lineage",
                    dispatch_tuple="(inspect_lineage,{rid},version_chain_report)",
                    returned_rids=[RID])
chain = []
seen = set()
current_rid = RID
chain_break = False; chain_cycle = False
max_depth = 20  # safety cap

while current_rid and len(chain) < max_depth:
    if current_rid in seen:
        chain_cycle = True
        break
    seen.add(current_rid)
    try:
        sc = fetch_sidecar(current_rid)
    except NotFoundError:
        chain_break = True
        break
    chain.append({
        "rid": current_rid,
        "version_record": sc.get("version", {}).get("record"),
        "record_status": sc.get("record_status"),
        "freshness_as_of": sc.get("freshness", {}).get("as_of"),
    })
    manifest.fetch_mode_per_rid[current_rid] = "full"
    current_rid = sc.get("replaces")  # may be None — chain ends naturally
    if current_rid:
        manifest.returned_rids.append(current_rid)

# 3. Render version_chain_report (Markdown):
#    | Position | record_id | version.record | record_status | freshness.as_of |
#    | 1 (current) | knows:.../2.0.0 | 2.0.0 | active | 2026-04-26 |
#    | 2 (parent)  | knows:.../1.0.0 | 1.0.0 | superseded | 2026-03-01 |
#
#    chain_break: false / true (with break_at_rid)
#    chain_cycle: false / true (with cycle_at_rid)
#    forward_view: unavailable
#    sibling_view: unavailable
#    latest_inference: NOT PROVIDED — latest-status asserted only via explicit replaces edge

# 4. Manifest finalize
print(manifest.finish())
```

## Routes

| `requested_artifact` | What user gets |
|---|---|
| `version_chain_report` | Markdown ancestry table + chain-break/cycle markers + explicit `forward_view: unavailable` and `sibling_view: unavailable` disclaimers |

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `rid` slot missing | `missing_required_input.rid` |
| Initial rid 404s | `rid_not_found.<rid>` |
| Initial rid fails G7 (e.g. user supplies a review@1 rid) | `empty_working_set_after_profile_filter` |

Note: chain breaks / cycles mid-walk are NOT abstain — they're reported in the artifact (chain_break_at, chain_cycle_at). Walk stops cleanly with what was traced.

## Manifest emission

Per G6 + G4: `skill: version-inspector`, `intent_class: inspect_lineage`, `dispatch_tuple`, `returned_rids: <every rid in chain>`, `fetch_mode_per_rid: {... "full"}`, plus skill-specific `chain_length`, `chain_break: bool`, `chain_cycle: bool`. The output MUST embed the G4 disclaimer: `forward_view: unavailable until /search exposes record_status/replaces fields`.

## Out of scope (locked, never)

- Forward `superseded_by` discovery — would require corpus scan, explicitly forbidden.
- Sibling enumeration — explicitly forbidden.
- Heuristic latest-status — explicitly forbidden.
- Cross-profile lineage (paper@1 ancestor of review@1) — different intent_class.
- Auto-merge of forking lineages — not a chain operation.

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
