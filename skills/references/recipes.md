# Knows Recipes — common cross-skill chains

> Moved out of `SKILL.md` for context efficiency. The SKILL.md body keeps a one-line
> index; read THIS file when actually executing a multi-skill chain.

## Recipes — common cross-skill chains

Many real research workflows take more than one sub-skill. Below are the canonical chains. Use these as templates — running them in the listed order saves an LLM call (or saves a wasted one when the upstream step would have abstained anyway).

> **v0.11+ chain pattern (Type B → Type A)**: stance skills under `stances/` chain into Type A emitters via fenced `brainstorm_summary` handoff. Stance does free dialogue + opinion + multi-turn convergence; emitter does mechanical translation + grounding verification + YAML emit. The stance fails closed (`status: needs_rework`) when grounding can't be verified. Recipe 9 below demonstrates the canonical case (`paper-brainstorm` → `commentary-builder`); the same shape applies to `review-prep` → `review-sidecar`, `rebuttal-prep` → `rebuttal-builder`, `pitch-grill` → `sidecar-author`, `survey-shape` → `survey-narrative`/`survey-table`. See `stances/README.md` § "How a stance hands off to its paired emitter" for the full schema.

### Recipe 1: `coverage-check → next-step-advisor`

User asks "what should I work on next in `<topic>`?" or "where are the open gaps in `<topic>`?"

```bash
# Step 1 — pre-flight: is the hub rich enough to ground a brief?
python3 scripts/orchestrator.py coverage-check "<topic>"
#   verdict ∈ {RICH, MODERATE} → proceed to Step 2
#   verdict ∈ {THIN, ABSENT}   → recommend pivoting (Scholar / arXiv) before committing
#                                 — do NOT call next-step-advisor on thin coverage; output will be honestly empty
```

```python
# Step 2 — agent-mediated next-step-advisor (Quick Start in sub-skills/next-step-advisor/SKILL.md)
# Use the canonical prompt: references/next-step-advisor-prompt.md
# It enforces banned phrases + grounding trace + heuristic disclaimer + (for intersection
# topics like "DP × code-LLMs") the §4.1 topical-relevance precheck.
```

**Why this chain**: a 2-second `coverage-check` saves a 30-second LLM call when the topic is off-corpus. Bigger win: prevents the "polished-sounding ungrounded brief" failure mode the contract was designed to catch.

### Recipe 2: `sidecar-author Path D → rebuttal-builder` (no-sidecar fallback)

User has a paper PDF but no `.knows.yaml` sidecar yet — the modal junior-PI case under deadline pressure.

```bash
# Step 1 — generate the paper sidecar from PDF (Path D = multimodal LLM read)
python3 scripts/orchestrator.py sidecar-author-pdf my-paper.pdf -o my-paper.knows.yaml
#   The wrapper sanitizes + lints + verifies metadata. Re-run with --no-cited if you want
#   to skip cited-corpus enrichment.
```

```python
# Step 2 — agent-mediated rebuttal-builder using the freshly-generated sidecar + reviewer text
# Use the canonical prompt: references/rebuttal-builder-prompt.md
# It enforces fabrication-tell banned phrases + response-type taxonomy + grounding trace.
# The rebuttal-builder-prompt.md also has a no-sidecar fallback policy if Step 1 isn't viable
# (opt-in unverified-anchors mode with [Sec. X — verify] placeholders).
```

**Why this chain**: the rebuttal contract requires every "we did X" claim to cite a `stmt:*`/`ev:*` anchor in the paper. Without a sidecar, every claim is unverifiable. Step 1 closes that gap with one extra hop.

### Recipe 3: `paper-finder → paper-compare`

User asks "how do `<paper A>` and `<paper B>` differ?" — typical Slack/email-thread question.

