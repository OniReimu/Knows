# Review Mode — Structured Peer Review as Sidecar

**IDs MUST be descriptive kebab-case** (e.g., `stmt:missing-ablation-study`, NOT `stmt:w1`). Same rule as SKILL.md.

> **Canonical LLM prompt**: `review-sidecar-prompt.md`. Use that prompt verbatim — it operationalizes the YAML-structure contract here (cross-record `challenged_by` grammar, statement types) AND adds the critique-discipline layer (banned reviewer-clichés, critique-typology ladder, anti-overreach rule, OpenReview Markdown rendering, 1-5 confidence calibration) so individual agents do not re-derive them per task.

Generate a structured peer review as a KnowsRecord sidecar.

```bash
knows review paper.knows.yaml -o review.knows.yaml
```

The generated review sidecar has `profile: review@1` and contains:
- **Weakness statements** (e.g., `stmt:missing-ablation-study`, `stmt:weak-baseline-comparison`) identifying specific issues
- **Strength statements** (e.g., `stmt:novel-theoretical-framework`, `stmt:comprehensive-evaluation`) acknowledging contributions
- **Cross-record relations** linking weaknesses to specific claims in the reviewed paper

## Cross-record reference grammar

Reviews link back to the original paper's sidecar using `record_id#local_id`:

```yaml
# In review.knows.yaml
relations:
  - id: rel:generalization-challenges-residual
    subject_ref: "knows:examples/resnet/1.0.0#stmt:main-contribution"  # original paper's claim
    predicate: challenged_by
    object_ref: "stmt:missing-ablation-study"  # this review's weakness
```

This enables:
- **Per-weakness traceability**: Every criticism points to the exact claim it challenges
- **Machine-traversable peer review**: Agents can follow the relation graph
- **Structured rebuttals**: Authors can respond to each weakness with targeted evidence

## Review workflow

1. Generate scaffold: `knows review paper.knows.yaml -o review.knows.yaml`
2. Fill in weakness/strength statements with specific observations
3. Add cross-record relations linking weaknesses to original claims
4. Validate: `knows lint review.knows.yaml`

## Existing review examples

The project has 13 review sidecars across disciplines in `examples/*/`, e.g.:
- `examples/cs/resnet_review.knows.yaml`
- `examples/biology/dna-double-helix_review.knows.yaml`
