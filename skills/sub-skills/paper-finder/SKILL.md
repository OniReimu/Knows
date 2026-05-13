---
name: knows-paper-finder
description: "Search knows.academy for sidecars matching a query, return ranked results and optional BibTeX. Triggers: 'find papers about X', 'give me 10 sidecars on Y', 'search knows.academy for Z', 'what's been published on W', 'BibTeX entries for query'."

# Orchestrator dispatch contract — see ../../references/dispatch-and-profile.md §1.5 + §3.4
intent_class: discover
required_inputs:
  - query_text          # free-text search query passed to GET /api/proxy/search?q=...
requested_artifacts:
  - ranked_paper_list   # primary route — Markdown table of search results
  - bibtex              # secondary route — papers.bib file with BibTeX entries

# Profile contract — G7 (single-profile in v1.0)
accepts_profiles: [paper@1]            # `discover` for paper@1 only; review@1 search is out of scope for v1.0

# Quality policy — G2'
quality_policy:
  require_lint_passed: true            # do not return broken records to users
  allowed_coverage:                    # exclude `partial` to match downstream consumer expectations
    - exhaustive
    - main_claims_only
    - key_claims_and_limitations
  min_statements: 5

# Fetch-planner — G3 (search returns SearchResult shape with stats; full /sidecars/<rid> not needed for ranking)
requires_full_record: false

# emits_profile omitted — ranked_paper_list and bibtex are not sidecar artifacts (read-only skill)
---

# paper-finder — Search knows.academy for sidecars

This sub-skill exercises the verified `GET /api/proxy/search` + `GET /api/proxy/partial?section=citation` endpoints. It is the simplest v1 sub-skill: read-only, paginated, well-bounded artifact, no LLM call required for ranking (LLM is optional for query reformulation).

## Use cases & flag presets

**READ THIS FIRST.** The server default is `--sort latest`, which buries published conference papers under arXiv preprints. For most non-trivial use cases the default is the wrong choice. Pick the preset matching your goal:

| Use case | Recommended flags | Why |
|---|---|---|
| Latest arXiv pulse on a topic | (defaults: `--sort latest`) | OK to surface preprints first |
| **Prior-art / collision check** | `--venue-type published --sort claims --top-k 8+` | Reaches conference + journal papers, sorts by sidecar richness |
| Survey / related-work prep | `--venue-type published --sort claims --top-k 10` | Same — feeds `survey-narrative` / `survey-table` recipes |
| Specific-venue subset | add `--venue "NeurIPS"` (client-side substring) | Note: hub mostly tags as `published`, not `conference`; substring filter on venue field |
| Foundational / pre-2024 papers | hub coverage is thin pre-2024 → **fall back to WebSearch / arXiv** | Hub indexing horizon ~2024+; cite-from-elsewhere |

> ⚠️ **Common failure**: calling `paper-finder` with default flags for a prior-art search, getting back only arXiv preprints, and concluding "the foundational paper is not on hub." Switch to `--venue-type published --sort claims` first; foundational pre-2024 misses are a real hub gap, not a search-flag gap.

## Quick Start (agent-mediated mode, v1.0)

Per `../../SKILL.md` "v1.0 Agent-Mediated Mode" — you (the agent) ARE the orchestrator. End-to-end for "find me 5 papers on X":

```bash
# 1. Construct dispatch tuple in your head: (discover, {query_text: "X"}, ranked_paper_list); top-K=5 is a knob, not a slot
# 2. Make the API call directly (G5 transport done by you):
curl -s "https://knows.academy/api/proxy/search?q=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "X")" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
hits = data['results'][:5]                              # top-K
# 3. G7 profile filter: drop non-paper@1
hits = [r for r in hits if r.get('profile') == 'paper@1']
# 4. G2' quality filter: lint_passed + allowed_coverage + stmt_count >= 5
hits = [r for r in hits if r.get('lint_passed') and r.get('coverage_statements') in ('exhaustive','main_claims_only','key_claims_and_limitations') and r.get('stats',{}).get('stmt_count',0) >= 5]
# 5. Format Markdown table (per route 'ranked_paper_list')
print('| # | Title | Venue | Year | Stmts |')
print('|---|---|---|---|---|')
for i, r in enumerate(hits, 1):
    print(f'| {i} | {r[\"title\"]} | {r.get(\"venue\",\"-\")} | {r.get(\"year\",\"-\")} | {r[\"stats\"][\"stmt_count\"]} |')
"
# 6. Manifest: build dict {skill, queries, returned_rids, applied_*, excluded_*, abstained}; print as JSON or write to ./manifest.json
```

