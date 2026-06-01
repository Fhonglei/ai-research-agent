# 我是如何用 AI 自动化内容生产流程的

> 从选题到发布：构建一条"无人值守"的内容生产线

---

## 背景：内容生产的真实痛点

作为一个独立开发者，我面临一个经典困境：

**不做内容 → 没有流量 → 产品没人知道 → 失败**

但做内容需要：
- 每天刷新闻找选题（1 小时）
- 调研、阅读、做笔记（2 小时）
- 写初稿、修改、润色（3 小时）
- 排版、配图、发布（1 小时）
- 各平台分发、回复评论（1 小时）

**一天 8 小时没了，代码一行没写。**

所以我思考：既然内容生产的每个环节都有明确的输入和输出，能否用 AI 把整条流水线自动化？

## 设计哲学：不是替代人类，是消除重复劳动

重要的事说在前面：**AI 不是替代创作者，而是替代创作中 80% 的机械劳动。**

我把内容生产拆成两个维度：

| 环节 | AI 擅长？ | 策略 |
|------|----------|------|
| 选题发现 | ✅ 扫描大量信息源 | AI 筛选 + 人工确认 |
| 资料收集 | ✅ 搜索、阅读、提炼 | 全自动 |
| 初稿撰写 | ⚠️ 结构好但缺乏灵魂 | AI 写骨架 + 人填血肉 |
| 事实核查 | ⚠️ 会幻觉 | AI 标引用 + 人验证 |
| 排版发布 | ✅ 格式转换 | 全自动 |
| 观点表达 | ❌ 没有真实体验 | 完全人工 |

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                  Content Pipeline                 │
│                                                   │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐       │
│  │ 选题引擎 │ → │ 研究Agent│ → │ 写作Agent│       │
│  │ (Trends  │   │ (Search +│   │ (Draft + │       │
│  │  Scanner)│   │  Summarize)  │  Polish) │       │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘       │
│       │               │               │            │
│       ▼               ▼               ▼            │
│  RSS Feeds       Tavily API      Claude API       │
│  Twitter API     Web Scraping    GPT-4           │
│  Google Trends   News APIs       Templates       │
│                                                   │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐       │
│  │ 审核面板 │ ← │ 排版引擎 │ ← │ 发布调度 │       │
│  │ (Human   │   │ (Format  │   │ (Multi-  │       │
│  │  Review) │   │  Convert)│   │  Platform)│       │
│  └─────────┘   └─────────┘   └──────────┘       │
└─────────────────────────────────────────────────┘
```

## 四大核心模块

### 模块 1：选题引擎 — 让 AI 帮你发现"值得写"的话题

好的选题 = 用户关心 + 竞争不激烈 + 你有独特视角

```python
class TopicDiscovery:
    """每日扫描信息源，输出按热度+相关性排序的选题列表"""
    
    SOURCES = [
        "rss://news.ycombinator.com/rss",
        "rss://arxiv.org/rss/cs.AI",
        "twitter://list/ai-developers",
        "trends://google?category=technology",
        "reddit://r/MachineLearning/hot",
    ]
    
    async def discover(self) -> list[TopicIdea]:
        candidates = []
        
        # 1. 并行扫描所有信息源
        for source in self.SOURCES:
            items = await self.fetch_source(source)
            candidates.extend(items)
        
        # 2. 去重 + 聚类（同一话题的多篇报道合并）
        clusters = await self.cluster_by_semantic_similarity(candidates)
        
        # 3. 评分：热度 × 竞争度 × 相关度
        scored = []
        for cluster in clusters:
            score = (
                cluster.engagement_score * 0.4 +       # 用户有多关心
                cluster.competition_score * 0.3 +       # 已有多少内容
                cluster.relevance_score * 0.3           # 和我的领域多相关
            )
            scored.append(TopicIdea(
                title=cluster.main_headline,
                score=score,
                sources=cluster.sources,
                suggested_angle=self.generate_angle(cluster),
            ))
        
        # 4. 返回 Top 5，包含"建议切入角度"
        return sorted(scored, key=lambda x: x.score, reverse=True)[:5]
```

**一个发现**：最好的选题往往来自交叉信息源。比如 Hacker News 上有讨论 + arXiv 上新论文 + Twitter 上 KOL 在争论 → 这是最佳写作时机。

### 模块 2：研究 Agent — 30 分钟的研究变成 3 分钟

这就是 AI Research Agent 的作用。选题确定后，自动：

1. 拆解为子话题
2. 搜索相关文章
3. 提取关键事实和数据
4. 生成带引用的研究笔记

```
输入: "2026年向量数据库市场现状"
输出:
  ├── 市场规模: $2.3B, CAGR 35% [来源: Gartner 2026]
  ├── 主要玩家: Pinecone, Weaviate, Milvus, Qdrant, Chroma
  ├── Pinecone: $1.3B 估值, 最新融资 Series C $150M [来源: TechCrunch]
  ├── 趋势: Serverless, Hybrid Search, Multi-modal embeddings
  └── 关键引用: 5 处，带原文链接
