# version-inspector — Reference Contract

**Status**: v1.0. **Hard non-goals are load-bearing — every "MUST NOT" below is part of the contract, not a TODO.**

> **Companion**: `sub-skills/version-inspector/SKILL.md`. Contract wins on disagreement.

---

## 1. Purpose and scope (deliberately narrow)

Walk a single `paper@1` sidecar's declared `replaces` chain **backward** (current → ancestor → grandparent → ...) and report each hop's `version.record`, `record_status`, `freshness.as_of`. Detect chain breaks (404 mid-walk) and chain cycles. Stop at depth 20 (safety cap).

**This is an ancestry tracer, NOT a lineage inspector** in the broad sense. The narrow scope is intentional and load-bearing.

---

## 2. Hard non-goals (MUST NOT)

Each clause below is a load-bearing non-goal:

1. **MUST NOT discover forward `superseded_by` relationships** — the API's `GET /search` does not expose `replaces` field for filtering. Forward-discovery would require corpus scan.
2. **MUST NOT infer "latest", "newest", or "canonical" status** by sorting/ranking on `version.record`, `freshness.as_of`, `provenance.created_at`, or any timestamp-derived heuristic. Latest-status is asserted only by an explicit `replaces` edge from a successor.
3. **MUST NOT perform reverse-link discovery** via corpus scan, brute-force `GET /search` enumeration, or pagination crawl to find records that may declare `replaces: <current_rid>`.
4. **MUST NOT enumerate "siblings"** of a record (other records replacing the same parent).
5. **MUST NOT silently follow chains containing cycles or missing-link RIDs** — emit explicit `chain_break` / `chain_cycle` markers in the output and stop traversal.
6. **MUST NOT mutate any record** — pure read-only.
7. **MUST NOT make claims about correctness, authoritativeness, or canonicality** of any record in the chain — only report what the chain says.

If you find yourself wanting to relax any of these to make the skill "more useful", you are reintroducing the failure mode this contract was written to prevent. These are non-negotiable in v1.x.

---

## 3. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `rid` | record_id | yes | Starting point of the backward walk |
| `max_depth` | int | no (default 20) | Hard cap; even if user supplies > 20, capped at 20 |

---

## 4. Output schema

```jsonc
{
  "starting_rid": "knows:author/title/2.0.0",
  "chain": [
    {
      "position": 1,
      "tag": "current",
      "rid": "knows:author/title/2.0.0",
      "version_record": "2.0.0",
      "record_status": "active",
      "freshness_as_of": "2026-04-26T00:00:00Z"
    },
    {
      "position": 2,
      "tag": "parent",
      "rid": "knows:author/title/1.0.0",
      "version_record": "1.0.0",
      "record_status": "superseded",
      "freshness_as_of": "2026-03-01T00:00:00Z"
    }
    /* ... up to max_depth entries ... */
  ],
  "chain_length": <int>,
  "chain_break": false,
  "chain_break_at_rid": null,                    // populated when chain_break: true
  "chain_cycle": false,
  "chain_cycle_at_rid": null,                    // populated when chain_cycle: true
  "depth_capped": false,                          // true if walk hit max_depth
  "forward_view": "unavailable",                  // ALWAYS this string
  "sibling_view": "unavailable",                  // ALWAYS this string
  "latest_inference": "NOT PROVIDED — latest-status asserted only via explicit replaces edge from a successor; this skill does not infer latest",
  "manifest_path": "<path>"
}
```

**Hard rules**:

- `forward_view`, `sibling_view`, `latest_inference` strings are MANDATORY and verbatim. Output without them is malformed.
- `chain[0].tag` MUST be `"current"`. Subsequent entries: `"parent"`, `"grandparent"`, `"great-grandparent"`, then `"ancestor (depth N)"` for N ≥ 4.
- `chain` is ordered current → ancestor (descending in version time, ascending in distance from query rid).

---

## 5. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `rid` slot missing | `missing_required_input.rid` |
| Initial rid 404s | `rid_not_found.<rid>` |
| Initial rid fails G7 (e.g. user supplies `review@1`) | `empty_working_set_after_profile_filter` |

**NOT abstain conditions** (chain is reported with markers):
- Chain break mid-walk (404 on parent rid) → `chain_break: true`, `chain_break_at_rid: <rid>`, walk stops cleanly with what was traced.
- Chain cycle (rid revisited within walk) → `chain_cycle: true`, `chain_cycle_at_rid: <rid>`, walk stops at first revisit.
- Hit `max_depth` → `depth_capped: true`, walk stops with chain[0..max_depth].

---

## 6. Walk algorithm (canonical implementation)

```python
chain = []
seen = set()
current_rid = starting_rid
chain_break = False
chain_cycle = False
depth_capped = False
for position in range(1, max_depth + 1):
    if current_rid in seen:
        chain_cycle = True
        cycle_at = current_rid
        break
    seen.add(current_rid)
    try:
        sc = fetch_sidecar(current_rid)
    except NotFoundError:
        chain_break = True
        break_at = current_rid
        break
    chain.append({...})  # populate from sc
    next_rid = sc.get("replaces")
    if not next_rid:
        break  # natural chain end
    current_rid = next_rid
else:
    depth_capped = True
```

The `for/else` structure ensures `depth_capped` is set only when the loop completes without break.

---

## 7. Manifest emission contract

```jsonc
{
  "skill": "version-inspector",
  "intent_class": "inspect_lineage",
  "dispatch_tuple": "(inspect_lineage,{rid},version_chain_report)",
  "returned_rids": [<every rid in chain>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* frontmatter, but min_statements=0 since lineage doesn't need content */ },
  "fetch_mode_per_rid": { /* all "full" — G3 requires full record per hop */ },
  /* skill-specific */
  "chain_length": <int>,
  "chain_break": <bool>,
  "chain_cycle": <bool>,
  "depth_capped": <bool>,
  "governance_disclaimer": "forward_view: unavailable until /search exposes record_status/replaces fields; sibling_view: unavailable; latest_inference: NOT PROVIDED"
}
```

The `governance_disclaimer` field is mandatory and verbatim per `dispatch-and-profile.md` G4.

---

## 8. Why this contract is load-bearing

Version inspection seems mundane until you consider what users do with the output. If `version-inspector` reports "this is the latest version" (heuristically), users cite that record as authoritative. If it reports a chain that silently includes a cycle, users get confused about which record is current. If it auto-discovers forward links by crawling, it presents a corpus-wide view that's actually incomplete (some records simply aren't on the hub yet).

The hard non-goals make the failure modes loud:

- "I can't tell you the latest" is honest; "this is the latest (heuristic)" is dangerous.
- "Cycle detected at X" is correct; silently following a cycle is broken.
- "Forward view unavailable" sets correct user expectations; faking forward discovery is a contract violation.

The skill is deliberately under-powered relative to what users might want, because over-powered would mean making claims the API can't actually back.