For `bibtex` route, after step 4 add: for each kept rid, `curl -s "https://knows.academy/api/proxy/partial?record_id=<encoded>&section=citation"` (returns raw BibTeX text, NOT JSON), concatenate, write to `papers.bib`.

## Query crafting (server search behavior, see api-schema.md §GET /search)

The hub's full-text search is **AND-logic over English-stemmed tokens** with field weights `A: title > B: venue/discipline/author > C: summary/keywords`. This means:

1. **Specific phrase queries beat broad topic queries** because title (Weight A) trumps summary (Weight C). `"side channel attacks"` will surface arXiv preprints with that exact phrase in title above S&P papers about specific contributions.
2. **Multi-token queries are restrictive** — `"side channel attacks on machine learning"` requires all 6 tokens. Wrappers should auto-fall-back to single-token OR fan-out when AND-logic returns 0 hits (orchestrator.py `run_paper_finder` does this automatically; pass `--no-or-fallback` to disable).
3. **Use server-side filters to reach published venues** — the hub has S&P/USENIX/CCS/NDSS papers, but topic queries can bury them under arXiv preprints. To reach published-only results:
   ```bash
   python3 ../../scripts/orchestrator.py paper-finder "side channel" \
     --venue-type published --year-min 2024 --top-k 10
   ```
