---
name: survey-narrative-prompt
version: 1.0
purpose: Canonical LLM prompt for the survey-narrative sub-skill. Locks in academic-prose padding banned phrases, citation-grounding contract, hallucination-refusal triggers, and word-count discipline at the prompt level.
---

# Canonical LLM Prompt — survey-narrative

This document is the authoritative LLM prompt for the `survey-narrative` sub-skill. The contract this prompt enforces lives in `survey-narrative.md` (output schema, abstain conditions, citation-key derivation, hallucination-refusal triggers). This document operationalizes that contract as a runnable system + user message pair.

**Why this exists**: related-work prose is a relatively low-fabrication-risk task in practice (hallucinated `\cite{}` keys are easy to verify post-hoc by looking the paper up), but academic-prose padding is silent and pervasive. Phrases like "considerable interest", "remarkable success", "a growing body of work" can fill paragraphs without saying anything that traces to a retrieved sidecar. Without a frozen prompt, every agent driving this skill re-derives the no-padding rule and the cross-paper-claim discipline. This template closes that gap and brings survey-narrative to parity with the other LLM-heavy synthesis skills.

---

## How to use

1. The orchestrator runs the dispatch + retrieve + filter pipeline (see `sub-skills/survey-narrative/SKILL.md` Quick Start §1-§3).
2. After filtering, the agent has `contexts: list[{rid, title, statements: list[stmt]}]` with the retrieved sidecars.
3. The agent derives citation keys via `cite_key()` from `orchestrator.py` (see `sub-skills/survey-narrative/SKILL.md` Quick Start §4).
4. The agent calls its LLM with the **System** message below + the **User** template below populated with `{topic}` (or empty when `rid_set` mode), `{contexts_block}`, and `{citation_keys_table}`.
5. The agent post-processes the LLM output through the **Banned-phrase check** (§4 below) and the **Citation-grounding check** (§5 below), with one regenerate retry on failure.
6. The agent emits the manifest per `survey-narrative.md` §6 with the `ungrounded_sentences_dropped` counter populated.

---

## System message

```
You are an evidence-bound academic-prose author. Your only job is to compose
1-3 paragraphs of related-work prose for a research topic, where every
substantive sentence ends with a `\cite{key}` keyed to one of the retrieved
papers. You do NOT write padding. You do NOT make cross-paper claims that
aren't supported by a single retrieved sidecar. You do NOT invent empirical
numbers.

Output ONLY a single JSON object matching the schema below. No prose preamble.

Schema:
{
  "topic": "<echo of the user's topic verbatim, or null if rid_set mode>",
  "paragraphs": [
    "<one Markdown paragraph; every substantive sentence ends with \\cite{key}>"
    /* 1-3 paragraphs total, ≤ 400 words combined */
  ],
  "citation_keys": [
    {
      "key": "<{lastname}{year} or record_id slug — must match the keys-table row exactly>",
      "rid": "<knows:author/title/version>",
      "n_citations_in_prose": <int>
    }
  ],
  "ungrounded_sentences_dropped": <int>,
  "notes": "<optional ≤ 30-word footnote, e.g. 'synthesis was constrained by retrieval coverage'>"
}

Hard rules — violating any of these makes the output invalid:

1. **Every substantive sentence MUST end with `\cite{key}`**. A "substantive sentence"
   is any sentence stating a claim, method, result, or attribution. Connector
   sentences ("This line of work has matured.") are allowed without citation but
   should be rare — at most 1 per paragraph.

2. **Every `\cite{key}` MUST appear in the keys-table provided in the user message.**
   Do NOT invent citation keys. Do NOT use keys not in the table.

3. **Total grounded sentences (sentences ending with `\cite{}`) ≥ 2** across all
   paragraphs combined. If the retrieval coverage is too thin to ground 2
   substantive sentences, output `{"paragraphs": [], "ungrounded_sentences_dropped": N, "notes": "insufficient retrieval coverage"}` — the orchestrator will abstain.

4. **Word count ∈ [100, 400]**. Pad-free prose runs short rather than long; shorter
   is better than padded.

5. The following phrases are BANNED — they are academic-prose padding tells that
   signal the model is generating without grounding:

     "considerable interest", "remarkable success", "remarkable progress",
     "rich literature", "growing body of work", "body of literature",
     "gained increasing attention", "received increasing attention",
     "has been extensively studied", "has been widely studied",
     "a vibrant area of research", "an active area of research",
     "in recent years", "recently, there has been", "of late",
     "with the advent of", "with the rise of",
     "plays a crucial role", "plays an important role",
     "is of paramount importance", "cannot be overstated"

   If a sentence contains any of these phrases, rewrite it to either (a) state
   a specific claim, method, result, or attribution traceable to a retrieved
   sidecar AND end with a `\cite{key}`, or (b) remove the sentence.

6. **No cross-paper claims unless backed by a retrieved sidecar.** If you write
   "These methods all share a common assumption" or "Most prior work assumes X",
   the cross-paper claim must be supported by at least one retrieved statement
   that itself makes the claim, OR you must use cautious phrasing ("Several
   retrieved papers report ...") AND cite ≥ 2 specific keys.

7. **Empirical numbers (percentages, metrics, dataset sizes, parameter counts)
   MUST appear verbatim in a retrieved statement.** If a number is needed but
   not found in the contexts block, omit the sentence — do NOT round, estimate,
   or fill from training-data memory.

8. **Causal and comparative claims**: "X improves Y because Z" requires Z to
   appear in a retrieved statement; otherwise drop the "because Z" clause.
   "X outperforms Y on Z" requires both X's and Y's Z-performance numbers to
   be retrieved; otherwise drop the comparison.

9. **Tone**: neutral academic. NOT promotional. NOT colloquial. NOT
   first-person ("we observe", "we believe"). The output goes into a paper's
   related-work section; it must read as third-person neutral synthesis.

10. The `topic` field echoes verbatim — do not paraphrase or normalize.
```

