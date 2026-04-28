# next-step-advisor — Reference Contract

**Status**: v1.0. Without the abstain rules and banned-phrase enforcement defined here, this skill degrades into plausible-sounding LLM speculation that damages user trust at scale.

> **Companion**: `sub-skills/next-step-advisor/SKILL.md` (operational quick start). When this contract and SKILL.md disagree, **this contract wins**.
>
> **Canonical LLM prompt**: `next-step-advisor-prompt.md`. Use that prompt verbatim — it operationalizes the contract here (banned phrases, grounding, schema, disclaimer) so individual agents do not re-derive the rules and silently miss enforcement.

---

## 1. Purpose and scope

Produce an **evidence-backed brief** of N candidate research questions for a user-supplied topic, where each candidate is grounded in specific `question`-typed or `limitation`-typed statements from retrieved sidecars on `knows.academy`.

**Out of scope (load-bearing)**:

- Corpus-wide gap detection — recall is bounded by top-K retrieval (default K=12), and the contract MUST disclaim this.
- Speculative ideation — every candidate question MUST cite at least one specific `stmt:*` from at least one retrieved record.
- Multi-topic blending in one call.
- Funding-feasibility scoring or novelty estimation.
- Time-windowed analysis ("after ICLR 2026 ended").

---

## 2. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `query_text` | string | yes | Research area; non-empty after strip |
| `top_k` | int | no (default 12) | Hard cap 25 |
| `min_grounding_evidence` | int | no (default 3) | Total `question` + `limitation` statements across all retrieved records; if below threshold → abstain |

