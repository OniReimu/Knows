# Interaction Stances — 目录（v0.11.2）

[English](./README.md) | 中文

Knows 有两类 sub-skill：**emitter**（位于 `../sub-skills/`）产出经 schema 验证的 artifact；**stance**（本目录）触发思维/对话姿态。Stance 短小精悍，采用 mattpocock 风格——选定一个，agent 即切换到对应的工作模式与你协作。

Stance 可选择性地链接到 emitter：先用 stance 进行自由对话，达成共识后，emitter 再将约定的输出机械地转译为严格的 YAML/Markdown artifact。**合约、组合方式、frontmatter 规范及如何编写新 stance 的详细说明，见 [`REFERENCE.md`](REFERENCE.md)。** 本 README 仅作为面向用户的功能目录。

## Stance 索引

| Stance | 触发方式 | 配对的 emitter | 用途 |
|---|---|---|---|
| [`paper-brainstorm`](paper-brainstorm/SKILL.md) | "让我们探讨论文 X 中的研究空白" | `commentary-builder` | 读者与 agent 协作反思论文 → 产出有依据的 `commentary@1` |
| [`review-prep`](review-prep/SKILL.md) | "帮我准备对论文 X 的评审" | `review-sidecar` | 深度阅读**他人**论文并准备批判 → `review@1` |
| [`draft-grill`](draft-grill/SKILL.md) *（v0.11.2）* | "在投稿前帮我严格审查自己的论文" | `review-sidecar` | 对**自己的**草稿进行自我评审，对抗作者防御心理。与 review-prep 使用相同的 emitter，但认知框架相反。 |
| [`rebuttal-prep`](rebuttal-prep/SKILL.md) | "帮我整理这些 reviewer 意见" | `rebuttal-builder` | 对 reviewer 意见分类（误读 / 有效 / 部分有效 / 政治性）→ `rebuttal_doc` |
| [`pitch-grill`](pitch-grill/SKILL.md) | "帮我审视这个研究想法" | `sidecar-author`（from-idea 路径） | 从原创性、可行性、范围三个维度压力测试一个想法（尚无草稿）→ from-idea `paper@1` |
| [`survey-shape`](survey-shape/SKILL.md) | "帮我规划这篇综述的结构" | `survey-narrative` / `survey-table` | 确定叙述弧线 / 核心论文 / 比较维度 → 散文或表格 |
| [`devils-advocate`](devils-advocate/SKILL.md) | "反驳我的计划" / "为对立面辩护" | （独立使用——可组合） | 前提批判。不同于 red-team（后者映射系统故障）。 |
| [`executive-summary`](executive-summary/SKILL.md) | "压缩成 3 条要点" / "TL;DR" | （独立使用——可组合） | 将长内容压缩为执行摘要形式，作为并行交付物。 |
| [`socratic`](socratic/SKILL.md) | "用提问代替直接回答"、"苏格拉底模式" | （独立使用——可组合） | 问题驱动，从不直接给出答案。 |
| [`red-team`](red-team/SKILL.md) | "找出攻击面"、"对我的计划进行 red-team" | （独立使用——可组合） | 系统故障映射。不同于 devils-advocate（后者质疑前提）。 |
| [`stance-mix`](stance-mix/SKILL.md) | 抽象使用场景，未指定具体 stance（"自我评审论文"、"回应 reviewer"） | （元 stance——提议其他 stance） | 单轮 dispatch：将高层使用场景映射到主链 + 叠加项。 |

v0.11.2 未收录的 stance（暂缓，待需求确认）：`eli5`、`archaeologist`、`revision-coach`、`compare-debate`。

## 激活优先级规则

若缺乏明确的优先级规则，"给我论文 X 的 commentary"这类 prompt 会同时匹配 `commentary-builder`（artifact 请求）和 `paper-brainstorm`（反思意图），导致路由不确定。

锁定规则如下：

1. **明确的 Type A artifact 请求绕过自动激活的 stance。** 包含"给我、生成、产出、制作、lint、比较、分析、总结"等动词 → 直接路由到 Type A。用户要的是 artifact。

   **1.5. 抽象使用场景陈述**（不满足规则 1，也不满足规则 2）→ 激活 `stance-mix`（元 stance dispatch 器）。示例：*"自我评审论文"、"回应 reviewer 意见"、"为这篇论文发布社区 commentary"*。stance-mix 提议一条链 + 叠加项供用户明确激活。见 [`stance-mix/SKILL.md`](stance-mix/SKILL.md)。

2. **Type B 仅在用户明确要求思考/探索时激活。** 触发词：*让我们探讨、帮我想想、带我梳理、探索这个、/<stance-name>* → 激活 stance。对话本身即是目标。

3. **一旦 Type B stance 激活，由 stance 决定何时交接**，方式是输出带围栏的 `brainstorm_summary` 块（规范 schema 见 [`REFERENCE.md`](REFERENCE.md)）。自动激活不会级联——用户正在进行 brainstorm 时，在对话中提到 emitter 的关键词，不应重新触发 Type A。

4. **Slash 命令始终优先。** `/<skill-name>` 是明确指令，覆盖所有启发式规则。

## 链式工作原理（一段话概要）

Stance 在多轮对话中进行自由交流。达成收敛后，stance 输出带围栏的 `brainstorm_summary` YAML 块，其中包含用户确认的反思、弱点、论点或结构决策（取决于所用 stance）。配对的 emitter（Type A）以 CONSUME MODE 消费该块——机械转译，不重新 brainstorm；若有反思内容未锚定或未经确认，则 fail-closed。输出 sidecar 的 `provenance.workflow_chain` 字段记录整条链，使下游消费者能区分链式派生 artifact 与独立模式 artifact。完整 schema 及 fail-closed 语义见 [`REFERENCE.md`](REFERENCE.md)。

## 可组合的 stance

独立 stance（`devils-advocate`、`executive-summary`、`socratic`、`red-team`）可作为叠加层附加到宿主 stance 上以深化输出。**每个 session 最多叠加 2 个独立 stance**——超过 2 个，组合效果会变得嘈杂。每个宿主 stance 的默认组合配方记录在各自的 SKILL.md 中；完整的已验证配方列表和冲突解决规则见 [`REFERENCE.md`](REFERENCE.md)。

示例：

- `paper-brainstorm + devils-advocate` — 对每个候选研究空白，同时论证为何它**不是**研究空白（更锋利的反过度声明检验）
- `draft-grill + devils-advocate` *（v0.11.2 默认）* — agent 审查你的论文；devils-advocate 扮演会对每个弱点升级追问的 reviewer
- `<任意链> + executive-summary` — 为非技术读者或时间紧迫的读者并行生成 3 条 TL;DR 要点

## 交叉参考

- 合约详情和组合规则：[`REFERENCE.md`](REFERENCE.md)
- Type A emitter 索引：[`../sub-skills/README.md`](../sub-skills/README.md)
- Orchestrator 概览：[`../SKILL.md`](../SKILL.md)
- 架构设计：[`../../docs/skill-catalog-evolution-2026-04-30.md`](../../docs/skill-catalog-evolution-2026-04-30.md)
