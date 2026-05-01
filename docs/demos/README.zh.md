# Knows Orchestrator 演示（v1.0）

[English](./README.md) | 中文

三份演示文字稿，展示每个 MVP sub-skill 的实际运行——输入内容、dispatch 过程、底层发生了什么、产生的 artifact，以及 manifest 的生成。

| 演示 | 功能说明 | 适用场景 |
|---|---|---|
| [`paper-finder.md`](paper-finder.md) | 在 knows.academy 中搜索匹配指定查询的 sidecar | "帮我找 10 篇关于 X 的论文" / "给我 Y 查询的 BibTeX" |
| [`sidecar-reader.md`](sidecar-reader.md) | 根据 sidecar 回答问题（实现 consume-prompt v1.1） | "论文 X 用了什么数据集？" / "Y 的主要论点是什么？" / 任何 benchmark Q&A |
| [`sidecar-author.md`](sidecar-author.md) | 从 PDF / LaTeX / 文本块生成 sidecar | "为 paper.pdf 生成 sidecar" / "从我的 LaTeX 项目生成" |

## 通用 dispatch 结构

每个演示都遵循相同的 orchestrator 合约：

```
User intent → (intent_class, required_inputs, requested_artifact) → sub-skill → artifact + manifest
```

完整合约见 [`../../skills/references/dispatch-and-profile.md`](../../skills/references/dispatch-and-profile.md)。每个 sub-skill 继承 7 个 orchestrator 守卫（G1–G7），覆盖 prompt 注入防护、质量过滤、profile 约束、传输缓存和 provenance manifest。

## 复现演示

每个演示底部都有"自己试试"章节，分别展示直接 API 调用和 Claude Code agent 调用两种方式。只读 API 端点无需任何认证即可使用。生成路径（sidecar-author 的 Path B）需要 `ANTHROPIC_API_KEY`。

关于这些演示所依赖的 orchestration 底层测试，见 [`../../skills/tests/`](../../skills/tests/)。3 个 fixture 共 25 个测试全部通过；按照 `dispatch-and-profile.md` §7.5，CI 全绿是 v1 版本发布的硬性前提。
