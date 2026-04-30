# knows.academy API Schema Reference

Authoritative field-level reference for the knows.academy API. For workflow
patterns and natural-language routing, see `remote-modes.md`.

Base URL: `https://knows.academy/api/proxy`

| Endpoint | Method | Status | Auth |
|---|---|---|---|
| `/jobs/stats` | GET | ✅ verified | none |
| `/search` | GET | ✅ verified | none |
| `/disciplines` | GET | ✅ verified | none — browse hub by discipline |
| `/sidecars/<rid>` | GET | ✅ verified | none — default Accept is YAML; send `Accept: application/json` for JSON |
| `/partial?section=statements` | GET | ✅ verified | none |
| `/partial?section=evidence` | GET | ✅ verified | none |
| `/partial?section=relations` | GET | ✅ verified | none |
| `/partial?section=artifacts` | GET | ✅ verified | none — list of cited/supporting artifact records only |
| `/partial?section=citation` | GET | ✅ verified | none — returns BibTeX text |
| `/health` | GET | ⚠️ may not be deployed on every hub instance; wrappers fall back to `/jobs/stats` probe | none |
| `/sidecars` | POST | ⚠️ unverified | likely `KNOWS_API_KEY` |
| `/generate/pdf` | POST | ⚠️ unverified | likely `KNOWS_API_KEY` |

---

## Hard constraints (read first)

1. **URL-encode `record_id`.** It contains `:` and `/`. Naked path → 404.
   ```python
   import urllib.parse
   rid = "knows:generated/discriminative-generative-synergy-3d-human-mesh/1.0.0"
   encoded = urllib.parse.quote(rid, safe='')
   # → knows%3Agenerated%2Fdiscriminative-generative-synergy-3d-human-mesh%2F1.0.0
   ```
2. **`/sidecars/<rid>` content negotiation.** v1 server defaults Accept to
   `application/x-yaml` (returns YAML). Send `Accept: application/json` for JSON.
   The proxy on `knows.academy/api/proxy` returns JSON by default for callers'
   convenience; the `.yaml` URL suffix returns 404 (`{"detail":{"error":"not_found"}}`).
   To get a YAML byte stream from the proxy: fetch JSON then dump locally via `pyyaml`.
3. **`/partial?section=citation` returns raw BibTeX text**, not JSON. Don't
   `.json()` it.

---

## GET /jobs/stats

**Request**: no params.

**Response** (`application/json`):

```json
{
  "pending":   10735,
  "running":   288,
  "completed": 37897,
  "failed":    1243,
  "skipped":   433,
  "total":     50596
}
```

All fields are integers. `total` is the running grand total across all states.

---

## GET /search

**Request params** (canonical per server v1 spec):

| Param | Type | Default | Notes |
|---|---|---|---|
| `q` | string | — | Full-text search via PostgreSQL `plainto_tsquery('english', ...)` — **AND-logic**: all tokens must match |
| `discipline` | string | — | Filter by discipline. Format is **full path** like `Machine Learning / General` (NOT just `Machine Learning`). Use `/disciplines` endpoint to list valid values. Sparse on records that aren't classified |
| `venue_type` | string | — | Spec canonical: `conference` \| `journal` \| `preprint` \| `workshop`. Hub data may still use the transitional values `published` + `preprint` only; canonical 4 may return 0 until server-side migration completes. Use `published` if `conference`/`journal` return empty |
| `year_min` / `year_max` | int | — | Inclusive range filter |
| `sort` | string | **`latest`** | `latest` (server default — newest first) \| `trending` \| `claims` (sort by stmt_count, useful for richness-prioritized synthesis) |
| `limit` | int | 20 | Max **100** server-side. Clients should set explicitly when targeting > 20 results |
| `offset` | int | 0 | Pagination offset (alternative to `cursor`) |
| `cursor` | string | — | Opaque pagination token returned as `next_cursor` (string-encoded offset). Equivalent to using `offset`. First page omits |

**Filter parameters NOT supported by server**:
- `venue` (specific venue name like "USENIX Security") — treated as keyword in `q`, not filter. Use client-side substring match on returned `venue` field instead.
- `profile` — ignored (cannot pre-filter by profile@ver server-side).
- Single `year` (without `_min`/`_max`) — ignored.

### Search ranking weights (server-side tsvector)

The `search_vector` GIN index assigns weights to fields:

| Weight | Fields |
|---|---|
| **A** (highest) | `title` |
| **B** | `venue`, `discipline`, `author` |
| **C** | `summary`, `keywords` |

**Implications for query crafting**:
- **Server default is `sort=latest` (NOT relevance)** — broad topic queries surface newest arXiv preprints first, burying older published venue papers. Pass `sort=claims` for richness or `sort=trending` for community signal when relevance order isn't critical.
- Specific phrase queries that match titles (Weight A) rank far above topical queries that only match summaries.
- AND-logic means `"side channel attacks on machine learning"` requires ALL 6 tokens to match — narrow queries miss real papers. Wrappers should fall back to single-token OR fan-out when AND returns 0 hits.
- For published security/ML conference papers buried under arXiv noise, combine `venue_type=conference` (or `journal`) + `year_min=YYYY` + `sort=claims` to surface high-quality refereed work.

