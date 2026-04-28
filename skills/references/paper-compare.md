# paper-compare — Reference Contract

**Status**: v1.0.

> **Companion**: `sub-skills/paper-compare/SKILL.md`. Contract wins on disagreement.

---

## 1. Purpose and scope

Pairwise depth-comparison of two `paper@1` sidecars: shared claims, divergent claims, contradictions (via relation graph), shared citations.

**Out of scope (load-bearing)**:

- N-way comparison (3+ papers) — use `survey-table`.
- Cross-profile diff (paper@1 vs review@1) — different intent_class.
- LLM-judged "which paper is better" — neutral diff only.

---

## 2. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `rid_pair` | tuple[record_id, record_id] | yes | Both must be `paper@1` after G7 filter; `rid_a == rid_b` is a degenerate self-diff |
| `similarity_threshold` | float | no (default 0.85) | Cosine / LLM-judge threshold for "shared claim" detection; ∈ [0.5, 1.0] |

---

## 3. Output schema

```jsonc
{
  "rid_a": "knows:...",
  "rid_b": "knows:...",
  "shared_claims": [
    {
      "stmt_a_id": "stmt:foo",
      "stmt_b_id": "stmt:bar",
      "similarity_score": 0.92,
      "match_method": "text_overlap" | "llm_judge",
      "shared_text_summary": "<≤ 50 word neutral summary of the shared claim>"
    }
  ],
  "divergent_claims": {
    "only_in_a": [
      {"stmt_id": "stmt:...", "text": "<verbatim claim text>", "type": "claim|method|limitation"}
    ],
    "only_in_b": [
      {"stmt_id": "stmt:...", "text": "<verbatim>", "type": "..."}
    ]
  },
  "contradictions": [
    {
      "subject_rid": "<rid_a or rid_b>",
      "subject_stmt_id": "stmt:...",
      "predicate": "challenged_by | supersedes | retracts",
      "object_rid": "<rid_a or rid_b>",
      "object_stmt_id": "stmt:...",
      "evidence_anchor": "<rel:* id from source sidecar>"
    }
  ],
  "shared_citations": [
    {
      "art_id": "art:wang-self-consistency",
      "rid_a_role": "cited",
      "rid_b_role": "cited"
    }
  ],
  "manifest_path": "<path>"
}
```

---

## 4. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `rid_pair` missing or wrong shape | `missing_required_input.rid_pair` / `invalid_slot_type.rid_pair` |
| `rid_a == rid_b` (self-diff) | `invalid_slot_type.rid_pair` |
| Either rid 404s | `rid_not_found.<rid>` |
| Either record fails G7 (e.g. one is `review@1`) | `empty_working_set_after_profile_filter` |
| Either record fails G2' quality | `empty_working_set_after_quality_filter` |

---

## 5. Diff semantics

### 5.1 Shared claims

Two statements `(stmt_a_id, stmt_b_id)` are "shared" iff **either**:

- **LLM-judge mode (default)**: LLM returns "yes, semantically equivalent" given both texts side-by-side. More accurate; needed for cross-terminology matches where two papers describe the same concept with different vocabulary. Returns `llm_judge_payload` for the agent to call its LLM, then merge via `finalize_paper_compare(initial_result, judgments)`.
- **Text-overlap mode (opt-in via `--text-overlap` / `match_method="text_overlap"`)**: cosine similarity of `text` fields ≥ `similarity_threshold`. Deterministic, no LLM. Use for CI smoke tests or one-shot deterministic answers. Misses cross-terminology shared concepts.

The `match_method` field records which was used. `llm_judge` is the default because text-overlap can return zero shared pairs on obviously-related papers when terminology differs.

Each statement appears in at most one shared pair (greedy matching by descending similarity).

### 5.2 Divergent claims

After shared-pair extraction, every remaining statement on side A is `only_in_a`; every remaining on side B is `only_in_b`.

`type` filter: only `claim`, `method`, `limitation` statement types are reported as divergent (assumptions and definitions are usually shared by convention).

### 5.3 Contradictions

A contradiction is a `relations[]` edge with `predicate ∈ {challenged_by, supersedes, retracts}` where:

- `subject_ref` is a `stmt:*` in one sidecar
- `object_ref` is a `stmt:*` in the OTHER sidecar (cross-record reference, qualified by `rid#stmt:*`)

The relation must originate in one of the two compared sidecars (not from a third party). If both sidecars assert contradictions about each other, both are reported.

### 5.4 Shared citations

Intersection of `{art_id : artifact.role == "cited"}` between the two sidecars. Match on `art_id` AND `identifiers.doi` / `arxiv` / `url` (any one matching counts).

---

## 6. Relation-edge profile-mismatch handling

If a `relations[]` edge in either sidecar references a `review@1` rid via `object_ref`, the edge is silently skipped (cross-profile relations are out of scope). Manifest records the skip with `cross_profile_relations_skipped: <count>`.

---

## 7. Manifest emission contract

```jsonc
{
  "skill": "paper-compare",
  "intent_class": "diff",
  "dispatch_tuple": "(diff,{rid_pair},diff_report)",
  "returned_rids": [rid_a, rid_b],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* frontmatter */ },
  "fetch_mode_per_rid": {<rid_a>: "full", <rid_b>: "full"},
  "model": "<llm if LLM-judge mode used>",
  /* skill-specific */
  "n_shared_claims": <int>,
  "n_only_in_a": <int>,
  "n_only_in_b": <int>,
  "n_contradictions": <int>,
  "n_shared_citations": <int>,
  "match_method_used": "text_overlap" | "llm_judge",
  "cross_profile_relations_skipped": <int>
}
```

---

## 8. Why this contract is load-bearing

Pairwise diffs are foundational for understanding research lineage, identifying replications, and surfacing genuine disagreements between papers. A buggy diff (e.g. missing a contradiction edge, or false-positive shared claims) leads users to incorrect conclusions about the relationship between two works.

The greedy-matching rule + cross-profile skip + explicit `match_method` recording make the diff reproducible and auditable. The `verbatim` text preservation (no LLM paraphrasing) ensures users see what each paper actually said.

