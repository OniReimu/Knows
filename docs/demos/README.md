# Knows Orchestrator Demos (v1.0)

English | [中文](./README.zh.md)

Three demo transcripts showing each MVP sub-skill in action — input, dispatch, what happens under the hood, the artifact produced, and manifest emission.

| Demo | What it does | When to use |
|---|---|---|
| [`paper-finder.md`](paper-finder.md) | Search knows.academy for sidecars matching a query | "Find me 10 papers on X" / "Give me BibTeX for query Y" |
| [`sidecar-reader.md`](sidecar-reader.md) | Answer a question from a sidecar (operationalizes consume-prompt v1.1) | "What dataset did paper X use?" / "What's the main claim of Y?" / any benchmark Q&A |
| [`sidecar-author.md`](sidecar-author.md) | Generate a sidecar from PDF / LaTeX / text blob | "Make a sidecar for paper.pdf" / "Generate from my LaTeX project" |

## Common dispatch shape

Every demo follows the same orchestrator contract:

```
User intent → (intent_class, required_inputs, requested_artifact) → sub-skill → artifact + manifest
```

The full contract is in [`../../skills/references/dispatch-and-profile.md`](../../skills/references/dispatch-and-profile.md). Every sub-skill inherits 7 orchestrator guards (G1–G7) covering prompt-injection containment, quality filtering, profile discipline, transport caching, and provenance manifests.

## Reproducing the demos

Each demo includes a "Try it yourself" section at the bottom showing both the direct API call and the Claude Code agent invocation. Live API endpoints (read-only) work without any auth. Generation paths (Path B in sidecar-author) require an `ANTHROPIC_API_KEY`.

For the orchestration plumbing tests — what these demos rely on for correctness — see [`../../skills/tests/`](../../skills/tests/). All 25 tests across 3 fixtures pass; CI green is a hard prerequisite for v1 release per `dispatch-and-profile.md` §7.5.