**Response** (`application/json`):

```jsonc
{
  "results":     [ /* up to 20 SearchResult objects */ ],
  "total":       9523,        // total matching records across all pages
  "next_cursor": "20"         // string; pass back as ?cursor= for next page
}
```

**SearchResult schema** (17 fields, verified):

| Field | Type | Notes |
|---|---|---|
| `record_id` | string | URL-encode before use in `/sidecars/<rid>` |
| `profile` | string | e.g. `"paper@1"`, `"review@1"` |
| `title` | string | |
| `summary` | string | Short abstract / blurb |
| `venue` | string \| null | |
| `year` | int \| null | |
| `discipline` | string | e.g. `"cs"`, `"math"` |
| `keywords` | list[string] | |
| `coverage_statements` | enum string | Mirrors `coverage.statements`. Allowed: `exhaustive` \| `main_claims_only` \| `key_claims_and_limitations` \| `partial` |
| `coverage_evidence` | enum string | Mirrors `coverage.evidence`. Allowed: `exhaustive` \| `key_evidence_only` \| `partial` |
| `provenance_origin` | enum string | `"author"` \| `"machine"` \| `"imported"` (matches canonical schema) |
| `provenance_actor_name` | string | Generating model / human (e.g. `"knows-gen"`, `"claude-opus-4-7"`) |
| `version_record` | string | e.g. `"1.0.0"` |
| `lint_passed` | bool | |
| `download_count` | int | |
| `created_at` | string (ISO 8601) | |
| `stats` | object | Per-section counts: `{stmt_count, evidence_count, relation_count, artifact_count, claim_count, method_count, limitation_count}` (all int) |

---

## GET /sidecars/&lt;rid&gt;

**Request**: path param `rid` (URL-encoded).

**Response** (`application/json`): full KnowsRecord. Canonical v0.9 schema permits
**30 top-level fields** (17 required + 13 optional). The example below shows a
representative subset — actual records may include any of the optional fields.

- **Required (17)**: `$schema`, `knows_version`, `record_id`, `profile`, `subject_ref`, `title`, `authors`, `summary`, `coverage`, `license`, `artifacts`, `statements`, `evidence`, `relations`, `provenance`, `version`, `freshness`
- **Optional (13)**: `abstract`, `access`, `actions`, `extensions`, `funding`, `keywords`, `language`, `record_status`, `replaces`, `resources`, `venue`, `venue_type`, `year`

```jsonc
{
  "$schema":      "https://knows.dev/schema/record-0.9.json",  // canonical schema URI (NOT knows.academy)
  "knows_version": "0.9.0",
  "profile":       "paper@1",
  "license":       "CC-BY-4.0",
  "record_id":     "knows:generated/.../1.0.0",
  "subject_ref":   "art:paper",
  "title":         "...",
  "summary":       "...",
  "venue":         "...",                                       // OPTIONAL: venue NAME (e.g. "NeurIPS 2026")
  "venue_type":    "preprint",   // OPTIONAL: enum: published | preprint | under_review | in_preparation
                                  //                | technical_report | thesis | book | other
  "year":          2026,                                        // OPTIONAL
  "authors":       [ /* Author objects */ ],
  "artifacts":     [ /* Artifact objects */ ],
  "statements":    [ /* Statement objects */ ],
  "evidence":      [ /* Evidence objects */ ],
  "relations":     [ /* Relation objects */ ],
  "actions":       [ /* OPTIONAL: Action objects */ ],
  "coverage":      { /* coverage scope */ },
  "freshness":     { /* freshness metadata */ },
  "version":       { /* sidecar versioning */ },
  "provenance":    { /* generation provenance */ }
  // Other optional fields may appear: abstract, access, extensions, funding,
  // keywords, language, record_status, replaces, resources
}
```

For nested object schemas (Author, Artifact, Statement, Evidence, Relation,
Action, Coverage, Freshness, Version, Provenance), see the canonical schema at
`knows-record-0.9.json` (sibling file in this `references/` directory). The
remote endpoint returns records that conform to that schema exactly.

---

## GET /partial?record_id=&lt;rid&gt;&section=&lt;name&gt;

**Request params**:

| Param | Required | Allowed values |
|---|---|---|
| `record_id` | yes | URL-encoded record_id |
| `section` | yes | `statements` \| `evidence` \| `relations` \| `citation` |

**Response** for `statements` / `evidence` / `relations` (`application/json`):

```jsonc
{
  "record_id": "knows:generated/.../1.0.0",
  "items":     [ /* list of section objects */ ]
}
```

`items` contains the full nested objects from the canonical schema (same shape
as the corresponding key in the full record). Use this when you only need one
slice — saves ~93% tokens per the E8 ablation.

**Response** for `citation` (`text/plain` BibTeX):

