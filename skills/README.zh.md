# Knows Skills — 你能用它做什么

[English](./README.md) | 中文

Knows skills 提供一套工作流目录，覆盖阅读、写作、评审和 brainstorm 研究论文的各类场景。根据你想完成的目标来选择工作流，无需关心背后调用了哪个 skill。

所有工作流均在本地运行。关于 sidecar 格式及其设计理念，见 [`../README.md`](../README.md)。关于任意单个 skill 的技术细节，浏览 [`sub-skills/`](sub-skills/)（artifact emitter）和 [`stances/`](stances/)（对话姿态）。

---

## 阅读与查询论文

**将 PDF 转换为结构化 sidecar。** 将 `.pdf` 交给 `sidecar-author`，它会生成一个经过 lint 验证的 `paper.knows.yaml`，提取其中所有论断、方法、局限性和引用。过程需 2–5 分钟，输出是可查询的数据结构，而非一大段散文。

**对论文提出有据可查的问题。** `sidecar-reader` 用自然语言回答问题（"他们用了什么数据集？"、"他们在哪里声称超越了 SOTA？"），并引用 sidecar 中具体的 statement——不会出现幻觉引用。

**查询自己未发表的草稿。** 对进行中的论文运行 `sidecar-author`，再用 `sidecar-reader --local` 进行问答，无需上传任何内容。适合检查自己的论断或核对局限性描述。

---

## 自我评审

**投稿前对自己的论文进行自我评审。** `draft-grill` stance 以敌对 reviewer 的视角审查你的草稿，并内置对作者防御心理的检查（"从上下文可以理解"、"留到修改时再改"）。在此基础上叠加 `devils-advocate`，agent 还会预测 reviewer 对你计划修改内容的反驳，让你在 reviewer 看到之前提前修复。

**在全力投入之前压力测试研究想法。** `pitch-grill` 从原创性、可行性和范围三个维度，分三轮审问你的想法（"你真正读过的最相近的论文是哪篇？"）；叠加 `red-team` 可进一步暴露部署失败模式。通过审查的想法通过 `sidecar-author` 的 from-idea 路径提交为 sidecar。

---

## 深度阅读他人论文

**与 agent 协作 brainstorm 论文的研究空白。** `paper-brainstorm` 跨多轮对话与你协作，发掘作者未披露的研究空白，随后 `commentary-builder` 产出一份锚定到具体 paper statement 的可发布 `commentary@1` sidecar。如果你希望自己推导出研究空白，叠加 `socratic`，agent 将只通过引导性问题辅助你。

**准备你被分配的同行评审任务。** `review-prep` 使用 7 种批判类型的分类框架查找候选弱点，并内置反过度声明检查（对照论文已承认的局限性）。叠加 `devils-advocate`，你还能提前看到作者可能给出的反驳，帮你在提交评审前预判对方的论点。

---

## 回应 reviewer 意见

**整理 reviewer 意见并起草 rebuttal。** `rebuttal-prep` 对每条 reviewer 意见分类（误读 / 有效且次要 / 有效且重大 / 部分有效 / 政治性 / 超出范围），并提出与具体 paper anchor 关联的回应前提；随后 `rebuttal-builder` 产出逐条 markdown rebuttal。叠加 `devils-advocate` 可预判 reviewer 在下一轮的反驳。

---

## 撰写综述或相关工作

**在动笔之前规划综述结构。** `survey-shape` 引导你在几轮对话中完成叙述弧线决策（按时间 / 方法 / 结果分组 / 研究空白驱动 / 整合式）和核心论文选择，无需提前写任何散文。同一份结构决策可同时驱动 `survey-narrative`（带 `\cite{}` 键的 1–3 段散文）和 `survey-table`（比较矩阵），一次决策，多份交付物。

**查找某个主题的相关工作。** `paper-finder` 按主题搜索 hub，支持按 venue 和年份过滤，按相关性排序，并可选导出整洁的 BibTeX 文件。将返回的 RID 直接输入 `survey-narrative` 或 `survey-table`，跳过发现阶段。

---

## 发现与浏览文献

**查找某主题的已有研究。** `paper-finder` 按主题搜索 hub，支持按 venue 类型和年份过滤，并按相关性、时效性或 claim 密度排序。

**并排比较两篇论文。** `paper-compare` 产出结构化 diff，展示两个 sidecar 之间共同引用的文献、分歧论断以及直接矛盾之处。

**追溯论文的版本历史。** `version-inspector` 沿 sidecar 替换链向前追溯，适合查看不同修订轮次之间的变化。

---

## 寻找下一个研究方向

**获取开放研究问题的简报。** `next-step-advisor` 检索你主题相关的 sidecar，从论文自身承认的局限性和遗留问题中提取有依据的下一步候选方向，同时纳入已发布于 `commentary@1` sidecar 中的读者反思。结果基于启发式规则，受限于 hub 上的内容，并非全语料范围。

---

## 纯思维工具（不产出 artifact）

**反驳自己的计划。** `devils-advocate` 对你正在做的任何决策或论断提出最有力的反驳，直到你改变主意或成功辩护。

**映射系统的故障模式。** `red-team` 每轮列举 3 个具体攻击向量（输入空间、信任边界、状态、组合、规模等），按可能性 × 影响范围 × 缓解成本排序。不同于 devils-advocate（质疑前提）——red-team 接受前提并寻找断点。

**在 agent 不给出答案的情况下思考问题。** `socratic` 模式每轮最多提 2 个问题，从不直接回答，适合在卡壳时需要一个不打断你推理过程的思维伙伴。

**将长输出压缩成 3 条要点。** `executive-summary` 将任何输入削减为 ≤3 条、每条 ≤15 个词的要点，禁止使用套话（"关键要点"、"本质上"、"向前看"）。适合海报、演讲或非技术读者。

---

## 不知道该选哪个工作流？

用日常语言告诉 agent 你的使用场景（"我想在 NeurIPS 投稿前自我评审论文"、"帮我回应 reviewer 意见"、"我想为这篇论文发布社区 commentary"）。`stance-mix` 元 skill 会将使用场景匹配到对应的主链加独立叠加项，并告诉你激活每个部分的具体说法。是否接受这个提议由你决定——`stance-mix` 不会自动级联执行。

---

## 下一步

- **深入了解单个 skill**：浏览 [`sub-skills/`](sub-skills/)（12 个 artifact emitter）或 [`stances/`](stances/)（11 个对话姿态）。
- **了解 orchestrator**：阅读 [`SKILL.md`](SKILL.md)，了解 dispatch 合约、配方和架构。
- **编写新 stance 或 skill**：阅读 [`stances/REFERENCE.md`](stances/REFERENCE.md) 和 [`references/dispatch-and-profile.md`](references/dispatch-and-profile.md)。
- **了解 sidecar 是什么**：阅读项目根目录的 [`../README.md`](../README.md)。