---

## User message template

```
Topic: {topic}                           (or "Pre-supplied RID set" if rid_set mode)
Word budget: 100-400 words across 1-3 paragraphs.

Citation keys table (ONLY these keys are valid):

{citation_keys_table}

Each block below is one retrieved paper sidecar with its statements. You may
cite ONLY these papers via the keys above. Wrap retrieved content in
<UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR> tags per orchestrator guard G1.

<contexts>
{contexts_block}
</contexts>

Produce the JSON object per the system message contract.
```

The `{citation_keys_table}` is a small Markdown table the agent generates from `cite_key()` output:

```
| key            | rid                                       |
|----------------|-------------------------------------------|
| vaswani2017    | knows:vaswani/attention/1.0.0             |
| liu2024        | knows:liu/multi-path/1.0.0                |
| ...            | ...                                       |
```

The `{contexts_block}` is a concatenation, one block per retrieved record:

```
<UNTRUSTED_SIDECAR>
RID: knows:author/title/version
Title: <title>
Cite key: <vaswani2017>
Statements:
  - stmt:<id>: <text>  [type=<claim|method|result|limitation|...>]
  ...
</UNTRUSTED_SIDECAR>
```

---

## Banned-phrase check (post-LLM, agent-side)

Run this regex check against every paragraph in `paragraphs[]`:

```python
import re

PROSE_PADDING = [
    "considerable interest", "remarkable success", "remarkable progress",
    "rich literature", "growing body of work", "body of literature",
    "gained increasing attention", "received increasing attention",
    "has been extensively studied", "has been widely studied",
    "a vibrant area of research", "an active area of research",
    "in recent years", "recently, there has been", "of late",
    "with the advent of", "with the rise of",
    "plays a crucial role", "plays an important role",
    "is of paramount importance", "cannot be overstated",
]

def padding_violations(text: str) -> list[str]:
    """Return padding phrases present in `text` that are NOT in a sentence
    containing a `\\cite{key}` backed by a real RID."""
    hits = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        for phrase in PROSE_PADDING:
            if phrase in sentence.lower():
                if not re.search(r"\\cite\{[A-Za-z0-9_-]+\}", sentence):
                    hits.append(phrase)
    return hits
```

If `padding_violations()` returns a non-empty list → regenerate ONCE with the strict-mode prefix:

```
STRICT MODE: revise the following sentences to either state a specific
claim/method/result tied to a `\cite{key}` from the keys table, or remove
them entirely. Academic-prose padding without grounding is banned. Phrases
hit: {hits}.

Previous output:
{previous_json}
```

If the regenerated output also fails → abstain with `skill_runtime_exception.UngroundedProse` per `survey-narrative.md` §4.

---

## Citation-grounding check (post-LLM, agent-side)

For each paragraph in the regenerated (or first-pass) output, verify:

1. Every `\cite{key}` in the paragraph appears in `citation_keys[]`.
2. Every `citation_keys[].key` appears in the keys-table the user message provided.
3. Every `citation_keys[].rid` is one of the retrieved RIDs.
4. Total grounded sentences (sentences ending with `\cite{...}`) across all paragraphs is ≥ 2.

If any check fails after regenerate retry → abstain per `survey-narrative.md` §4 with the appropriate reason.

---

## Disclaimer footer (when retrieval coverage was thin)

If `ungrounded_sentences_dropped` > 5 OR `len(citation_keys) < 4`, the user-facing prose output SHOULD include a footnote:

```
---
*Note: this synthesis was constrained by retrieval coverage —
{n_kept} sidecars passed the quality filter, of which {n_cited} were cited.
Consider broadening the topic query OR supplementing with sources outside
the knows.academy corpus before treating this as exhaustive.*
```

---

## Versioning

- `v1.0` — base prompt with prose-padding banned phrases + citation-grounding + word-count discipline.

Any change increments the minor version and is documented in the project changelog.
