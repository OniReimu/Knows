# scoop-check — Reference Contract

**Status**: v1.0. Without the worst-case aggregation, the grounding requirement, and the thin-coverage abstain defined here, this skill degrades into a confident novelty verdict that a researcher believes and acts on — the single most expensive silent failure in early-stage research.

> **Companion**: `sub-skills/scoop-check/SKILL.md` (operational quick start). When this contract and SKILL.md disagree, **this contract wins**.
>
> **Canonical LLM prompt**: `scoop-check-prompt.md`. Use it verbatim — it operationalizes the four-axis decomposition, cited-span requirement, worst-case aggregation, value read, verdict taxonomy, banned phrases, and disclaimer defined here.

---

## 1. Purpose and scope

Given a **candidate research idea** (natural-language paragraph, no paper yet), report how close it sits to published prior work and whether it is worth pursuing. The unit of analysis is a *proposed contribution*, not an existing paper.

**Out of scope (load-bearing)**:

- Scoring an existing paper's novelty — that is a review task (`review-sidecar`).
- Live web / Scholar / arXiv retrieval — hub-only in v1; the coverage bound is disclaimed, not hidden.
- A scalar "impact score" — the value read is qualitative and evidence-cited; a number invites false precision.
- Corpus-wide novelty proof — recall is bounded by top-K retrieval and MUST be disclaimed.

---

## 2. Input contract

| Field | Type | Required | Notes |
|---|---|---|---|
| `idea_text` | string | yes | The candidate idea, 1-2 paragraphs; non-empty after strip. Must be concrete enough to name a *mechanism*, not only a topic. |
| `top_k` | int | no (default 12) | Hard cap 24. Closest prior work to collide against. |
| `min_coverage` | int | no (default 3) | Coverage floor for a CONFIDENT novel verdict. Below it, a would-be PURSUE is downgraded to `PURSUE (UNCONFIRMED)` — NOT a hard abstain. Only 0 hits (after a broaden-retry) hard-abstains. A collision verdict stands at any count. |

An `idea_text` that names only a topic ("something about long-context RL") with no mechanism cannot be decomposed into four axes → abstain `IdeaTooVague` (§4). This is deliberate: a vague idea reads as maximally novel for the wrong reason (it collides with nothing because it says nothing), which is exactly the "novel-but-empty" trap.

---

## 3. The four axes and the level scale

Decompose `idea_text` into four axes:

| Axis | Question it answers |
|---|---|
| `problem_framing` | What problem / setting does the idea target? |
| `core_mechanism` | What is the technical move that does the work? |
| `key_insight` | What non-obvious reason makes it work? |
| `application_domain` | Where does it apply? |

For each retrieved prior paper P, mark each axis MATCHED or DISTINCT. `level(P) = 5 − |matched axes of P|`.

**Aggregation is worst-case**: the reported `novelty_level = min over retrieved P of level(P)`. Never average. A single paper matching all four axes scoops the idea (level 1) no matter how novel it looks against the rest — averaging would dilute a decisive collision with unrelated hits and inflate novelty. This mirrors the paper's Scoop-Check rationale: take the minimum, because one sufficiently close prior work is enough.

---

## 4. Output schema

```jsonc
{
  "idea_summary": "<one-sentence restatement of the candidate idea>",
  "axes": {
    "problem_framing": "<the framing extracted>",
    "core_mechanism": "<the mechanism extracted>",
    "key_insight": "<the insight extracted>",
    "application_domain": "<the domain extracted>"
  },
  "closest_prior": [
    {
      "rid": "knows:author/title/version",
      "title": "<title>",
      "matched_axes": ["core_mechanism", "application_domain"],
      "evidence": [
        {
          "axis": "core_mechanism",
          "stmt_id": "stmt:<id>",
          "verbatim_quote": "<≤30-word exact substring of the cited statement's text>"
        }
      ],
      "level": 3
    }
    /* sorted by ascending level (closest scoop first) */
  ],
  "novelty_level": 3,               // = min over closest_prior[].level (worst case)
  "value_read": {
    "gap_real_and_important": "<yes/no/uncertain + ≤25 words, cited when yes>",
    "non_obvious": "<yes/no/uncertain + ≤25 words>",
    "mechanism_closes_gap": "<yes/partially/no + ≤25 words>"
  },
  "verdict": "PURSUE | DIFFERENTIATE | ALREADY DONE",
  "verdict_detail": "<PURSUE: the novelty-carrying axis. DIFFERENTIATE: closest RID + axis to sharpen. ALREADY DONE: scooping RID + one-line subsumption argument.>",
  "coverage_disclaimer": "This collision check is bounded by hub coverage — it retrieved the top-K closest paper@1 sidecars (here K={top_k}) and matched against them. A 'novel' verdict means no scoop was found within that coverage, not that none exists.",
  "manifest_path": "<path to manifest.json>"
}
```

