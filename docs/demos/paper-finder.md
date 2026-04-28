# Demo: `paper-finder`

> **What it does**: Search [knows.academy](https://knows.academy) for sidecars matching a query. Returns ranked list + optional BibTeX export.

## User intent

> "Find me 5 papers about diffusion models and privacy."

## Dispatch tuple

```
intent_class:        discover
required_inputs:     {query_text: "diffusion + privacy"}
requested_artifact:  ranked_paper_list   (or `bibtex` for BibTeX export)
                     ↓
                  paper-finder
```

## What happens under the hood

```bash
# G5 transport: paginated search
curl -s "https://knows.academy/api/proxy/search?q=diffusion+privacy" \
  | jq '.results[:5] | .[] | {rid: .record_id, title, profile, lint_passed, stmts: .stats.stmt_count}'
```

```json
{"rid": "knows:liu/diffusion-privacy/1.0.0", "title": "Privacy-Preserving Diffusion Models...", "profile": "paper@1", "lint_passed": true, "stmts": 14}
{"rid": "knows:chen/dp-diffusion/1.0.0",     "title": "Differentially Private Diffusion...",   "profile": "paper@1", "lint_passed": true, "stmts": 11}
{"rid": "knows:wang/private-gan/1.0.0",      "title": "PrivGAN: Private Synthesis via...",     "profile": "paper@1", "lint_passed": true, "stmts": 9}
{"rid": "knows:tan/dp-sde/1.0.0",            "title": "Differentially Private SDEs...",        "profile": "paper@1", "lint_passed": true, "stmts": 13}
{"rid": "knows:zhang/dp-noise/1.0.0",        "title": "Calibrated Noise for Diffusion...",     "profile": "paper@1", "lint_passed": true, "stmts": 10}
```

**G7 profile filter** silently drops any `review@1` records that came back in the search — `paper-finder` declares `accepts_profiles: [paper@1]` so review records never enter the working set.

**G2' quality filter** drops records with `lint_passed: false`, `coverage_statements: partial`, or `stmt_count < 5`. Manifest logs every exclusion.

## Artifact: Markdown table

| # | Title | Venue | Year | Stmts | Lint |
|---|---|---|---|---|---|
| 1 | Privacy-Preserving Diffusion Models for Sensitive Data | NeurIPS 2024 | 2024 | 14 | ✅ |
| 2 | Differentially Private Diffusion Trained on Mixed Data | ICML 2024 | 2024 | 11 | ✅ |
| 3 | PrivGAN: Private Synthesis via Generative Adversarial Privacy | CCS 2023 | 2023 | 9 | ✅ |
| 4 | Differentially Private SDEs for Score-Based Generative Modeling | ICLR 2024 | 2024 | 13 | ✅ |
| 5 | Calibrated Noise for Diffusion Privacy Budgets | arXiv preprint | 2024 | 10 | ✅ |

## Artifact: BibTeX (when `requested_artifact: bibtex`)

```bibtex
@article{liu2024,
  title  = {Privacy-Preserving Diffusion Models for Sensitive Data},
  author = {Yang Liu and ...},
  year   = {2024},
  note   = {Sidecar: knows:liu/diffusion-privacy/1.0.0}
}
@article{chen2024,
  title  = {Differentially Private Diffusion Trained on Mixed Data},
  ...
}
```

## Manifest emission (G6)

```json
{
  "skill": "paper-finder",
  "intent_class": "discover",
  "queries": ["diffusion + privacy"],
  "returned_rids": ["knows:liu/...", "knows:chen/...", ...],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": {
    "require_lint_passed": true,
    "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations"],
    "min_statements": 5
  },
  "excluded_missing_profile": [],
  "excluded_malformed_profile": [],
  "quality_exclusions": [{"rid": "knows:weak-paper/1.0", "policy_field": "min_statements", "actual": 3}],
  "abstained": false
}
```

## Token economics (vs naive web search)

- 5 returned hits with full metadata: ~1.2K tokens
- Equivalent Google Scholar scrape + manual filter: ~12K tokens (10× more)
- BibTeX export: free (already in sidecar partial endpoint)

## Try it yourself

```bash
# Direct API call
curl -s "https://knows.academy/api/proxy/search?q=diffusion+privacy"

# Via Claude Code (requires the Knows skill installed)
"Find me 5 papers about diffusion models and privacy."
```
