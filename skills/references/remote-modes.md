# Remote Modes (knows.academy platform)

The knows.academy API is at `https://knows.academy/api/proxy`. No authentication required for read operations. Set `KNOWS_API_KEY` for uploads if required.

All examples use `curl` — no `pip install` needed. Claude can also use WebFetch for GET requests.

> **For verified field-level schemas, see `api-schema.md`.** This file covers
> workflow patterns and natural-language routing. The schema reference covers
> exact response shapes and which endpoints are probed vs unverified.

> **`record_id` must be URL-encoded** (contains `:` and `/`). Examples below
> show both naked (readable) and encoded (working) forms — always use the
> encoded form in real calls. In shell:
> `ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")`

---

## search — Find sidecars on knows.academy

```bash
# Basic search
curl -s "https://knows.academy/api/proxy/search?q=attention+mechanism&limit=5"

# Filter by discipline
curl -s "https://knows.academy/api/proxy/search?q=transformer&discipline=cs&limit=3"
```

**Response**: JSON with `results[]` array. Each result has `record_id`, `title`, `summary`, `venue`, `year`, `discipline`, `stats` (stmt/evidence/relation counts).

**Example usage**: User says "find papers about adversarial robustness" → construct query → parse results → present as table.

---

## download — Get a sidecar (full or partial)

The proxy returns **JSON only** — `.yaml` suffix returns 404. To save as YAML,
fetch JSON then dump locally with `pyyaml`.

```bash
# Encode record_id once (contains : and /)
RID="knows:vaswani/attention/1.0.0"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")

# Full sidecar (all fields, JSON)
curl -s "https://knows.academy/api/proxy/sidecars/$ENC" -o paper.knows.json

# Partial fetch — statements only (93% fewer tokens)
curl -s "https://knows.academy/api/proxy/partial?record_id=$ENC&section=statements"

# Evidence only
curl -s "https://knows.academy/api/proxy/partial?record_id=$ENC&section=evidence"

# Relations only
curl -s "https://knows.academy/api/proxy/partial?record_id=$ENC&section=relations"

# BibTeX citation (returns plain text, NOT JSON)
curl -s "https://knows.academy/api/proxy/partial?record_id=$ENC&section=citation" -o paper.bib
```

**Partial fetch** is the recommended default for agents — statements-only retains 88% of accuracy at 7% of token cost. Download full sidecar only when needed for validation or cross-reference checks.

---

## upload — Publish a sidecar

> ⚠️ **Unverified endpoint.** Auth header pattern, content-type, and response shape
> below are documented from prior assumptions but have NOT been probed against the
> live API. See `api-schema.md` "Unverified" section. Probe before relying on it.

```bash
# Upload (lint locally first!)
python3 scripts/lint.py paper.knows.yaml && \
curl -s -X POST "https://knows.academy/api/proxy/sidecars" \
  -H "Content-Type: application/x-yaml" \
  -H "Authorization: Bearer $KNOWS_API_KEY" \
  --data-binary @paper.knows.yaml
```

**Expected response** (unverified): JSON with `record_id` and `url` of the published sidecar.

**Important**: Always lint before uploading. The platform may reject invalid sidecars.

---

## generate — Remote sidecar generation from PDF

> ⚠️ **Unverified endpoint.** Sync-vs-async behavior and job-polling protocol
> below are assumed, not probed. See `api-schema.md` "Unverified" section.

```bash
curl -s -X POST "https://knows.academy/api/proxy/generate/pdf" \
  -H "Content-Type: application/pdf" \
  --data-binary @paper.pdf
```

**Expected response** (unverified): JSON with either immediate `sidecar` field (synchronous) or `job_id` (async — check status).

---

## status — Check platform job queue

```bash
curl -s "https://knows.academy/api/proxy/jobs/stats"
```

**Response**: JSON with `pending`, `running`, `completed`, `failed`, `skipped`, `total`.

---

## Natural language routing for remote operations

| User says | API call |
|---|---|
| "search for papers about X" | `GET /search?q=X` |
| "download the sidecar for X" | `GET /sidecars/<record_id>` |
| "just get the claims from X" | `GET /partial?record_id=...&section=statements` |
| "upload this sidecar" | Lint first → `POST /sidecars` |
| "generate sidecar from this PDF" | `POST /generate/pdf` |
| "how many sidecars are on the platform" | `GET /jobs/stats` → report `total` |
