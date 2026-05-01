# Sub-skills — Type A artifact emitters（Knows Orchestrator v1.0+）

[English](./README.md) | 中文

每个子目录存放一个 **Type A** sub-skill，Knows orchestrator 通过 `../references/dispatch-and-profile.md` §1 中定义的类型化元组 `(intent_class, required_inputs, requested_artifact)` 将请求 dispatch 到对应的 sub-skill。

> **v0.11+ 同时提供以下目录中的内容**：Knows 还提供 [`Type B interaction stances`](../stances/README.md)——短小的 mattpocock 风格 sub-skill（5–50 行 SKILL.md，无 schema），触发思维/对话姿态，并通过 `brainstorm_summary` 交接链入 Type A emitter。完整架构见 [`../../docs/skill-catalog-evolution-2026-04-30.md`](../../docs/skill-catalog-evolution-2026-04-30.md)。激活优先级规则（Type A 在 artifact 请求时优先；Type B 仅在用户明确发出 explore/brainstorm 意图时激活）记录在 stances README 中。

## Sub-skill 索引

| Sub-skill | `intent_class` | 参考文档 | Wrapper |
|---|---|---|---|
| [`paper-finder`](paper-finder/SKILL.md) | `discover` | `../references/api-schema.md` | 有（`scripts/orchestrator.py paper-finder`） |
| [`sidecar-reader`](sidecar-reader/SKILL.md) | `extract` | `../references/consume-prompt.md` | 有（`scripts/orchestrator.py sidecar-reader`） |
| [`sidecar-author`](sidecar-author/SKILL.md) | `contribute` | `../references/gen-prompt.md` | 有（`scripts/orchestrator.py sidecar-author-pdf` / `sidecar-author-postgen`） |
| [`paper-compare`](paper-compare/SKILL.md) | `diff` | `../references/paper-compare.md` | 有（`scripts/orchestrator.py paper-compare`） |
| [`version-inspector`](version-inspector/SKILL.md) | `inspect_lineage` | `../references/version-inspector.md` | 有（`scripts/orchestrator.py version-inspector`） |
| [`sidecar-reviser`](sidecar-reviser/SKILL.md) | `revise_local` | `../references/sidecar-reviser.md` | 有（`scripts/orchestrator.py sidecar-reviser`） |
| [`review-sidecar`](review-sidecar/SKILL.md) | `critique_generate` | `../references/review-mode.md` | agent 介导 |
| [`survey-narrative`](survey-narrative/SKILL.md) | `synthesize_prose` | `../references/survey-narrative.md` | agent 介导 |
| [`survey-table`](survey-table/SKILL.md) | `synthesize_table` | `../references/survey-table.md` | agent 介导 |
| [`next-step-advisor`](next-step-advisor/SKILL.md) | `brief_next_steps` | `../references/next-step-advisor.md` | agent 介导 |
| [`rebuttal-builder`](rebuttal-builder/SKILL.md) | `critique_respond` | `../references/rebuttal-builder.md` | agent 介导 |
| [`commentary-builder`](commentary-builder/SKILL.md) | `reflection_generate` | `../references/commentary-builder-prompt.md` | agent 介导（v0.10 新增） |

**Wrapper** = 哪些 sub-skill 在 `scripts/orchestrator.py` 中有 Python CLI wrapper，哪些是 agent 介导的（LLM 密集型——agent 读取 SKILL.md Quick Start 并执行底层 API 调用）。原因详见 `../SKILL.md` §"v1.0 Execution Mode"。

截至 v0.10，目录共有 **12 个 sub-skill**（原为 11 个；新增 `commentary-builder`，用于读者/agent 反思，产出 `commentary@1` sidecar，供下游的 `next-step-advisor` 使用）。

## 如何添加新 sub-skill

1. 阅读 `../references/dispatch-and-profile.md` §1–§7（核心合约）。
2. 阅读 `../SKILL.md` 中的"Orchestrator Architecture (v1.0)" → "Sub-skill frontmatter contract"。
3. 创建 `sub-skills/<your-skill>/SKILL.md`，包含必要的 frontmatter：
   - `accepts_profiles` 或 `co_inputs`（必填）
   - `quality_policy`（必填）
   - `requires_full_record`（可选）
   - `emits_profile`（条件必填——仅当 skill 产生 sidecar 时）
4. 在 `../references/<your-skill>.md` 中编写每个 skill 的参考文档，描述合约（abstain 规则、输出 schema、边界情况）。
5. 如果该 skill 涉及新的 orchestrator 不变式，在 `../tests/` 中添加集成测试 fixture。
6. 验证 skill 注册无误：orchestrator 启动时必须根据合约验证 frontmatter。

## 硬性规则

- Sub-skill 主体**不得**自行实例化 HTTP 客户端——必须使用 orchestrator 的 G5 传输层。
- Sub-skill 主体**不得**访问未通过 orchestrator profile 过滤器（G7）或 quality policy（G2'）的记录。
- Sub-skill 主体**必须**将 sidecar 派生内容包裹在 `<UNTRUSTED_SIDECAR>…</UNTRUSTED_SIDECAR>` 标签中，遵照 G1 规定。
- 多 artifact 请求在 orchestrator 层被拒绝（`multi_artifact_request_rejected`）——每次调用，sub-skill 只产生一个 artifact。
