# survey-narrative — Reference Contract

**Status**: v1.0. Multi-record synthesis sub-skill — composes academic prose grounded in the statements of N retrieved sidecars.

> **Companion**: `sub-skills/survey-narrative/SKILL.md`. Contract wins on disagreement.
>
> **Canonical LLM prompt**: `survey-narrative-prompt.md`. Use that prompt verbatim — it operationalizes the contract here (citation-grounding, word-count discipline, hallucination-refusal triggers) and adds prose-padding banned-phrase enforcement so individual agents do not re-derive the rules.

---

## 1. Purpose and scope

Compose 1-3 paragraphs of polished academic prose for a related-work / background section, every substantive sentence ending with a `\cite{key}` keyed to a retrieved sidecar.

**Out of scope (load-bearing)**:

- Cross-discipline narrative blending without explicit `discipline` filter.
- LaTeX `bibitem` generation (call `paper-finder bibtex` route on same `rid_set`).
- Auto-tone matching to user's draft.
- Evaluative claims about retrieved papers ("X is the best"/"Y is flawed") — neutral synthesis only.

---

## 2. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `query_text` | string | yes (OR `rid_set`) | Topic for paper-finder retrieval |
| `rid_set` | list[record_id] | yes (OR `query_text`) | Pre-supplied RIDs; skip retrieval |
| `top_k` | int | no (default 8) | Hard cap 15 for narrative coherence |
| `target_words` | int | no (default 200) | Soft target; output ∈ [100, 400] |

`query_text` AND `rid_set` both supplied → `invalid_slot_type.<second>` per §1.5 OR-pair rule.

---

## 3. Output schema

```jsonc
{
  "topic_or_rid_set": "<echo of input>",
  "paragraphs": [
    "<Markdown paragraph with \\cite{...} keys>",
    /* 1-3 paragraphs */
  ],
  "citation_keys": [
    {
      "key": "vaswani2017",                    // {first_author_lastname}{year} OR record_id-slug if anonymous
      "rid": "knows:vaswani/attention/1.0.0",
      "n_citations_in_prose": 2
    }
  ],
  "ungrounded_sentences_dropped": <int>,       // sentences the LLM proposed but couldn't ground; dropped
  "manifest_path": "<path>"
}
```

**Hard rules**:

- Total grounded sentences (sentences ending with `\cite{}`) ≥ 2. If post-grounding the prose has < 2 grounded sentences, abstain.
- Every `\cite{key}` MUST appear in `citation_keys[]`.
- Every `citation_keys[].rid` MUST appear in manifest's `returned_rids` (no inventing references).
- Word count ∈ [100, 400]. Out-of-bound output is regenerated once; second failure → return as-is with manifest warning.

---

## 4. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| Both `query_text` AND `rid_set` supplied | `invalid_slot_type.<second>` |
| Neither supplied | `missing_required_input.query_text` |
| `query_text` empty / `rid_set` empty list | `invalid_slot_type.<slot>` |
| API search returns 0 hits (`query_text` mode) | `empty_working_set_after_profile_filter` (no-hits tie-breaker) |
| All hits dropped by G7 / G2' | `empty_working_set_after_profile_filter` / `_quality_filter` |
| Generated prose has < 2 `\cite{}` after agent refusal | `empty_working_set_after_quality_filter` (effective grounding empty) |
| LLM produces a `\cite{key}` not in retrieved set | regenerate once → `skill_runtime_exception.UngroundedCitation` |

---

## 5. Hallucination-refusal triggers

The LLM body MUST refuse to write a sentence under any of these conditions; instead omit the sentence:

1. **Cross-paper conclusion not stated in any single sidecar** — e.g. "These methods all share X" when X isn't in any retrieved record. Use cautious phrasing ("Several papers report ...") OR omit.
2. **Empirical numbers not present in retrieved statements** — never make up percentages / metrics / dataset sizes. If a number is needed but not found, omit the sentence.
3. **Causal claims** — "X improves Y because Z" requires Z to be in a retrieved statement; otherwise drop the "because Z" clause.
4. **Comparative ranking** — "X outperforms Y on Z" requires both X's and Y's Z-performance numbers to be retrieved; otherwise drop the comparison.

Each refusal increments `ungrounded_sentences_dropped` in the output. If `> 5`, the output SHOULD include a footnote: "synthesis was constrained by retrieval coverage; consider expanding the query".

---

## 6. Citation key derivation

Per `paper-finder bibtex` semantics:

1. If sidecar has `authors[0].name` and `year`: `{lastname_slug}{year}` (e.g. `vaswani2017`).
2. If author is anonymous (`authors[0].anonymous: true`): use record_id slug (e.g. `generated-mimo-llm`).
3. Multiple papers by same `{lastname}{year}`: append `a`, `b`, `c` deterministically by record_id sort order.
4. Special chars in lastname → strip to `[a-z]` (e.g. "Müller" → `muller`).

The orchestrator post-validates uniqueness — duplicate keys → regenerate with disambiguation.

---

## 7. Fetch-planner contract (G3 default partial)

Per `dispatch-and-profile.md` G3, this skill defaults to partial fetch:

```
For each kept rid:
  fetch_partial(rid, "statements")     # NOT full record
```

Statements are sufficient for prose synthesis. Full record only fetched if the LLM specifically requests evidence-level grounding (rare for narrative; opt-in via skill-internal flag, NOT user-facing).

Manifest's `fetch_mode_per_rid` MUST be `"partial:statements"` for every rid in default mode. Any `"full"` entry triggers a manifest warning since it indicates the skill body bypassed the G3 default.

---

## 8. Manifest emission contract

```jsonc
{
  "skill": "survey-narrative",
  "intent_class": "synthesize_prose",
  "dispatch_tuple": "(synthesize_prose,{query_text|rid_set},related_work_paragraph)",
  "queries": [<query_text>] | [],
  "returned_rids": [<all hits before filtering>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* skill frontmatter */ },
  "excluded_*": [...],
  "quality_exclusions": [...],
  "fetch_mode_per_rid": { /* all "partial:statements" */ },
  "cache_hits": [...],
  "model": "<llm>",
  "token_cost_estimate": <int>,
  /* skill-specific */
  "ungrounded_sentences_dropped": <int>,
  "n_grounded_sentences": <int>,
  "n_citation_keys": <int>,
  "word_count": <int>
}
```

The output prose MUST embed a footnote at the bottom:

```
> Generated via knows survey-narrative; provenance: <manifest_path>; disclaimer: synthesis grounded only in the {n_kept_records} retrieved sidecars on this topic; broader literature not surveyed.
```

---

## 9. Why this contract is load-bearing

Related-work paragraphs are skim-read by reviewers and influence first impressions of a paper. A paragraph with hallucinated claims or invented citations is a credibility-killer.

The grounding contract (every sentence cites a real retrieved sidecar; numbers/comparisons require explicit support; refusal-on-ungrounded) makes the skill safe to use directly in paper drafts. Without it, the skill is a polished-prose generator that occasionally fabricates references — exactly the opposite of useful.