```bibtex
@article{liu2026,
  title     = {Discriminative-Generative Synergy for Occlusion Robust 3D Human Mesh Recovery},
  author    = {Yang Liu and Zhiyong Zhang},
  journal   = {arXiv preprint},
  year      = {2026},
  note      = {Sidecar: knows:generated/discriminative-generative-synergy-3d-human-mesh/1.0.0}
}
```

Fields included: `title`, `author`, `journal` / `booktitle`, `year`, `note` (always
contains the sidecar `record_id` for traceability). Do not call `.json()` —
parse as text or shell-redirect to a `.bib` file.

---

## Error responses

All error responses come back as JSON regardless of endpoint:

```json
{"detail": {"error": "not_found"}}
{"detail": {"error": "<other_code>", "message": "..."}}
```

Common codes:
- `not_found` — bad `record_id`, wrong section name, `.yaml` suffix, etc.
- 4xx returned with the JSON body, not bare HTTP error.

---

## Pagination pattern

```python
cursor = None
while True:
    params = {"q": query}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(BASE + "/search", params=params).json()
    yield from resp["results"]
    cursor = resp.get("next_cursor")
    if not cursor or len(resp["results"]) == 0:
        break
```

`next_cursor` is absent / null on the last page.

**Note**: `cursor` and `offset` are equivalent — `next_cursor` is just a string-encoded next-`offset`. Use whichever style fits your code; do not mix both in the same request (server only inspects one). The orchestrator's `fetch_search` uses `offset` internally for explicit page-boundary control.

---

## Probe commands (reproducible)

```bash
BASE="https://knows.academy/api/proxy"
RID="knows:generated/discriminative-generative-synergy-3d-human-mesh/1.0.0"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")

curl -s "$BASE/jobs/stats" | jq .
curl -s "$BASE/search?q=attention" | jq '.results | length, .total, .next_cursor'
curl -s "$BASE/sidecars/$ENC" | jq 'keys'
curl -s "$BASE/partial?record_id=$ENC&section=statements" | jq '.items | length'
curl -s "$BASE/partial?record_id=$ENC&section=citation"   # raw BibTeX
```

---

## Unverified — needs probing before relying on

- POST `/sidecars` (upload). Auth header pattern, payload format, response shape.
- POST `/generate/pdf` (remote generation). Sync vs async behavior, job polling.
- Rate limits (no public docs found).
- Whether `next_cursor` ever returns as int instead of string.

Update this file when an unverified endpoint is probed against a live deployment.

---

## v0.10 prerequisite — cross-profile relation filter (NOT YET SHIPPED)

`next-step-advisor` v0.10 widens its evidence pool to include `commentary@1` sidecars whose `relations[*].predicate==reflects_on AND object_ref` resolves to a paper@1 RID in the working set. **The hub `/search` API does not currently support filtering by relation-typed cross-references.** Today's `/search` accepts only the params listed above (`q`, `discipline`, `venue_type`, `year_min`/`max`, `sort`, `limit`, `offset`/`cursor`); `profile` is ignored, and there is no `?relation=` filter.

### Today's fallback — two-phase fetch

`next-step-advisor` works around this with a two-phase keyword-fallback:

1. **Phase 1**: search `/search?q=<topic>` → keep `profile==paper@1` results, derive seed RIDs.
2. **Phase 2**: for each seed paper, search `/search?q=<paper.title>` → keep `profile==commentary@1` results → fetch their `/partial?section=relations` → in-memory filter for `predicate==reflects_on AND object_ref starts with <seed_rid>`.

This works because the tsvector ranking weights titles as Weight A (highest), so a paper title query reliably surfaces commentary@1 sidecars whose `title` field references the paper. It pulls some noise that gets filtered in-memory; cost is acceptable until the hub adds a relation filter.

### Server-side feature requested (proposed)

When the hub team is ready, the cleanest server-side support would be **either** of:

**Option A — relation-typed param on `/search`:**

```
GET /search?relation=reflects_on&target_rid=<encoded_rid>
  → returns SearchResult[] for sidecars whose relations[*] include
    {predicate: "reflects_on", object_ref: "<target_rid>#..."}
```

**Option B — dedicated `/relations` endpoint:**

```
GET /relations?predicate=reflects_on&object_rid=<encoded_rid>
  → returns minimal records: {record_id, profile, predicate, subject_ref, object_ref}
    suitable for a follow-up batch fetch via /sidecars/<rid> if needed
```

Option A reuses the existing search infrastructure and pagination; Option B is more flexible for future predicates (e.g. cross-paper `cites` traversal) but requires a new endpoint. We do not have a strong preference — either lets `next-step-advisor` collapse Phase 2 into a single targeted call per seed.

### Server-side data dependency

The fallback assumes `commentary@1` sidecars are **uploaded to the hub** (POST `/sidecars`, currently unverified — see above). Until upload is wired up, commentary@1 sidecars stay local and `next-step-advisor` Phase 2 returns zero results. The skill's manifest emits a coverage note in this case, so the user knows the brief is paper@1-only and recommends running `commentary-builder` locally on the seed papers.