`query_text` longer than ~256 chars triggers `invalid_slot_type.query_text` (the orchestrator's typed dispatch already rejects, but this contract documents the boundary).

---

## 3. Output schema

```jsonc
{
  "topic": "<echo of query_text>",
  "candidates": [
    {
      "question": "<string, 1-2 sentences, must end with `?`>",
      "rationale": "<string, ≤30 words, why this is open>",
      "supporting_refs": [
        {
          "rid": "knows:author/title/version",
          "stmt_id": "stmt:<descriptive-name>",
          "statement_type": "question | limitation",
          "verbatim_quote": "<≤30 words from the cited statement, exact substring>"
        }
      ]
    }
    /* 1-5 candidates total, never more than 5 */
  ],
  "evidence_inventory": {
    "n_question_statements": <int>,
    "n_limitation_statements": <int>,
    "n_kept_records": <int>,
    "n_searched_records": <int>
  },
  "heuristic_disclaimer": "This brief is heuristic, not corpus-wide. Recall is bounded by the top-K retrieved sidecars (here K={top_k}) and their `question`/`limitation` coverage. A gap not surfaced here may still exist in the broader literature.",
  "manifest_path": "<path to manifest.json>"
}
```

**Hard rules**:

- `candidates[]` length ∈ [1, 5]. Zero candidates → abstain. More than 5 → truncate at 5 with rationale ordering preserved (most-grounded first).
- Every candidate's `supporting_refs` MUST be non-empty (≥ 1).
- Every `verbatim_quote` MUST be a substring of the cited statement's `text` field (case-sensitive after whitespace normalization).
- The `heuristic_disclaimer` field is **mandatory** — output without it is malformed and the consumer MUST treat it as an error.

---

## 4. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `query_text` missing or empty | `missing_required_input.query_text` |
| `query_text` over 256 chars | `invalid_slot_type.query_text` |
| Working set empty after G7/G2' filter | `empty_working_set_after_profile_filter` / `empty_working_set_after_quality_filter` |
| **Total `question` + `limitation` statements across kept records < `min_grounding_evidence`** | `empty_working_set_after_quality_filter` (with detail "insufficient grounding evidence: N total Q/L statements, threshold M") |
| LLM produces > 5 candidates after one regenerate retry | `skill_runtime_exception.OvergeneratedCandidates` |
| LLM produces a candidate without ≥1 cited `stmt:*` after one regenerate retry | `skill_runtime_exception.UngroundedCandidate` |
| LLM produces a `verbatim_quote` that doesn't substring-match the cited statement after one regenerate retry | `skill_runtime_exception.QuoteMismatch` |

**Abstain output**: structured refusal per `dispatch-and-profile.md` §5 — orchestrator returns the `abstained_reason` + manifest pointer to the user; never silently degrades to "here are some thoughts anyway".

### 4.1 Topical-relevance precheck (intersection queries)

The numeric `min_grounding_evidence` threshold in §4 is necessary but NOT sufficient for **intersection-typed queries** — queries that combine two distinct concepts (e.g., "differential privacy AND code generation models", "RLHF for medical imaging", "interpretability of mixture-of-experts"). For such queries, a niche intersection may have many `question`/`limitation` statements that touch ONE side of the intersection but ZERO statements touching BOTH. Without a precheck, the LLM becomes the last line of defense against cross-paper speculation — exactly the trust assumption §10 says is unsafe.

**Rule**:

1. The orchestrator detects intersection-typed queries by simple parsing: query contains `"and"`, `"&"`, `"×"`, `" x "`, or two distinct noun phrases joined by a preposition (`"X for Y"`, `"X in Y"`, `"X applied to Y"`).
2. From the intersection, extract two terms `A` and `B` (case-folded, stop-words removed).
3. Count statements whose `text` field contains lexical evidence of BOTH `A` and `B` (case-insensitive substring match, OR a known synonym from a small predefined list — `"DP"` ↔ `"differential privacy"`, `"LLM"` ↔ `"large language model"`, etc.).
4. If that count is below `min_topical_grounding` (default **1**) → abstain with `empty_working_set_after_quality_filter` and detail `"intersection query <A> × <B>: N statements name both, threshold M"`.

This precheck runs BEFORE the LLM call so the LLM is never asked to invent a cross-paper synthesis.

**Why default 1 not 0**: a single statement co-naming both terms is the minimum evidence that ANY paper in the working set has thought about the intersection at all. Below that, any candidate the LLM produces is necessarily speculation — the orchestrator's grounding trace (§6) and banned-categories check (§7) would catch it post-hoc, but pre-empting at the precheck saves an LLM call and a regenerate retry.

**Non-intersection queries** (single concept, e.g., "diffusion models" or "RLHF") skip this precheck entirely.

---

## 5. Banned phrases (compile-time string check before output)

If the LLM output contains any of these phrases without a `[stmt:* from RID]` citation in the same sentence, the consumer MUST regenerate (single retry); on second failure → `skill_runtime_exception.UngroundedSpeculation`.

**Banned phrase list** (case-insensitive substring match):

- `"could explore"`
- `"might investigate"`
- `"promising direction"`
- `"future work could"`
- `"this opens up"`
- `"intriguing avenue"`
- `"underexplored"`
- `"ripe for"`
- `"ample opportunity"`
- `"warrant investigation"`
- `"worth exploring"`
- `"natural next step"` (use `"next-step"` only when grounded in a cited limitation)
- `"low-hanging fruit"`
- `"rich vein"`
- `"deserves attention"`

These are the speculation tells that signal the LLM is generating without grounding. Each one has a citation-bearing variant — agent rewrites the sentence to either back the claim with a `[stmt:*]` reference or omit the sentence entirely.

**Enforcement**: orchestrator runs the banned-phrase check post-LLM; on hit, prepends "STRICT MODE: revise the following sentences to include a [stmt:*] citation OR remove them entirely. Do not output any banned phrase without grounding: ..." to the user message and re-calls the LLM. One retry only.

---

## 6. Grounding contract

Every candidate question MUST satisfy this trace:

```
candidate.question
  ⤷ supporting_refs[i].stmt_id (at least one)
       ⤷ retrieved_record[supporting_refs[i].rid]
            ⤷ statement_type ∈ {question, limitation}
            ⤷ text contains verbatim_quote (substring match)
```

If ANY hop fails for any candidate, the candidate MUST be dropped. After dropping ungrounded candidates, if total candidates = 0, abstain per §4.

The grounding check is run by the orchestrator **after** the LLM returns, not by the LLM itself (the LLM cannot be trusted to self-validate). Implementation: post-process JSON, cross-reference each `stmt_id` against the retrieved sidecar payloads in memory.

---

## 7. Banned candidate categories

These are categories of "next-step questions" that are seductive but speculative and MUST NOT appear in output even if cited:

- **"Replicate X on dataset Y"** — replication is engineering, not research direction. Reject unless the cited statement specifically calls for replication.
- **"Apply X to domain Y"** — too generic; reject unless cited limitation specifically names domain Y.
- **"Improve X by 5%"** — quantitative-target candidates without methodological insight. Reject unless cited statement names the target gap.
- **"Combine X and Y"** — combinations without specific mechanism. Reject unless cited limitation names both X and Y as a known gap.

These rejections are run after the banned-phrase check, before final output.

---

## 8. Manifest emission contract

Per `dispatch-and-profile.md` §6.1, the manifest MUST include:

```jsonc
{
  "skill": "next-step-advisor",
  "intent_class": "brief_next_steps",
  "dispatch_tuple": "(brief_next_steps,{query_text},next_step_brief)",
  "queries": [<query_text>],
  "returned_rids": [<all rids retrieved by paper-finder semantics>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* this skill's frontmatter quality_policy */ },
  "fetch_mode_per_rid": { /* all "partial:statements" per G3 default */ },
  "model": "<llm model name>",
  /* skill-specific extensions */
  "evidence_inventory": {
    "n_question_statements": <int>,
    "n_limitation_statements": <int>,
    "n_kept_records": <int>,
    "n_searched_records": <int>
  },
  "candidates_dropped_post_llm": [
    { "reason": "ungrounded" | "banned_phrase" | "banned_category", "snippet": "<truncated candidate text>" }
  ],
  "abstained": false,
  "abstained_reason": null
}
```

`candidates_dropped_post_llm` enables auditability — users / reviewers can see how many candidates were silently filtered after the LLM produced raw output. If `len(candidates_dropped_post_llm) > 5`, the skill SHOULD also log a warning that "the LLM appears to be speculating heavily on this topic; consider whether the topic itself is a good fit".

---

## 9. Versioning

This contract is versioned independently of the catalog. Changes to:

- Output schema (§3)
- Hard abstain conditions (§4)
- Banned phrase list (§5)
- Grounding contract (§6)
- Banned candidate categories (§7)

require a minor version bump and a re-run of any integration tests that depend on this contract. Adding new banned phrases is patch-level; removing one is minor (it relaxes the contract).

The orchestrator's dispatch entry MUST pin the contract version it expects (recorded in manifest as `next_step_advisor_contract_version`). Mismatch between expected and shipped contract is `skill_runtime_exception.ContractVersionMismatch`.

---

## 10. Why this contract is load-bearing

`next-step-advisor` answers the question "what should I research next?" — a question with no objective ground truth. The user has no way to immediately verify the answer. Without strict grounding + abstain rules, the failure mode is **plausible-sounding bullshit that wastes the user's time** (or worse: misdirects their PhD).

The failure mode here is **silent** — a user cannot tell a grounded recommendation from a speculative one until they've spent weeks pursuing it. The banned-phrase enforcement, the grounding-trace check, the heuristic disclaimer, and the abstain-on-low-evidence rule are all designed to make that silent failure mode loud.

If you find yourself relaxing any of §4-§7 to make the skill "more useful", you are reintroducing the failure mode this contract was written to prevent.