```bash
# Step 1 — discover the two RIDs (skip if user already supplied them)
python3 scripts/orchestrator.py paper-finder "<paper A name or topic>" --top-k 3
python3 scripts/orchestrator.py paper-finder "<paper B name or topic>" --top-k 3
#   Pick the right RID from each output. Title-rerank surfaces canonical names at the top.

# Step 2 — pairwise diff (default: llm_judge mode with top-3 candidate-pair preview)
python3 scripts/orchestrator.py paper-compare "knows:<a>/<slug>/1.0.0" "knows:<b>/<slug>/1.0.0"
#   Returns: candidate pairs, divergent claims, contradictions, shared citations.
#   Use --text-overlap if you want a deterministic Jaccard answer (CI smoke or one-shot).
```

**Why this chain**: paper-compare is RID-typed; users almost always have paper names, not RIDs. Rolling the discovery step into the workflow eliminates one round of "what's the RID for X?" friction.

### Recipe 4: `paper-finder → survey-narrative`

User asks "draft me a related-work paragraph on `<topic>`" — typical paper-writing prep.

```bash
# Step 1 — discover candidate sidecars (use --sort claims for richer sidecars in lit-map quality)
python3 scripts/orchestrator.py paper-finder "<topic>" --top-k 8 --sort claims
#   Auto-applies --venue-type published with --sort claims; pass --venue-type preprint to override.
```

```python
# Step 2 — agent-mediated survey-narrative (Quick Start in sub-skills/survey-narrative/SKILL.md)
# Use the cite_key() helper to derive {lastname}{year} keys cleanly:
from orchestrator import cite_key
keys = {h["record_id"]: cite_key(h["record_id"]) for h in hits}
# Synthesize 1-3 paragraphs of academic prose with \cite{key} citations, grounded in retrieved
# statements. Wrap context in <UNTRUSTED_SIDECAR>...</UNTRUSTED_SIDECAR> per G1.
```

**Why this chain**: survey-narrative accepts either `query_text` or pre-supplied `rid_set`. Doing paper-finder first lets the human vet the candidate set before paying for prose synthesis — and surfaces hub coverage gaps explicitly.

### Recipe 5: `paper-finder → survey-table`

User asks "compare these N papers in a table by `<axes>`" — typical lab-meeting / reading-group prep.

This chain is documented in detail at `sub-skills/survey-table/SKILL.md` Quick Start §0. The pattern is the same as Recipe 4: discover RIDs first, abstain explicitly with `hub_missing_canonical_papers` when the canonical reading list isn't on the hub (rather than substituting random hub neighbors). For canonical pre-2024 papers (FlashAttention, PagedAttention, etc.), expect to ground citations outside the hub.

### Recipe 6: `paper-finder → sidecar-reader`

User asks "find papers on `<topic>` and tell me what they say about `<question>`" — high-traffic researcher Q&A pattern, e.g. "what does the recent literature on diffusion guidance say about CFG scale tradeoffs?"

```bash
# Step 1 — discover candidate RIDs on the hub
python3 scripts/orchestrator.py paper-finder "<topic>" --top-k 5
#   Pick the RIDs you want to interrogate. Title-rerank surfaces canonical names at the top.

# Step 2 — ask the same question against each retrieved sidecar (hub mode)
python3 scripts/orchestrator.py sidecar-reader "knows:<a>/<slug>/1.0.0" "<question>"
python3 scripts/orchestrator.py sidecar-reader "knows:<b>/<slug>/1.0.0" "<question>"
#   Repeat per RID. Each call returns a per-paper grounded answer with stmt:*/ev:* anchors.
#   sidecar-reader fetches the sidecar from the hub via G5 transport — no local file required.
```

**Why this chain**: for "what does the recent literature on X say about Y" workflows where the user wants per-paper answers (not synthesized prose). Different from `survey-narrative` (Recipe 4), which produces ONE prose paragraph; this gives N independent answers the user can compare or quote individually. Useful for lit-review note-taking and "did anyone already report Z?" sanity checks.