4. **Use `--sort claims`** to surface the richest sidecars first (highest stmt_count). Best for synthesis sub-skills (survey-narrative, next-step-advisor) that need substantive content.
5. **Use `--venue "USENIX"` substring filter** for specific-venue subsetting (server doesn't support exact venue name filter; client-side substring match on returned `venue` field).

## Canonical references

1. **`../../references/dispatch-and-profile.md`** §1.5 + §3.4 — routing contract
2. **`../../references/api-schema.md`** §`/search` + §`/partial?section=citation` — endpoint shapes
3. **`../../references/remote-modes.md`** — workflow patterns + URL-encoding helpers

## Routes

This sub-skill owns 2 rows in `dispatch-and-profile.md` §1.5:

| `requested_artifact` | What user gets | Implementation |
|---|---|---|
| `ranked_paper_list` | Markdown table: record_id / title / venue / year / stmt count / lint_passed | Iterate `GET /search?q=&cursor=`, format SearchResult objects into table |
| `bibtex` | `papers.bib` file with BibTeX entries for top-K results | After ranked list, for each top-K rid: `GET /partial?record_id=&section=citation` (returns raw BibTeX text), concatenate |

The orchestrator routes based on `requested_artifact`. Same skill body, different output formatter. If user asks for both ("ranked list AND bibtex"), orchestrator emits `multi_artifact_request_rejected` per §7 — user must call twice.

## Workflow

```
1. Validate inputs (orchestrator §1.3 runtime validation already passed)
   - query_text: non-empty string

2. Fetch search results via G5 transport layer
   - cursor = None
   - Loop: GET /api/proxy/search?q=<query_text>[&cursor=<cursor>]
   - Each response yields up to 20 SearchResult objects per api-schema.md
   - Continue until next_cursor is null OR top-K limit reached (default K = 20, configurable)

3. Apply G7 profile filter to results
   - Each SearchResult has a `profile` field (per api-schema.md SearchResult schema)
   - Drop results where profile != "paper@1" (or missing/malformed)
   - Log exclusions to manifest's excluded_missing_profile / excluded_malformed_profile

4. Apply G2' quality filter to remaining results
   - Drop results failing quality_policy: lint_passed != true, coverage_statements not in allowed_coverage, stats.stmt_count < min_statements
   - Log exclusions to manifest's quality_exclusions

5. If working set empty after filters → abstain (per §5):
   - All profile-dropped → empty_working_set_after_profile_filter
   - All quality-dropped → empty_working_set_after_quality_filter
   - No hits returned by API → empty_working_set_after_profile_filter (no-hits tie-breaker per §2.2)

6. Branch on requested_artifact:
   a. ranked_paper_list: format kept results into Markdown table; return
   b. bibtex: for each top-K rid, GET /partial?record_id=<encoded>&section=citation (returns raw BibTeX text, NOT JSON); concatenate; return papers.bib content

7. Emit manifest (G6) and return
```

## Manifest emission

Per G6, every run emits manifest with these fields populated:

- `skill: knows-paper-finder`
- `intent_class: discover`
- `dispatch_tuple: (discover, {query_text}, {ranked_paper_list|bibtex})`
- `queries: [<query_text>]`
- `returned_rids: [<every rid from API hits, before filtering>]`
- `applied_profile_filters: [paper@1]`
- `applied_quality_policy` (this skill's frontmatter)
- `excluded_missing_profile` / `excluded_malformed_profile` / `quality_exclusions` arrays populated as exclusions occur
- `fetch_mode_per_rid`:
  - For ranked_paper_list route: empty (search returns SearchResult shape directly; no per-rid fetch)
  - For bibtex route: `{<rid>: "partial:citation"}` for each top-K rid
- `cache_hits` populated by G5 transport layer
- `abstained` / `abstained_reason` (when applicable)

## Abstain conditions (from §5)

| Condition | `abstained_reason` |
|---|---|
| `query_text` slot missing or empty | `missing_required_input.query_text` / `invalid_slot_type.query_text` |
| API returns empty results AND no profile/quality drops | `empty_working_set_after_profile_filter` (no-hits tie-breaker) |
| All hits filtered by G7 profile | `empty_working_set_after_profile_filter` |
| All surviving hits filtered by G2' quality | `empty_working_set_after_quality_filter` |
| API call fails (G5 retries exhausted) | `upstream_unavailable_retries_exhausted` |
| API response malformed | `upstream_response_malformed` |

## Smoke test

```bash
# Ranked list route — minimal happy path
curl -s "https://knows.academy/api/proxy/search?q=attention" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total matches: {data[\"total\"]}')
print(f'Returned: {len(data[\"results\"])} results, next_cursor: {data.get(\"next_cursor\")}')
for r in data['results'][:5]:
    print(f'  {r[\"record_id\"]} | {r[\"title\"][:60]} | profile={r[\"profile\"]} | lint={r[\"lint_passed\"]} | stmts={r[\"stats\"][\"stmt_count\"]}')
"
# Expect: total > 0, results have profile=paper@1 mostly, lint_passed=true mostly

# BibTeX route — fetch citation for one rid
RID="knows:vaswani/attention/1.0.0"   # replace with a real rid from the search
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$RID")
curl -s "https://knows.academy/api/proxy/partial?record_id=$ENC&section=citation"
# Expect: raw BibTeX text starting with @article{... or @inproceedings{...}
```

## Implementation

CLI wrapper available: `python3 scripts/orchestrator.py paper-finder "<query>" --top-k N [--year-min ...] [--venue-type ...] [--sort {latest|trending|claims}]`. The wrapper handles pagination, filter application, and table/BibTeX formatting. Agent-mediated mode (LLM agent making the curl calls directly) is also supported and follows the steps in §3 above.

## Out of scope

- Cross-profile search (returning paper@1 + review@1 in one call) — multi-profile pools are a §3 violation; user must issue separate calls
- Citation graph traversal ("papers cited by X") — DEFERRED, no graph endpoint
- Semantic similarity ranking beyond the API's default — server-side ranking is what we get
- Full-record fetch in this skill — that's `extract` → sidecar-reader, not `discover`
- Multi-query batch in one call — single artifact per request (§7)

Related: [`../../SKILL.md`](../../SKILL.md) | [`../../references/api-schema.md`](../../references/api-schema.md) | [`../../references/dispatch-and-profile.md`](../../references/dispatch-and-profile.md) §1.5 + §3.4