```

### 模块 3：写作 Agent — 骨架自动生成，人只填"灵魂"

这是最关键的一步。我的原则是：**AI 负责结构和信息密度，人负责观点和个人经验。**

```python
WRITING_SYSTEM_PROMPT = """你是一个专业技术内容编辑。根据研究笔记撰写文章。

文章结构要求：
1. 开头：用一个具体的问题或场景引入（不要用"在当今时代..."）
2. 正文：每个论点必须配一个具体的数据或案例（来自研究笔记）
3. 过渡：段落之间要有逻辑递进，不是清单式罗列
4. 结尾：给出可操作的建议或思考框架

风格要求：
- 像在给同事解释一个问题，不是写教科书
- 短句为主（15-25字），穿插 1-2 句长句
- 每 300 字至少一个具体例子
- 不要用"值得注意的是""毫无疑问""众所周知"这类废话

格式：
- 在 [需要人工补充观点或经验] 的地方用 <<<INSERT_PERSONAL_INSIGHT>>> 标记
- 在研究笔记没有覆盖但读者会关心的地方用 <<<NEEDS_VERIFICATION>>> 标记"""
```

这个 prompt 的核心是 **<<>>，在需要人工介入的地方做显式标记。这样我只需要花 15 分钟审核 + 补充，而不是从头写。

### 模块 4：排版 + 多平台发布

```python
class ContentPublisher:
    PLATFORMS = {
        "blog": {
            "format": "markdown",
            "frontmatter": ["title", "date", "tags", "description"],
        },
        "wechat": {
            "format": "rich_text",
            "requirements": ["封面图 900x383", "摘要 120字以内", "文末引导关注"],
        },
        "twitter": {
            "format": "thread",
            "requirements": ["每条 280 字符", "第一条必须 hook", "最后一条加 CTA"],
        },
        "linkedin": {
            "format": "long_post",
            "requirements": ["开头 3 行决定展开率", "每段 ≤ 3 行", "加 3-5 个 hashtag"],
        },
        "juejin": {
            "format": "markdown",
            "requirements": ["封面图", "掘金特殊语法", "分类标签"],
        },
    }
    
    async def publish(self, article: Article, platforms: list[str]):
        for platform in platforms:
            config = self.PLATFORMS[platform]
            
            # 1. 格式转换
            formatted = self.convert_format(article.content, config["format"])
            
            # 2. 平台适配
            adapted = self.adapt_for_platform(formatted, config["requirements"])
            
            # 3. AI 生成平台特定元素（摘要、标题变体、Hashtag）
            if "description" in config.get("elements", []):
                adapted["description"] = await self.generate_description(article)
            
            # 4. 排队发布（避免同一时间发多个平台被标记为 spam）
            await self.schedule_publish(platform, adapted)
```

## 实际效果

用这条流水线运营技术博客 3 个月的数据：

| 指标 | 纯人工 | AI 辅助 |
|------|--------|---------|
| 每篇文章耗时 | 6-8 小时 | 1.5-2 小时 |
| 月产出 | 4 篇 | 12 篇 |
| 平均阅读量 | 800 | 1200（量多覆盖更多关键词） |
| Google 收录时间 | 3-7 天 | 1-3 天（规律发布信号更好） |
| 我的投入 | 每周 2 天 | 每周 4 小时 |

**最重要的是**：我不再因为"没时间写文章"而焦虑。AI 处理了研究、初稿、排版、发布，我只需要做两件事——**确认选题方向**和**加入个人观点**。

## 三个血泪教训

### 1. AI 写的内容能检测出来

最早的版本，我让 AI 从头写到尾。结果：
- 遣词造句有明显模式（"值得注意的是"出现了 8 次）
- 文章四平八稳，没有棱角
- 读者留言："这篇是 ChatGPT 写的吧？"

**修正**：现在我确保每篇文章至少有 30% 是我自己写的——开头 hook、个人经历、争议性观点。搜索引擎和读者都能分辨。

### 2. 多平台不是"一键同步"

简单地写一篇文章然后同步到 5 个平台，效果很差：
- 微信公号需要"爽点"密集
- Twitter 需要每条都能独立传播
- 掘金需要更 technical
- LinkedIn 需要更 business

**修正**：每个平台用单独的 prompt 做内容适配，不只是格式转换。

### 3. 事实核查不可省略

AI 研究 Agent 找的信息不一定对。有次它引用了一个"Gartner 报告"，链接点进去是 404。后来发现那个数据是一个咨询公司博客编的，被多个 AI 内容农场引用后扩散了。

**修正**：我现在要求 Agent 标注每个事实的"可信度"：
- 🟢 官方来源（年报、财报、政府数据）
- 🟡 媒体报道（知名科技媒体）
- 🔴 间接引用（博客、论坛、其他 AI 生成内容）

审核时重点看 🔴。

## 这个系统的开源版本

这篇文章描述的内容生产流水线的"研究"部分，我提取出来开源成了 [AI Research Agent](https://github.com/Fhonglei/ai-research-agent)。它可以独立使用——给一个话题，返回带引用的研究报告。

## 总结

AI 内容自动化的真正价值不是"省掉写作者"，而是 **把创作者从信息收集和格式转换中解放出来，把时间花在只有人能做的事情上：形成观点、分享经验、建立信任。**

我的建议：如果你打算用 AI 做内容，从"研究助手"开始，而不是"写作替代"。先让 AI 帮你找资料、理结构，你只负责写。习惯了这个节奏后，再逐步让 AI 承担更多。

---

**相关项目**: [AI Research Agent](https://github.com/Fhonglei/ai-research-agent) — 多智能体自动化研究系统，内容生产流水线的开源核心组件