### Recipe 7: `commentary-builder → next-step-advisor` (gaps when authors are silent) — NEW v0.10

User asks "what's next in `<topic>`" but the seed papers are publication-pressured (no honest gap disclosure in their `limitation`/`question` statements). Default `next-step-advisor` runs surface only author-stated gaps, missing the much larger pool of gaps a careful reader/agent would spot.

```python
# Step 1 — identify seed papers (skip if user supplied them)
hits = fetch_search(TOPIC, sort="trending", limit=12)["results"]
seed_rids = [h["record_id"] for h in hits if h.get("profile") == "paper@1"][:5]

# Step 2 — generate commentary@1 sidecars for each seed (one call per paper)
# Use the canonical prompt at references/commentary-builder-prompt.md.
# Output: <paper>_commentary.knows.yaml conforming to profile: commentary@1.
# Each commentary record has 3-6 reflections (gap_spotted / scenario_extrapolation /
# method_transfer_idea / lesson) anchored via `reflects_on` to paper stmt:* IDs.
# Lint each commentary YAML before publishing — schema enforces commentary@1's
# 4-type statement_type partition.

# Step 2.5 — PUBLISH PREREQUISITE (load-bearing).
# `next-step-advisor` Phase 2 retrieves commentary records via the hub's `/search` endpoint.
# That means the commentary YAML produced in Step 2 MUST be uploaded to the hub before
# Step 3 can consume it. POST `/sidecars` is currently UNVERIFIED (api-schema.md §"Unverified"),
# so commentary@1 sidecars STAY LOCAL until the upload path is wired. In the local-only state,
# Step 3 silently runs paper@1-only and emits the coverage-gap note. To unblock end-to-end
# automation, EITHER (a) wait for hub upload to ship, OR (b) manually upload via the future
# `knows publish <commentary>.knows.yaml` CLI when it lands, OR (c) point next-step-advisor at
# a local-only commentary directory via a future `--local-commentary <dir>` flag (not yet
# implemented in v0.10).

# Step 3 — run next-step-advisor. Its v0.10 retrieval pulls in commentary@1 sidecars via
# the two-phase fetch (Quick Start §3 in next-step-advisor/SKILL.md), BUT only if those
# sidecars are present on the hub. With local-only commentary (the v0.10 default), Phase 2
# yields zero hits and the advisor emits a manifest coverage-gap note recommending publication.
# Evidence pool grows from N (paper@1 only) to N + N×k (k ≈ 3-6 reflections per paper)
# ONLY AFTER commentary upload is wired.
```

**Why this chain**: the value of `commentary-builder` only materializes when consumed downstream. Running it without immediately consuming the output via `next-step-advisor` is academically interesting but operationally wasted work. The chain also respects publication pressure — authors don't have to disclose anything; the reader-side reflection layer fills in. Caveat: commentary@1 sidecars carry the agent's grounding, not the author's authority — `next-step-advisor` weighs them via `provenance.actor.type == "tool"` so they don't masquerade as author-stated questions.

**Honest scope statement (v0.10)**: this recipe describes the INTENDED end-to-end chain. In v0.10 the chain is partially blocked at Step 2.5 because hub upload is UNVERIFIED. Treat this recipe as a forward-looking design pattern; for actual gap-finding workflows today, prefer Recipe 1 (`coverage-check → next-step-advisor` over paper@1 alone) until the hub-upload prerequisite lands.

### Recipe 8: `sidecar-author → sidecar-reader` (own-paper Q&A)

User has a paper PDF, generates a sidecar, then asks questions about their own paper — typical self-review / rebuttal-prep pattern before the paper has any hub presence.

```bash
# Step 1 — generate the sidecar from PDF (Path D, multimodal LLM read)
python3 scripts/orchestrator.py sidecar-author-pdf my-paper.pdf -o my-paper.knows.yaml
#   Wrapper sanitizes + lints + verifies metadata. Output stays local (no upload).
```

