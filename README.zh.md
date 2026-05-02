# <img src="./artifacts/icon.svg" width="40" /> Knows：让任意论文在几分钟内对 AI agent 可用

[English](./README.md) | 中文

> **一个 YAML 文件。每一条论断、每一个数字、每一条关联——结构化、经过验证，随时供你的 AI agent 使用。**

[![Schema](https://img.shields.io/badge/Schema-v0.9-blue)](src/knows_sidecar/schema/knows-record-0.9.json)
[![Papers](https://img.shields.io/badge/Papers-20-green)]()
[![Disciplines](https://img.shields.io/badge/Disciplines-14-orange)]()
[![Platform](https://img.shields.io/badge/Platform-knows.academy-purple)](https://knows.academy)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

```bash
npx skills add OniReimu/Knows
```

然后跟你的 agent 说：*"find papers about transformers"*、*"summarize this paper"*、*"what's the main contribution?"*

<p align="center">
  <img src="./artifacts/why_knows.png" alt="为什么需要 Knows：agents 重复重建作者已经知道的东西 — sidecar 解决这个问题" width="450" />
</p>

## Knows 的由来

学术出版仍是一座象牙塔，还在假装自己活在 1995 年。

我们训练研究者用八股文式的论文格式写作，这种格式为人类的眼球而优化——然后把同样的 PDF 喂给 AI agent，让它们从散文中反向工程出文章结构。每个 agent，每一次，都要从同样的非结构化文本中独立提取论断、将证据映射到断言、解析引用目标。这是有损的，是重复的，也是荒谬的。

与此同时，agent 已经是消费研究成果的主要界面。它们评审论文、检索文献、综合发现。我们早已过了"让人类为人类写自然语言，再让机器重新解析"这种做法还有意义的阶段。

**信息流应该反转。** 内容应该以最高效、最结构化、token 最少的形式创作——为 agent 优化。当人类需要阅读时，由 agent 将其翻译成自然语言。而不是反过来。

这就是我们构建 **Knows** 的原因。

不是另一个论文写作工具。不是另一个 PDF 解析器。而是一套**伴侣标准**，将结构化知识置于首位，让格式服务于任何阅读它的人——或事物。

---

## Knows 是什么？

**Knows** 是一个 sidecar YAML 文件，放在你的 PDF 旁边——是你的论文所有论断、证明和关联的结构化、agent 原生表示：

```
paper.pdf          ← 人类文档（不变）
paper.knows.yaml   ← 面向 agent 的伴侣文件
```

经过 schema 验证。支持版本链。比 PDF 减少 77% 的 token。无需修改已发表的文档。

```yaml
# paper.knows.yaml
$schema: https://knows.dev/schema/record-0.9.json
knows_version: 0.9.0
profile: paper@1
title: "Deep Residual Learning for Image Recognition"

statements:
  - id: stmt:c1
    statement_type: claim
    modality: empirical
    text: "ResNets achieve 3.57% top-5 error on ImageNet"
    confidence:
      claim_strength: high
      extraction_fidelity: high

evidence:
  - id: ev:imagenet
    evidence_type: table_result
    observations:
      - metric: top5_error
        value: 3.57
        unit: "%"

relations:
  - id: rel:1
    subject_ref: stmt:c1
    predicate: supported_by
    object_ref: ev:imagenet
```

<p align="center">
  <img src="./artifacts/expected_knows.png" alt="Example KnowsRecord sidecar — claims, evidence, relations" width="700" />
</p>

---

## 安装

### 面向 agent 用户（推荐）

```bash
# Claude Code，项目级
npx skills add OniReimu/Knows -a claude-code -s '*' -y

# Claude Code，全局安装（在所有项目中可用）
npx skills add OniReimu/Knows -g -a claude-code -s '*' -y

# Codex CLI
npx skills add OniReimu/Knows -a codex -s '*' -y

# 同时安装到 Claude Code 和 Codex
npx skills add OniReimu/Knows -a claude-code -a codex -s '*' -y

# 安装到所有支持的 agent（50+）
npx skills add OniReimu/Knows --all
```

`npx skills` CLI 由 [vercel-labs/skills](https://github.com/vercel-labs/skills) 提供，支持 50+ 个 agent。上面的参数指定特定 agent 并跳过交互式选择器。

### 面向 sidecar 作者（Python CLI）

如果你是论文作者，需要为自己的论文编写 sidecar，请安装 Python 包：

```bash
pip install knows-sidecar
# 或
uv add knows-sidecar
```

这会提供 `knows gen`（LaTeX → sidecar scaffold）、`knows lint`（验证）、`knows query`（基于 sidecar 提问）等命令。作者工作流见[快速开始](#快速开始)。

---

## 快速开始

### 作为 agent 用户

安装 skill 之后（见上），直接用自然语言和你的 agent 对话：

- **查找论文**：*"find me 5 papers on diffusion models"*
- **总结**：*"summarize this paper for me"*（粘贴 `paper.knows.yaml` 或 PDF）
- **对比**：*"compare these two papers — what's different?"*
- **头脑风暴**：*"what's underexplored in side-channel ML attacks?"*
- **起草评审**：*"help me prep a review of this paper"*

agent 会根据你的表达自动选择合适的 Knows sub-skill。完整菜单见[你的 agent 能做什么](#你的-agent-能做什么)。

### 作为 sidecar 作者

如果你在发表论文，想随论文附上 sidecar：

```bash
# 1. 从 LaTeX 源文件生成 scaffold
knows gen paper/main.tex -o paper.knows.yaml

# 2. 填写 TODO（有经验的用户约 15 分钟）

# 3. 验证
knows lint paper.knows.yaml

# 4.（可选）测试查询
knows query paper.knows.yaml "What is the main contribution?"
```

完整 CLI 参考，运行 `knows --help`。

---

## 你的 agent 能做什么

Knows 提供 **12 个 sub-skill**（查找 / 阅读 / 写作 / 对比 / 评审 / 头脑风暴 / 起草 rebuttal / 生成 sidecar / 检视版本 / 建议下一步 / 构建 commentary / 修补元数据），以及 **11 个交互 stance**（devil's advocate, socratic, red-team, executive summary, paper brainstorm, draft grill, ...）。

Sub-skills 产出 schema 验证过的产物（一个 sidecar、一份排序后的论文列表、一篇同行评审等）。Stances 触发思考姿态（让我们辩论、向我提问、找漏洞），并通过 fenced YAML 握手与 sub-skills 串联。

→ **查看 [完整 skill 目录](./skills/README.md)** 了解每个 skill 做什么、何时激活、如何组合。

---

## 工作原理

### KnowsRecord schema（v0.9）

KnowsRecord 是一个放在论文 PDF 旁边的 YAML 文件。它绑定 **statements**（claim / method / limitation / question / reflection / lesson）、**evidence**（数字、来源、支撑）、**typed relations**（一条 statement 支持/反驳/扩展另一条）、**artifacts**（引用的数据集、代码、模型）和 **provenance**（谁写了每个部分、何时、如何写的）。

```
KnowsRecord
  ├─ artifacts[]        paper, repository, dataset, model, benchmark, software, website, other
  ├─ statements[]       claim | assumption | limitation | method | question | definition
  │   modality:         empirical | theoretical | descriptive | normative
  │   confidence:       claim_strength × extraction_fidelity
  ├─ evidence[]         table_result | figure | experiment_run | proof | case_study | observation | ...
  │   observations[]:   value（数值）OR qualitative_value（字符串）
  ├─ relations[]        supported_by | challenged_by | depends_on | limited_by | cites
  ├─ actions[]          可选的可执行 hook，含安全策略
  ├─ provenance         来源、行为者、方法、验证
  ├─ replaces           上一版本的 record_id（版本链）
  ├─ version            spec × record × source
  └─ freshness          as_of, update_policy, stale_after
```

30 个根级字段，23 个实体定义，可通过 `x_extensions` 扩展。完整示例见 [examples 目录](./examples/)。

### Orchestrator + dispatch

Orchestrator 通过类型化元组 `(intent_class, required_inputs, requested_artifact)` 将用户意图路由到 12 个 sub-skill 之一。**7 个守卫（G1-G7）** 防范 prompt 注入、profile 污染、质量泄漏和无界 fetch。完整合约见 [skills/references/dispatch-and-profile.md](./skills/references/dispatch-and-profile.md)。

<p align="center">
  <img src="./artifacts/how_knows.png" alt="How Knows works — orchestrator routes intent through guards to sub-skills" width="700" />
</p>

### 两种使用模式

| 模式 | 适用场景 | 发生了什么 |
|---|---|---|
| **Knows-only**（agent 原生） | 你有 sidecar | agent 只读 YAML——快速、确定性、低 token |
| **Knows + PDF fallback**（混合） | 冷启动，sidecar 不完整 | agent 读 YAML，并在 sidecar 覆盖不足时回退到 PDF |

默认为 Knows-only。当 sidecar 报告 `coverage_statements: partial`，或 agent 的查询需要 sidecar 未绑定的证据时，fallback 自动激活。

---

## 评估

横跨 11 项实验（E1-E10），覆盖 20 篇论文、14 个学科、8+ 个 LLM agent：

- **+29 到 +42 个百分点** 的准确率提升 — 弱模型（Qwen-0.8B、Gemma-2B）在拿到 sidecar 后 vs 仅看 PDF
- **节省 55% token** 即可达到与读完整 PDF 相同的准确率
- **可追溯性 0% → 64-91%** — sidecar 把每个论断绑定到证据；PDF 不绑定任何东西
- **覆盖 14 个学科** — 从 CS / ML 到经济学、生物学、土木工程

→ **完整结果表、length-effect 分析、评分稳健性、每个实验细节请见 [docs/evaluation.zh.md](./docs/evaluation.zh.md)**

---

## 引用

```bibtex
@misc{yu2026knowsagentnativestructuredresearch,
      title={Knows: Agent-Native Structured Research Representations}, 
      author={Guangsheng Yu and Xu Wang},
      year={2026},
      eprint={2604.17309},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2604.17309}, 
}
```

## 许可证

Apache License 2.0——见 [`LICENSE`](LICENSE)。

Copyright 2026 The Knows Authors. Licensed under the Apache License, Version 2.0.
