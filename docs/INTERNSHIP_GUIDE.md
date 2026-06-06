# 实习/兼职展示指南

这个项目适合投递 AI 应用开发、全栈开发、后端开发、AIGC 工具开发、数据/研究自动化相关实习。

## 一句话介绍

我做了一个 AI Research Agent。用户输入研究主题后，系统会自动拆解子问题、联网搜索资料、抓取网页内容、生成带引用的研究报告，并支持 Markdown、PDF、PPTX 导出。

## 简历写法

可以直接放在项目经历里：

- 开发 AI Research Agent，基于 Next.js + FastAPI 实现从选题输入、任务拆解、联网检索、内容抽取、LLM 总结到报告导出的完整自动化研究流程。
- 使用 Server-Sent Events 实现长任务实时进度流，前端可展示 decomposition、search、synthesis、export 等阶段状态。
- 设计研究质量评估模块，统计来源数量、引用覆盖率、来源域名多样性、任务成功率和 confidence score，提升 AI 输出可评估性。
- 增强后端稳定性和安全性：请求校验、CORS 配置、并发限制、私有地址抓取拦截、DuckDuckGo fallback、pytest mock 测试。
- 使用 Docker Compose、Railway/Render 配置和 Vercel 环境变量完成部署准备。

## 面试可讲技术点

### 1. 为什么不是简单调用大模型？

这个项目不是把用户问题直接发给 LLM，而是拆成多个阶段：

1. Task decomposition
2. Web search
3. Content extraction
4. Per-track summarization
5. Report synthesis
6. Export
7. Quality evaluation

这样可以降低幻觉风险，并且让输出有来源和质量指标。

### 2. 为什么用 SSE？

研究任务可能运行几分钟。如果用普通 HTTP 请求，用户只能等待，体验很差。SSE 可以让后端持续推送状态，前端实时展示每个阶段。

### 3. 怎么控制成本？

- `quick/standard/deep` 控制子任务数量。
- `SEARCH_MAX_RESULTS` 控制每个子任务搜索结果数量。
- `FETCH_TOP_N` 控制深入抓取网页数量。
- `MAX_PARALLEL_RESEARCH_TASKS` 控制并发。
- `CONTENT_FETCH_MAX_CHARS` 限制发给模型的内容长度。

### 4. 怎么处理失败？

单个子任务失败不会让整个报告失败。系统会记录 failed task，继续用成功的任务生成报告，并在 quality warnings 里提示。

### 5. 怎么评估 AI 输出质量？

项目新增了质量评估：

- sources 是否足够
- 来源域名是否多样
- summary 是否有 `[1]` 这类引用
- 子任务成功率
- confidence score
- warnings

这是面试里很好的亮点，因为它说明你知道 AI 系统不能只看“能不能生成”，还要看“生成质量是否可评估”。

## 还可以继续提升

优先级从高到低：

1. 部署在线 Demo：Vercel + Railway/Render。
2. 配置真实 DeepSeek/Tavily key，让完整流程可演示。
3. 增加用户登录和报告隔离。
4. 把长任务改成后台队列，例如 Celery/RQ/Redis。
5. 增加引用校验，检查报告中的引用是否真的来自 sources。
6. 增加 arXiv/Semantic Scholar 学术搜索。
7. 把 PDF/PPTX 存到 Supabase Storage 或 Cloudflare R2。

## 面试时不要夸大的点

不要说这是“完全生产级”。更准确的说法是：

> 这是一个接近真实产品形态的 AI research assistant prototype。我重点做了 agent pipeline、SSE 实时状态、来源抓取、报告导出和质量评估。下一步如果产品化，我会加入用户系统、后台队列、对象存储和更严格的 citation verification。

这种说法更可信。