```bash
# Step 2 — sidecar-reader in LOCAL MODE against the freshly-generated YAML
python3 scripts/orchestrator.py sidecar-reader --local my-paper.knows.yaml "<question>"
#   --local reads the sidecar off disk; no hub fetch, no upload. Same grounding/anchor contract
#   as hub mode. Use for "what assumption am I leaning on for Theorem 3?" / "where do I claim
#   beating SOTA?" / "find every limitation I admit" — drives rebuttal anchor prep.
```

**Why this chain**: closes the "I have a paper but no hub presence" gap for self-review tasks. Local mode (`--local`) keeps the sidecar off the hub during the draft phase — useful when the paper is under double-blind review or simply not ready to publish. Once the paper is accepted/posted, the same sidecar can be uploaded and the chain switches to hub mode (Recipe 6).

### Recipe 9: `paper-brainstorm → commentary-builder` (Type B → Type A canonical chain) — NEW v0.11

User wants to publish a `commentary@1` sidecar to the public hub but a solo-agent commentary has limited community-resource value. The brainstorm-derived chain produces a higher-trust artifact that consumers can distinguish via `provenance.workflow_chain`.

```
# Step 1 — user activates the paper-brainstorm stance
# User: "let's brainstorm gaps in <paper title>" or "/paper-brainstorm <paper_rid>"
# The stance auto-activates per its description (or via slash command).
# It reads the paper@1 sidecar, enumerates already-conceded ground (limitation/question/assumption),
# then surfaces 1-3 candidate reflections per turn with opinion + proposed anchor.

# Step 2 — multi-turn dialogue
# User keeps/refines/drops candidates each turn. Stance integrates user judgment.
# Anti-overreach check runs continuously: nothing that overlaps a paper-conceded limitation
# survives as a fresh gap_spotted reflection.

# Step 3 — convergence + handoff
# User signals convergence ("ok, ship those").
# Stance emits a fenced brainstorm_summary YAML block per stances/README.md schema.
# status: ready iff every reflection has grounded: true AND user explicitly confirmed at least one.
# Otherwise status: needs_rework, hand back to user for another round.
```

```python
# Step 4 — orchestrator routes the consume-mode tuple
# Dispatch tuple: (reflection_generate, {paper_rid, brainstorm_summary}, commentary_sidecar)
# This matches the SECOND row in dispatch-and-profile.md §1.5 (consume mode), not the solo row.
# commentary-builder body switches to CONSUME MODE per its SKILL.md §"Consume mode":
#   - Validates schema: brainstorm-v1
#   - Refuses if status != ready
#   - Verifies each reflection's grounding (anchor_id exists, verbatim_quote substring check, user-confirmed)
#   - Mechanical YAML translation — NO new reflections, NO LLM rewriting of arguments
#   - Sets provenance.workflow_chain: ["paper-brainstorm", "commentary-builder"]
#   - Skips the post-LLM banned-phrase check on argument text (stance already enforced it)
#   - Lints + emits commentary@1 sidecar
```

**Why this chain**: solo `commentary-builder` produces "what one LLM thought after reading paper X" — anyone running Claude can produce similar. Brainstorm-derived `commentary-builder` produces "what an agent and a careful reader agreed on after multi-turn refinement, with grounding verified twice (stance + emitter)." Public hub consumers see `provenance.workflow_chain: [paper-brainstorm, commentary-builder]` and can weigh accordingly. The same shape pattern applies to other Type B → Type A chains: `review-prep` → `review-sidecar`, `rebuttal-prep` → `rebuttal-builder`, `pitch-grill` → `sidecar-author`, `survey-shape` → `survey-narrative`/`survey-table`.

**Stance composition** (mattpocock-style): standalone stances (`devils-advocate`, `executive-summary`) compose with task-bound stances. `paper-brainstorm + devils-advocate` → for each candidate gap, also argue why it's NOT actually a gap; sharpens anti-overreach. `<any chain> + executive-summary` → after handoff, produce a 3-bullet TL;DR of the agreed reflections for the busy reader. The standalone stance overrides verbosity but defers to the host stance's handoff format.

