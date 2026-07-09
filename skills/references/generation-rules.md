# Schema Quick Reference + Common Lint Failures

> Moved out of `SKILL.md` for context efficiency. Read this file alongside
> `yaml-template.yaml` + `gen-prompt.md` before generating or fixing a sidecar.

## Schema Quick Reference (v0.9)

```
KnowsRecord (31 root fields)
  +- authors[]          name (required), affiliation (required), role: first|corresponding|senior|contributor
  |                     optional: orcid, email, homepage, scholar_id, anonymous
  +- artifacts[]        artifact_type: paper|repository|dataset|model|benchmark|software|website|other
  |                     role: subject|supporting|cited
  +- statements[]       statement_type: claim|assumption|limitation|method|question|definition
  |   modality:         empirical|theoretical|descriptive|normative
  |   status:           asserted|retracted|superseded|under_review
  |   confidence:       claim_strength (high|medium|low) x extraction_fidelity (high|medium|low)
  |   locator_type:     fragment|xpath|css|line_range|page_range|table|figure|section|paragraph|other
  +- evidence[]         evidence_type: table_result|figure|experiment_run|proof|case_study|observation|survey_result|citation_backed|qualitative_analysis|statistical_test|simulation|artifact_run|clinical_trial|other
  |   observations[]:   metric (required) + value (number) OR qualitative_value (string)
  +- relations[]        predicate: supported_by|challenged_by|depends_on|limited_by|cites|uses|evaluates_on|implements|documents|same_as|supersedes|retracts
  |   citation_intent:  supports|extends|uses_method|compares_to|contradicts|reviews|cites_data|background|other
  +- actions[]          action_type: download|run|query|deploy|other
  +- replaces           record_id of previous version (singly-linked version chain)
  +- record_status      active|retracted|superseded|deprecated
  +- venue_type         published|preprint|under_review|in_preparation|technical_report|thesis|book|other
  +- access             open|embargoed|closed|login_required|subscription
  +- coverage           statements (exhaustive|main_claims_only|key_claims_and_limitations|partial) x evidence (exhaustive|key_evidence_only|partial)
  +- provenance         origin (author|machine|imported), actor.type (person|org|tool), method (extraction|manual_curation|conversion|import)
  +- version            spec x record x source (three-layer versioning)
  +- freshness          as_of, update_policy (immutable|versioned|rolling), stale_after
  +- Locator.type       url|git|path|doi|other
```

**Version chain:** When updating a sidecar, set `replaces: <old_record_id>` in the new record. The old record should set `record_status: superseded`.

---

## Common Mistakes That Cause Lint Failure

These are the most frequent errors LLMs make when generating sidecars. AVOID ALL OF THESE:

| Mistake | Wrong | Correct |
|---|---|---|
| actor.type | `type: ai` | `type: tool` (ONLY: person, org, tool) |
| observation.value | `value: '22'` (quoted string) | `value: 22` (unquoted number) |
| observation.value | `value: "75.8%"` | `value: 75.8` + `unit: "%"` |
| artifact field name | `type: paper` | `artifact_type: paper` |
| statement field name | `claim: "text..."` | `text: "text..."` + `statement_type: claim` |
| evidence field name | `type: table_result` | `evidence_type: table_result` |
| relation field name | `type: supported_by` | `predicate: supported_by` |
| relation source | `statement: "stmt:c1"` | `subject_ref: "stmt:c1"` |
| relation target | `evidence: "ev:e1"` | `object_ref: "ev:e1"` |
| wrong predicate tense | `evaluated_on` | `evaluates_on` (present tense, no 'd') |
| wrong predicate | `supports` | `supported_by` (passive form) |
| wrong predicate | `challenges` | `challenged_by` (passive form) |
| extra fields | `description: "..."` on any entity | NOT ALLOWED (additionalProperties: false) |
| missing provenance | No provenance on sub-entities | Every statement/evidence MUST have provenance with origin, actor (name + type), generated_at |
| origin field | `origin: author` (for AI-generated) | `origin: machine` (use `author` ONLY for human-curated sidecars) |
| artifact role | `role: evaluated_on` | `role: supporting` (ONLY: subject, supporting, cited) |
| missing metric | `qualitative_value: "..."` alone | MUST also include `metric: "name"` — every observation requires a metric |
| documents target | `stmt:m1 documents stmt:c1` | `documents` object_ref MUST be an artifact (`art:*`), not a statement |
| invented modality | `modality: conditional` | ONLY: `empirical`, `theoretical`, `descriptive`, `normative` — no other values exist |
| invented status | `status: assumed` | ONLY: `asserted`, `retracted`, `superseded`, `under_review` — no other values exist |
| invented claim_strength | `claim_strength: strong` | ONLY: `high`, `medium`, `low` |
| invented extraction_fidelity | `extraction_fidelity: exact` | ONLY: `high`, `medium`, `low` |
| invented locator_type | `locator_type: abstract` | ONLY: `fragment`, `xpath`, `css`, `line_range`, `page_range`, `table`, `figure`, `section`, `paragraph`, `other` |
| invented coverage.statements | `statements: complete` | ONLY: `exhaustive`, `main_claims_only`, `key_claims_and_limitations`, `partial` |
| invented coverage.evidence | `evidence: full` | ONLY: `exhaustive`, `key_evidence_only`, `partial` |
| invented update_policy | `update_policy: static` | ONLY: `immutable`, `versioned`, `rolling` |
| invented origin | `origin: generated` | ONLY: `author`, `machine`, `imported` |
| invented provenance.method | `method: auto` | ONLY: `extraction`, `manual_curation`, `conversion`, `import` |
| invented Locator.type | `type: file` | ONLY: `url`, `git`, `path`, `doi`, `other` |
| invented record_status | `record_status: draft` | ONLY: `active`, `retracted`, `superseded`, `deprecated` |
| invented venue_type | `venue_type: journal` | ONLY: `published`, `preprint`, `under_review`, `in_preparation`, `technical_report`, `thesis`, `book`, `other` |
| invented citation_intent | `citation_intent: references` | ONLY: `supports`, `extends`, `uses_method`, `compares_to`, `contradicts`, `reviews`, `cites_data`, `background`, `other` |

**CRITICAL YAML rules:**
- Numbers MUST be unquoted: `value: 22` not `value: '22'` or `value: "22"`
- Strings with special chars need quotes: `text: "The 3:1 ratio"`
- **Nested quotes**: If text contains `"`, use single-quote wrapping: `title: 'Why "money" matters'` — NEVER nest double quotes inside double quotes
- actor.type is ONLY `person`, `org`, or `tool` — NEVER `ai`, `llm`, `model`, `agent`
- **Output ONLY raw YAML** — no markdown fences (` ``` `), no XML tags, no preamble text, no explanation before or after
- If sanitization is needed after generation, run `python3 scripts/sanitize.py`

---

