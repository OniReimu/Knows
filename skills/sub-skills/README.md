# <img src="../../artifacts/icon.svg" width="40" /> Sub-skills — Type A artifact emitters (Knows Orchestrator v1.0+)

English | [中文](./README.zh.md)

Each subdirectory hosts one **Type A** sub-skill that the Knows orchestrator dispatches to via the typed tuple `(intent_class, required_inputs, requested_artifact)` defined in `../references/dispatch-and-profile.md` §1.

> **v0.11+ alongside this catalog**: Knows also has [`Type B interaction stances`](../stances/README.md) — short, mattpocock-style sub-skills (5-50 line SKILL.md, no schema) that trigger thinking/dialogue postures and chain into Type A emitters via `brainstorm_summary` handoff. See [`../../docs/skill-catalog-evolution-2026-04-30.md`](../../docs/skill-catalog-evolution-2026-04-30.md) for the full architecture. The activation precedence rule (Type A wins on artifact requests; Type B activates only on explicit explore/brainstorm intent) is documented in the stances README.

## Sub-skill index

| Sub-skill | `intent_class` | Reference doc | Wrapper |
|---|---|---|---|
| [`paper-finder`](paper-finder/SKILL.md) | `discover` | `../references/api-schema.md` | yes (`scripts/orchestrator.py paper-finder`) |
| [`sidecar-reader`](sidecar-reader/SKILL.md) | `extract` | `../references/consume-prompt.md` | yes (`scripts/orchestrator.py sidecar-reader`) |
| [`sidecar-author`](sidecar-author/SKILL.md) | `contribute` | `../references/gen-prompt.md` | yes (`scripts/orchestrator.py sidecar-author-pdf` / `sidecar-author-postgen`) |
| [`paper-compare`](paper-compare/SKILL.md) | `diff` | `../references/paper-compare.md` | yes (`scripts/orchestrator.py paper-compare`) |
| [`version-inspector`](version-inspector/SKILL.md) | `inspect_lineage` | `../references/version-inspector.md` | yes (`scripts/orchestrator.py version-inspector`) |
| [`sidecar-reviser`](sidecar-reviser/SKILL.md) | `revise_local` | `../references/sidecar-reviser.md` | yes (`scripts/orchestrator.py sidecar-reviser`) |
| [`review-sidecar`](review-sidecar/SKILL.md) | `critique_generate` | `../references/review-mode.md` | agent-mediated |
| [`survey-narrative`](survey-narrative/SKILL.md) | `synthesize_prose` | `../references/survey-narrative.md` | agent-mediated |
| [`survey-table`](survey-table/SKILL.md) | `synthesize_table` | `../references/survey-table.md` | agent-mediated |
| [`next-step-advisor`](next-step-advisor/SKILL.md) | `brief_next_steps` | `../references/next-step-advisor.md` | agent-mediated |
| [`rebuttal-builder`](rebuttal-builder/SKILL.md) | `critique_respond` | `../references/rebuttal-builder.md` | agent-mediated |
| [`commentary-builder`](commentary-builder/SKILL.md) | `reflection_generate` | `../references/commentary-builder-prompt.md` | agent-mediated (NEW v0.10) |

**Wrapper** = which sub-skills have a Python CLI wrapper in `scripts/orchestrator.py` vs which are agent-mediated (LLM-heavy body — agent reads SKILL.md Quick Start and runs the underlying API calls). See `../SKILL.md` §"v1.0 Execution Mode" for why.

The catalog has **12 sub-skills** as of v0.10 (was 11; +`commentary-builder` for reader/agent reflections producing `commentary@1` sidecars consumed downstream by `next-step-advisor`).

## How to add a new sub-skill

1. Read `../references/dispatch-and-profile.md` §1-§7 (load-bearing contract).
2. Read `../SKILL.md` "Orchestrator Architecture (v1.0)" → "Sub-skill frontmatter contract".
3. Create `sub-skills/<your-skill>/SKILL.md` with the required frontmatter:
   - `accepts_profiles` OR `co_inputs` (REQUIRED)
   - `quality_policy` (REQUIRED)
   - `requires_full_record` (OPTIONAL)
   - `emits_profile` (CONDITIONAL — only if skill produces a sidecar)
4. Write a per-skill reference doc in `../references/<your-skill>.md` describing the contract (abstain rules, output schema, edge cases).
5. Add an integration test fixture in `../tests/` if the skill exercises a new orchestrator invariant.
6. Verify the skill registers cleanly: orchestrator startup must validate frontmatter against the contract.

## Hard rules

- Sub-skill bodies **MUST NOT** instantiate their own HTTP clients — use the orchestrator's G5 transport layer.
- Sub-skill bodies **MUST NOT** see records that fail the orchestrator's profile filter (G7) or quality policy (G2').
- Sub-skill bodies **MUST** wrap sidecar-derived content in `<UNTRUSTED_SIDECAR>…</UNTRUSTED_SIDECAR>` per G1.
- Multi-artifact requests are rejected at the orchestrator level (`multi_artifact_request_rejected`) — sub-skills produce exactly one artifact per call.