### Recipe 10: `paper-finder → next-step-advisor → scoop-check` (the idea-lab loop) — NEW v1.1

The highest-traffic student workflow: *"I searched some papers on `<topic>`, now give me a research idea worth pursuing — and tell me if it's actually novel."* This is the find → ideate → check loop. It pairs `next-step-advisor` (idea-search — GENERATES grounded directions) with `scoop-check` (idea-analysis — COLLISION-checks each direction against prior art). Neither half alone answers the student's real question; chained, they do.

```bash
# Step 0 — pre-flight: is the hub rich enough to both ground directions AND collide against?
python3 scripts/orchestrator.py coverage-check "<topic>"
#   RICH / MODERATE → proceed. THIN / ABSENT → pivot to Scholar/arXiv first; do NOT trust a
#   "novel" verdict on thin coverage (scoop-check will abstain, but the pre-flight saves the trip).
```

```python
# Step 1 — next-step-advisor GENERATES grounded directions (Quick Start in sub-skills/next-step-advisor/SKILL.md)
# Use references/next-step-advisor-prompt.md. Each candidate is grounded in a retrieved
# question/limitation statement, and (v1.1) carries an optional gap_type + move_type tag.

# Step 2 — for EACH generated direction, run scoop-check as an idea_text collision check.
# Dispatch tuple per direction: (check_novelty, {idea_text: <direction restated as a 1-para idea>}, novelty_report)
# Use references/scoop-check-prompt.md. It decomposes the direction into 4 axes, retrieves the
# closest prior work, and returns a worst-case novelty level + verdict (PURSUE / DIFFERENTIATE /
# ALREADY DONE) naming the scooping paper when the direction is already done.

# Step 3 — rank the directions by verdict and present as idea cards:
#   PURSUE (level 4-5)  >  DIFFERENTIATE (level 3)  >  ALREADY DONE (level 1-2, drop or flag)
# Each card: bottleneck (from next-step-advisor grounding) / the move (move_type) /
#   novelty level + closest paper / verdict. Fixed, readable — never a raw JSON/YAML dump.
```

**Why this chain**: a generated direction that looks exciting is worthless if it was published two years ago — and a novelty verdict is worthless without a concrete direction to check. Running them separately makes the student do the join by hand (the exact friction that made them give up). The chain also composes the two skills' opposite safety biases: `next-step-advisor` refuses to over-*generate* (banned speculation tells), `scoop-check` refuses to over-*claim novelty* (banned inflation tells). Together the loop is conservative in both directions — which is what makes its "PURSUE" trustworthy.

**Honest scope (v1.1)**: both halves are hub-coverage-bounded and say so. Step 2 collides only against `paper@1` sidecars on knows.academy; for a high-stakes go/no-go, widen with Scholar/arXiv per each report's coverage disclaimer. The loop reduces — not eliminates — scoop risk.

### Recipe 11: `scoop-check` standalone (own-idea check)

User already has an idea (theirs, or one from Recipe 10) and only wants the collision check: *"is this novel / has anyone already done this / am I about to get scooped?"*

```python
# Single dispatch: (check_novelty, {idea_text: "<the idea, 1-2 paragraphs naming a mechanism>"}, novelty_report)
# scoop-check decomposes → retrieves closest prior work → worst-case novelty level (1-5) + value read + verdict.
# Requires the idea to name a MECHANISM, not just a topic — a topic-only idea abstains IdeaTooVague
# (it would read as maximally novel for the wrong reason: it collides with nothing because it says nothing).
```

**Why standalone matters**: the modal student question is literally "is my idea any good?" — and the honest answer needs prior-art retrieval, not model opinion. This is the single most-requested capability from the student feedback; Recipe 10 is Recipe 11 applied to auto-generated directions.

---

