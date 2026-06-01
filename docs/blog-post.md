# 我是如何做一个 AI Research Agent 的

> 从零构建一个能自动搜索、分析、生成报告的多智能体研究系统

---

## 背景：为什么需要一个 AI Research Agent？

在过去，做任何深度研究都需要人工完成一套固定流程：

1. 打开 Google，搜索关键词
2. 打开 10+ 个网页，逐篇阅读
3. 手动摘录重点，整理笔记
4. 把碎片信息组装成文章或报告
5. 排版、导出、分享

这个过程通常需要 **几个小时到几天**。而 LLM 的出现，让我们有机会把这个流程完全自动化。

但单纯的 LLM 有一个致命缺陷：**知识截止日期**。ChatGPT 或 Claude 独自工作时，无法获取最新信息。它们需要"眼睛"和"手"——搜索网页 + 阅读内容 + 综合分析。

这就是 AI Research Agent 要解决的问题：**给 LLM 装上工具，让它们真正地去"做研究"。**

## 核心设计理念

在动手写代码之前，我确立了三条原则：

### 1. 多智能体协作，而非单一大 Prompt

与其写一个巨大的 prompt 让一个 agent 做所有事情，不如把研究流程拆成多个专职 agent：

```
Task Decomposer → 拆解研究主题
Researcher × N   → 并行搜索每个子主题
Synthesizer      → 汇总生成最终报告
```

这样做的好处：
- 每个 agent 的职责清晰，prompt 可以精准优化
- 子任务可以并行执行，大幅提速
- 错误隔离：一个子主题失败不影响其他

### 2. SSE 流式传输，不让人等待

研究过程可能需要 1-3 分钟。如果用户盯着空白页面等待，体验极差。

使用 **Server-Sent Events (SSE)** 流式推送每一步进展：

```
🔍 Analyzing research topic...
✅ Found 5 subtopics
📖 Researching: Industry Trends (1/5)
📖 Researching: Top Companies (2/5)
✅ Completed: Industry Trends
...
📝 Synthesizing final report...
🎉 Report ready!
```

### 3. 自定义 Agent Loop，拒绝框架锁定

我选择直接使用 Anthropic SDK 构建 agent loop，而非 LangChain 或 CrewAI。原因：

- **透明**：每一行 agent 逻辑都是自己写的，出问题能立刻定位
- **轻量**：没有框架依赖的开销，部署更简单
- **可控**：prompt 完全自定义，不会被框架的"最佳实践"绑架

## 技术实现深度解析

### 整体架构

```
Next.js (Vercel) → FastAPI (Railway) → Claude API + Tavily + Supabase
```

选型理由：
- **Next.js**：SEO 友好、App Router 的路由组织清晰、Vercel 一键部署
- **FastAPI**：Python 异步、自动生成 API 文档、对 SSE 支持良好
- **Claude API**：tool use 能力强、输出结构化好、推理深度优于竞品
- **Tavily**：专为 AI agent 设计的搜索 API，返回干净的结构化结果

### 核心模块拆解

#### 1. Task Decomposer — 把大问题拆成小问题

这是整个流程的第一步，也是决定研究质量的关键。

```python
def decompose(self, topic: str, depth: str) -> list[str]:
    prompt = f"""You are a research analyst. Given the topic:
    
    "{topic}"
    
    Break it down into {subtopic_count} focused subtopics for research.
    Each subtopic should be specific and researchable via web search.
    
    Depth level: {depth}
    """
    
    response = self.client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return parse_subtopics(response.content[0].text)
```

关键设计：根据 depth 参数动态调整子主题数量：
- `quick` → 2-3 个子主题（快速概览）
- `standard` → 4-5 个（平衡深度）
- `deep` → 6-8 个（详尽研究）

#### 2. Researcher — 搜索 + 阅读 + 总结

这是最复杂的模块，因为需要串联多个工具：

```python
async def research(self, subtopic: str) -> ResearchTask:
    # Step 1: Web search
    search_results = await self.search_tool.search(subtopic, max_results=5)
    
    # Step 2: Fetch content of top 3 results
    for result in search_results[:3]:
        result["content"] = await self.content_fetcher.fetch(result["url"])
    
    # Step 3: Summarize with Claude
    summary = await self.summarize(subtopic, search_results)
    
    return ResearchTask(
        subtopic=subtopic,
        summary=summary,
        sources=search_results,
        status="complete"
    )
```

**遇到的一个坑**：很多网页的正文提取非常困难。导航栏、广告、评论区混在一起。解决方案：

- 使用 BeautifulSoup 提取 `<article>`、`<main>` 等语义标签
- 移除 `<script>`、`<style>`、`<nav>`、`<footer>`
- 对剩余文本按段落长度加权过滤
- 截断到 5000 字符避免 token 浪费

#### 3. Synthesizer — 把碎片拼成完整报告