**Hard rules**:

- Every MATCHED axis MUST carry ≥1 `evidence` entry whose `verbatim_quote` is a substring of the cited statement's `text` (after whitespace normalization). An axis marked matched without a cited span is invalid — drop the match (see §5 on which direction to fail).
- `novelty_level` MUST equal `min(closest_prior[].level)`. A reported level that does not equal the min of the per-paper levels is malformed.
- `closest_prior` is sorted ascending by `level` (the scooping paper, if any, is first).
- `verdict` MUST be consistent with `novelty_level`: PURSUE requires level ≥ 4; ALREADY DONE requires some paper at level ≤ 2; level 3 is DIFFERENTIATE.
- `coverage_disclaimer` is mandatory.

---

## 5. Which direction to fail — a note specific to this skill

`next-step-advisor` fails toward *fewer* candidates (drop the ungrounded one). A collision checker cannot borrow that rule directly: dropping an unsupported *axis match* fails toward MORE novelty, which is the dangerous direction here (it hides a possible scoop). So the rule is inverted:

- An axis the LLM claims MATCHED but cannot cite → **drop the match but lower confidence and keep the paper in `closest_prior` flagged `uncertain`**, and never let dropping it *raise* the reported novelty level above what the cited matches already establish.
- When evidence is genuinely ambiguous, the verdict floors at **DIFFERENTIATE**, not PURSUE. A student is better served by "sharpen this against X" than by a false "go ahead."

---

## 6. Hard abstain conditions

| Condition | `abstained_reason` |
|---|---|
| `idea_text` missing or empty | `missing_required_input.idea_text` |
| `idea_text` names no mechanism (undecomposable) | `skill_runtime_exception.IdeaTooVague` |
| Working set empty after G7/G2' | `empty_working_set_after_profile_filter` / `empty_working_set_after_quality_filter` |
| **< `min_coverage` relevant paper@1 sidecars** | `empty_working_set_after_quality_filter` (thin coverage → false-novel; recommend Scholar/arXiv pivot) |
| LLM output `novelty_level` ≠ min of per-paper levels after one retry | `skill_runtime_exception.WorstCaseViolation` |
| A MATCHED axis with no substring-valid `verbatim_quote` after one retry | resolve per §5 (downgrade to uncertain), do NOT abstain unless it empties `closest_prior` |

**Abstain output**: structured refusal per `dispatch-and-profile.md` §5 — never silently degrade to "looks novel to me."

---

## 7. Banned novelty-inflation phrases (compile-time check)

Symmetric to `next-step-advisor` §5 but for the opposite bias. If output contains any of these without a `[stmt:* from RID]` citation demonstrating the absence was actually searched, regenerate (one retry; second failure → `skill_runtime_exception.UngroundedNoveltyClaim`):

- `"first to"`, `"no prior work"`, `"nobody has"`, `"unprecedented"`, `"entirely new"`
- `"clearly novel"`, `"highly original"`, `"no one has explored"`, `"novel approach"` (bare)

A novelty claim is only as strong as the retrieval that failed to contradict it. The grounded substitute is a bounded "within the retrieved top-K, no paper matches axis X" — which the coverage disclaimer then qualifies.

---

## 8. Manifest emission contract

Per `dispatch-and-profile.md` §6.1:

```jsonc
{
  "skill": "scoop-check",
  "intent_class": "check_novelty",
  "dispatch_tuple": "(check_novelty,{idea_text},novelty_report)",
  "queries": [<LLM-derived retrieval query>],
  "returned_rids": [<all rids retrieved>],
  "applied_profile_filters": ["paper@1"],
  "applied_quality_policy": { /* frontmatter quality_policy */ },
  "fetch_mode_per_rid": { /* "partial:statements" per G3 */ },
  "model": "<llm model name>",
  "novelty_level": <int 1-5>,
  "n_closest_prior": <int>,
  "axis_matches_dropped": [ { "rid": "...", "axis": "...", "reason": "no_cited_span" } ],
  "verdict": "PURSUE | DIFFERENTIATE | ALREADY DONE",
  "abstained": false,
  "abstained_reason": null
}
```

`axis_matches_dropped` enables auditability — a reviewer can see how many axis matches were downgraded to uncertain (per §5). A large count signals the retrieval was noisy or the idea underspecified.

---

## 9. Why this contract is load-bearing

A wrong "novel" verdict is a *silent* failure with a long fuse: the student cannot verify it until they have written the paper and a reviewer names the scoop. The worst-case aggregation, the cited-span requirement, the inverted fail-direction (§5), the novelty-inflation banned list, and the thin-coverage abstain all exist to convert that silent failure into a loud one at the idea stage — which is the whole reason a researcher runs the check before committing.

If you relax §3 (worst-case), §5 (fail-direction), or §6 (thin-coverage abstain) to make the skill "more encouraging," you have reintroduced exactly the failure this contract prevents.
