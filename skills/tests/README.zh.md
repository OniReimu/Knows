# Knows Orchestrator 集成测试

[English](./README.md) | 中文

三个 fixture 用于测试 v1.0 公开 sub-skill 不直接触及的 orchestration 底层逻辑。**按照 `../references/dispatch-and-profile.md` §7.5，三个 fixture 的 CI 全绿是 v1 版本发布的硬性前提。**

## Fixture 说明

### `fixture_mixed_profile_retrieval/`

测试 **G7 — Profile Discipline** 和 §3（类型化 co-input 槽位）。

**合成语料**（位于 `run.py`）：`paper@1` 记录 + `review@1` 记录 + `profile` 字段格式错误的记录 + `profile` 字段缺失的记录。

**涉及的 skill**：声明 `accepts_profiles: [paper@1]` 的单输入 skill（如 `paper-finder` smoke）；声明 `co_inputs: {paper: paper@1, review: review@1}` 的多输入 skill（如 `rebuttal-builder` smoke）。

**断言**：
- 仅接受 `paper@1` 的 skill 绝不应在其工作集中看到 `review@1` 记录。
- `profile` 缺失或格式错误的记录默认被排除（除非 skill 明确声明 `accepts_profiles: [unknown]`）。
- Manifest 中包含正确的 `excluded_missing_profile` 和 `excluded_malformed_profile` 条目。
- 多输入 skill 的 `paper` 和 `review` 槽位独立过滤；槽位为空时抛出 `missing_co_input.<slot_name>`。

### `fixture_quality_exclusion_logging/`

测试 **G2' — Skill 声明的 Quality Policy** 和 §6（manifest 可见性）。

**合成语料**（位于 `run.py`）：混合 `lint_passed: true/false` 的记录、`coverage.statements` 枚举值各异的记录、`coverage.evidence` 枚举值各异的记录、statement 数量参差不齐的记录（部分 <5，部分 ≥5）。

**涉及的 skill**：声明严格 `quality_policy: {require_lint_passed: true, allowed_coverage: [exhaustive, main_claims_only], min_statements: 5}` 的 skill。

**断言**：
- 不满足 `require_lint_passed` 的记录被排除。
- `coverage.statements` 不在 `allowed_coverage` 范围内的记录被排除。
- statement 数量 `< min_statements` 的记录被排除。
- Manifest 的 `quality_exclusions` 列举每条被丢弃的记录，包含 `policy_field`（哪项检查失败）和 `actual`（记录的实际值）。
- Skill 主体不会看到任何被排除的记录。

### `fixture_dispatch_clarify_and_abstain/`

测试 **§4（澄清协议）** 和 **§5（Abstain 条件）**。

**合成查询**（4 条路径）：
1. **唯一元组路径**：元组精确匹配 §1.5 中的某一行 → 正确路由到单个 skill。
2. **歧义-澄清路径**：元组匹配超过 1 行 → orchestrator 发出一条澄清消息，列出候选项。
3. **歧义-abstain 路径**：歧义元组 + 未能消歧的回复 → orchestrator 以 `ambiguous_dispatch_unresolved_after_clarification` 抛出 abstain，manifest 中 `abstained_reason` 字段被填充。
4. **歧义-解决路径**：歧义元组 + 能消歧的回复（指定 skill 名称 + artifact）→ 正确路由。

**断言**：
- 绝不允许静默默认路由（路径 3 必须 abstain，绝不能静默选择最保守的选项）。
- 路径 2 只发出一条澄清消息，不触发递归澄清链。
- 路径 4 的回复必须唯一确定某一行（单行 skill 名称，或多行 skill 名称 + artifact）。
- 仅路径 3 填充 manifest `abstained_reason`。

## 运行方式

```bash
bash skills/tests/run_all.sh                                       # 运行全部三个
python3 skills/tests/fixture_dispatch_clarify_and_abstain/run.py   # 运行单个 fixture
```

每个 fixture 在自己的目录中自成一体，包含 `run.py` 运行器。`run_all.sh` 依次调用全部三个，任意一个失败则以非零状态退出。