这一步决定最终输出的质量。关键 prompt 设计：

```
你将收到多个子主题的研究摘要。请综合所有信息，生成一份专业的研究报告。

报告结构：
1. 执行摘要（2-3 段概括）
2. 每个子主题的详细章节（包含关键数据和引用来源）
3. 关键要点（可操作的 bullet points）
4. 参考资料列表

要求：
- 使用 Markdown 格式
- 所有数据引用必须注明来源链接
- 避免重复，要跨章节交叉引用
- 语言专业但不枯燥
```

#### 4. Report Generator — 多格式输出

Markdown 是通用格式，但不同场景需要不同格式：

| 格式 | 使用场景 | 转换方法 |
|------|---------|---------|
| Markdown | 开发者、笔记、Git | 直接输出 |
| PDF | 正式报告、打印、分享 | MD → HTML → WeasyPrint |
| PPTX | 演讲、汇报 | python-pptx 逐页构建 |

PDF 的生成坑最多：
- WeasyPrint 依赖系统库（Pango、Cairo），Docker 里要额外安装
- 中文排版需要合适的字体
- 页码、目录、页眉需要 CSS `@page` 规则

### SSE 流式传输的实现

后端用 FastAPI 的 `EventSourceResponse`，前端用 `fetch` + `ReadableStream`：

```typescript
// 前端 SSE 消费者
const response = await fetch(`${API_URL}/api/research`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic, depth })
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      handleEvent(event);  // Update UI in real-time
    }
  }
}
```

### 数据库设计

Supabase (PostgreSQL) 的表设计非常简洁，只有两张核心表：

```sql
research_reports — 存储完整报告
research_tasks   — 存储每个子主题的研究结果（外键关联 report）
```

用 JSONB 存储 sources 数组，可以灵活存不同结构的引用数据。

## 部署与运维

### 部署方案

生产环境使用三层架构：

```
Vercel (Frontend) → Railway (Backend) → Supabase (Database)
```

全部有免费额度，个人项目零成本运行。

### CI/CD

GitHub push → Vercel 自动部署前端 + Railway 自动部署后端。无需手动操作。

### 成本分析

单次标准深度的研究（5 个子主题）：

- Claude API：~$0.03（decompose + 5× summarize + synthesize，总计约 15K tokens）
- Tavily API：~$0.005（5 × 5 = 25 次搜索，在免费额度内）
- Supabase：免费额度绰绰有余
- **单次总成本：约 $0.03-0.08**

## 开发中的三个关键教训

### 1. 搜索质量 >> 搜索数量

最初我每个子主题搜 10 条结果，但摘要质量反而不如搜 5 条。原因是：
- 低质量结果混入噪音，LLM 难以分辨
- Token 消耗翻倍，但信息增益边际递减
- 最终锁定在 `max_results=5`，取前 3 篇深度阅读

### 2. Prompt 是产品逻辑，不是自然语言

不要用"请帮我..."这样的聊天式 prompt。给 agent 的 prompt 要像写代码一样精确：

```
❌ "Please search for information about..."
✅ "Search query: '{subtopic}'. Return a structured summary with:
    - 3 key findings
    - 2 relevant statistics with source URLs
    - 1 contrarian viewpoint if available"
```

### 3. 错误处理不是可选项

当依赖外部 API 时，失败是常态：
- Tavily 偶尔超时 → 重试 2 次，还失败就降级用空结果
- 网页可能 403/404 → 静默跳过，不阻断整个流程
- Claude API 可能 rate limit → 指数退避重试
- 每个 try/except 都要考虑：**部分结果 > 没有结果**

## 未来方向

这个项目下一步的可能优化：

1. **多 LLM 支持**：支持切换 OpenAI、Gemini、本地模型
2. **学术搜索**：接入 arXiv、Google Scholar API
3. **持久化记忆**：同一主题的后续研究可以基于前次结果深入
4. **协作研究**：多人同时编辑、评论研究大纲
5. **定时研究**：设置周期性自动研究（如每周生成行业动态报告）

## 总结

构建 AI Research Agent 的过程让我深刻体会到：**AI 应用的本质不是模型本身，而是如何把模型的能力编排成有价值的用户体验。**

Claude 可以写摘要，Tavily 可以搜索，FastAPI 可以流式传输——这些单独看都不新鲜。但把它们组合成一个 3 分钟自动生成专业研究报告的 pipeline，就从"演示"变成了"产品"。

如果你也在做类似的 AI 应用，欢迎交流讨论！

---

**项目地址**: [github.com/YOUR_USERNAME/ai-research-agent](https://github.com/YOUR_USERNAME/ai-research-agent)

**在线演示**: [ai-research-agent.vercel.app](https://ai-research-agent.vercel.app)

**技术栈**: Claude API · FastAPI · Next.js · Tavily · Supabase · Docker
