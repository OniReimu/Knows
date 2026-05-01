# Knows：让任意论文在几分钟内对 AI agent 可用

[English](./README.md) | 中文

> **一个 YAML 文件。每一条论断、每一个数字、每一条关联——结构化、经过验证，随时供你的 AI agent 使用。**

[![Schema](https://img.shields.io/badge/Schema-v0.9-blue)](src/knows_sidecar/schema/knows-record-0.9.json)
[![Papers](https://img.shields.io/badge/Papers-20-green)]()
[![Disciplines](https://img.shields.io/badge/Disciplines-14-orange)]()
[![Platform](https://img.shields.io/badge/Platform-knows.academy-purple)](https://knows.academy)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue)](LICENSE)

---

## Knows 的由来

学术出版仍是一座象牙塔，还在假装自己活在 1995 年。

我们训练研究者用八股文式的论文格式写作，这种格式为人类的眼球而优化——然后把同样的 PDF 喂给 AI agent，让它们从散文中反向工程出文章结构。每个 agent，每一次，都要从同样的非结构化文本中独立提取论断、将证据映射到断言、解析引用目标。这是有损的，是重复的，也是荒谬的。

与此同时，agent 已经是消费研究成果的主要界面。它们评审论文、检索文献、综合发现。我们早已过了"让人类为人类写自然语言，再让机器重新解析"这种做法还有意义的阶段。

**信息流应该反转。** 内容应该以最高效、最结构化、token 最少的形式创作——为 agent 优化。当人类需要阅读时，由 agent 将其翻译成自然语言。而不是反过来。

这就是我们构建 **Knows** 的原因。

不是另一个论文写作工具。不是另一个 PDF 解析器。而是一套**伴侣标准**，将结构化知识置于首位，让格式服务于任何阅读它的人——或事物。

---

## 核心结果

<table>
<tr>
<td width="50%">

### 弱模型：准确率提升 +29 到 +42pp

| 模型 | PDF | Knows | 提升幅度 |
|:------|----:|------:|:-----------:|
| Qwen3.5-0.8B | 19% | **47%** | **+29pp** |
| Qwen3.5-2B | 25% | **67%** | **+42pp** |

以 LLM 作为评判者（Claude Sonnet 4）的验证表明，弱模型读取 sidecar 的准确率达到 **75–77%**，接近中等模型读取 PDF 的水平（78–83%）。

</td>
<td width="50%">

### token 减少 55%，准确率不变

| 条件 | 准确率 | Token 数 | 效率 |
|:----------|:--------:|-------:|:----------:|
| PDF | 59% | 9,955 | 5.9%/1Ktok |
| **Full Sidecar** | **59%** | **4,463** | 13.2%/1Ktok |
| Stmts-only | 52% | 693 | **75.0%/1Ktok** |

Full sidecar 与 PDF 准确率持平。仅使用 statement 时，在 **token 减少 93%** 的情况下保留 88% 准确率（效率提升 12.7 倍）。

</td>
</tr>
</table>

### 可追溯性：0%（PDF）→ 64–91%（Knows）

使用 Knows 生成的 agent 评审，在弱点描述部分引用了具体的 claim/evidence ID。PDF 评审在测试的四个模型中，每条弱点描述中的 ID 引用数均为**零**。

### 跨学科覆盖

在 **14 个学科**的 **20 篇论文**上进行评测（计算机科学、生物学、化学、物理学、经济学、心理学、医学、教育学、哲学、数学、土木工程、机械工程、电气工程、半导体）。在长度受控的论文（2K–20K 词）上，Knows 在弱模型的 **10 个学科中有 6 个**提升了准确率。

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

---

## Orchestrator + 研究者工作流（v1.0+）

在 sidecar 规范之上，Knows 还提供一套 **orchestrator skill**，将研究者意图路由到专门的 sub-skill——这是构建在 [knows.academy](https://knows.academy) hub 之上的即用型工作流库。

```
User intent → dispatch tuple → sub-skill → artifact
```

**MVP v1.0（3 个 sub-skill）**——涵盖只读发现、下游 Q&A 和上游贡献：

| Sub-skill | 用户说… | 产出 Artifact |
|---|---|---|
| `paper-finder` | "找 10 篇关于 diffusion + 隐私的论文" | 排序表格 + 可选 `papers.bib` |
| `sidecar-reader` | "Vaswani 用了什么数据集？" | JSON 答案（consume-prompt v1.1） |
| `sidecar-author` | "为这个 PDF/LaTeX 生成 sidecar" | `paper.knows.yaml`（lint-pass + verify-pass） |

**v1.1+ 计划中**——paper-compare / review-sidecar / survey-narrative / survey-table / next-step-advisor / rebuttal-builder / version-inspector / sidecar-reviser / commentary-builder（v0.10）。完整 12 个 skill 的目录和发布计划见 [`skills/sub-skills/README.md`](skills/sub-skills/README.md)。

**7 个 orchestrator 守卫**（G1–G7）防范 prompt 注入、质量泄漏、无类型路由、profile 污染和无界 fetch。完整合约：[`skills/references/dispatch-and-profile.md`](skills/references/dispatch-and-profile.md)。

**试用**（3 个演示）→ [`docs/demos/`](docs/demos/) — `paper-finder.md` / `sidecar-reader.md` / `sidecar-author.md`。

---

## 安装

### Python CLI（`knows lint` / `knows gen` / `knows query` / …）

```bash
pip install knows-sidecar
```

或使用 uv：
```bash
uv add knows-sidecar
```

### Agent skills（Claude Code、Codex CLI 等）

[`skills/`](skills/) 下的 orchestrator + 12 个 sub-skill + 11 个 interaction stance，通过 [`vercel-labs/skills`](https://github.com/vercel-labs/skills) 安装，该通用 CLI 支持 50+ 个 agent。以下命令跳过交互式 agent/skill 选择器：

```bash
# Claude Code，项目级（推荐用于论文仓库）
npx skills add OniReimu/Knows -a claude-code -s '*' -y

# Claude Code，全局安装（在所有项目中可用）
npx skills add OniReimu/Knows -g -a claude-code -s '*' -y

# Codex CLI
npx skills add OniReimu/Knows -a codex -s '*' -y

# 同时安装到 Claude Code 和 Codex CLI
npx skills add OniReimu/Knows -a claude-code -a codex -s '*' -y

# 安装到所有支持的 agent
npx skills add OniReimu/Knows --all
```

不加 `-a` 和 `-s` 参数时，CLI 会打开交互式选择器，列出所有 50+ 个支持的 agent 和本仓库中全部 24 个 skill——如需跳过，使用 `--all` 或上面的显式参数。

## CLI 用法

```bash
# 验证 sidecar
knows lint paper.knows.yaml

# 从 LaTeX 生成 scaffold
knows gen paper/main.tex -o paper.knows.yaml

# 分析 sidecar
knows analyze paper.knows.yaml

# 仅使用 sidecar 查询论文
knows query paper.knows.yaml "What is the main contribution?"

# 生成结构化评审
knows review paper.knows.yaml -o review.knows.yaml

# 比较两篇论文
knows compare paper1.knows.yaml paper2.knows.yaml
```

---

## 评估摘要

11 个实验（E1–E10），覆盖 20 篇论文、14 个学科、8 个以上 LLM agent：

| 实验 | 范围 | 关键发现 |
|:-----------|:------|:------------|
| **E1** 任务准确率 | 140Q × 20p × 6m × 3 条件 | 弱模型：+29 到 +42pp；强模型：-1pp，但 token 减少 64–83% |
| **E2** Token 效率 | 来自 E1 | 减少 29–83%（MiMO-V2-Flash：2,856K → 401K） |
| **E3** 延迟 | 来自 E1 | 本地弱模型提速 3.4–4.6 倍 |
| **E4** 评审可追溯性 | 15p × 4m × 2 条件 | 逐条弱点可追溯性：64–91%（Knows）vs 0%（PDF） |
| **E5** 一致性 | 15p × 3 次注入 | 结构性：100% 检出；语义性：0%（边界清晰） |
| **E6** 跨论文 | 15p × 4m × 4Q | 使用 Knows 的 ID 引用数提升 4–17 倍 |
| **E7** LLM 生成 | 5p × 7m | Lint 通过率：Claude 100%，非 Claude <20%。Haiku 4.5 = Opus 质量，成本仅 1/15 |
| **E8** 消融实验 | 15p × 5 条件 × 4m | Full sidecar = PDF 准确率（59%），token 减少 55% |
| **E9** 粒度 | 8p × 4 层级 × 2 条件 | Dense sidecar（statements 增 2.5×）：中等模型 +27pp，强模型 +29pp（均值） |
| **E9b** Dense+Fallback | 8p × 2m × 2 条件 | 对 dense sidecar 而言 fallback 边际效益极小；仅用 dense 是最优选择 |
| **E10a** 跨评估（one-shot） | 5p × 4gen × 2cons | 非 Claude one-shot：消费准确率 21–50% |
| **E10b** 跨评估（agent） | 20p × 3gen | Opus 88.6%，Haiku-dense 72.9%，Haiku 64.3%。Opus 仍是质量标杆 |

### 长度效应

Knows 的优势随论文长度增加而增大：

| 论文长度 | 弱模型 Δ | 中等模型 Δ | 强模型 Δ |
|:-------------|:------:|:--------:|:--------:|
| SHORT（<2K 词） | +8pp | +8pp | +14pp |
| MEDIUM（2–8K） | **+29pp** | -6pp | -5pp |
| STANDARD（8–20K） | **+40pp** | -19pp | -9pp |
| LONG（>20K） | **+57pp** | +13pp | **+17pp** |

### 评分鲁棒性

| 模型 | 关键词评分 Knows | LLM 评判 Knows | PDF（LLM） |
|:------|:------------:|:---------------:|:---------:|
| Qwen3.5-0.8B | 47% | **75%** | 24% |
| Qwen3.5-2B | 67% | **77%** | 25% |

**弱模型 + Knows（75–77%）≈ 中等模型 + PDF（78–83%）**

---

## KnowsRecord Schema（v0.9）

30 个根级字段，23 个实体定义，可通过 `x_extensions` 扩展。

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

### 评审即 Sidecar

评审也是 KnowsRecord（`profile: review@1`）。每条弱点通过跨记录引用链接到原论文的具体论断：

```yaml
relations:
  - subject_ref: "knows:examples/resnet/1.0.0#stmt:a1"
    predicate: challenged_by
    object_ref: "stmt:w1"  # 本评审的该条弱点
```

---

## 示例

[`examples/`](examples/) 目录下，14 个学科共 21 份示例 sidecar：

| 学科 | 论文 | 主要特征 |
|:-----------|:-------|:------------|
| 计算机科学 | ResNet, DP-SGD | 定量 benchmark，隐私分析 |
| 生物学 | Watson-Crick, Mendel | 定性证据，遗传比率 |
| 化学 | Mendeleev, Pauling | 规律识别，键理论 |
| 物理学 | Einstein | 理论预测 |
| 经济学 | Akerlof | 理论模型 |
| 心理学 | Kahneman | 行为实验 |
| 医学 | Semmelweis | 临床观察 |
| 教育学 | Bloom, Dewey | 专家分类 |
| 哲学 | Gettier, Turing | 思想实验 |
| 数学 | Godel | 纯证明 |
| 土木工程 | Terzaghi | 实验室测试 + 理论 |
| 机械工程 | Reynolds | 染料实验 |
| 电气工程 | Shannon | 数学证明 |
| 半导体 | Moore, Dennard | 实证外推 |

---

## 工具链

### `knows-lint` — 7 项验证检查
1. JSON Schema 验证
2. 交叉引用完整性
3. ID 唯一性
4. ID 前缀规范（`art:`、`stmt:`、`ev:`、`rel:`）
5. 关系谓词约束
6. Artifact 可发现性
7. 可选的 URL 存活检查

可捕获 **100% 的结构性损坏**。语义性损坏（值错误）需要未来基于 LLM 的验证。

### `knows-gen` — LaTeX 转 scaffold
- 处理嵌套 `\input{}`（递归，最多 10 层）
- 多格式作者解析（acmart, NeurIPS, IEEEtran）
- 扩展引用命令
- 典型会议论文的 scaffold 生成约需 15 分钟

---

## 两种使用模式

| 模式 | 适用场景 | 方式 |
|:-----|:-----|:----|
| **Knows-only** | Agent 原生工作流 | Agent 仅读取 sidecar，token 减少 29–83%。 |
| **Knows+Fallback** | 改造既有论文 | sidecar 优先，不足时回退到 PDF。6 个模型中有 5 个准确率最佳。 |

---

## 快速开始

```bash
pip install knows-sidecar

# 从 LaTeX 生成 sidecar
knows gen paper/main.tex -o paper.knows.yaml

# 填写 TODO（约 15 分钟）
# 验证
knows lint paper.knows.yaml

# 你的论文现在对 agent 可用了。
```

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
