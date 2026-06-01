# 我是如何做一个 RAG 知识库系统的

> 从向量检索到语义理解，构建一个能真正回答问题的 AI 知识库

---

## 背景：为什么现有搜索不够用？

传统的企业知识库面临两个困境：

1. **关键词搜索太笨** — 用户问"上季度销售额怎么样？"，系统搜"销售额"返回 200 篇文档
2. **信息更新滞后** — 文档散落在 Notion、Google Docs、Slack、邮件里，没人维护统一的知识库

而 LLM 本身有两个致命缺陷：
- **幻觉**：不知道的事情会编造
- **知识截止日期**：训练数据停在某个时间点

**RAG（Retrieval-Augmented Generation）** 正是解决方案：先检索相关文档，再让 LLM 基于这些文档回答问题。LLM 不需要"知道"答案，只需要"理解"检索到的内容。

## 核心架构

```
用户提问
    │
    ▼
┌──────────────┐
│  Query        │  把问题改写为搜索查询
│  Rewriting    │  "上季度销售额" → "2025 Q4 sales revenue report"
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Embedding    │  查询向量化 → [0.23, -0.67, 0.41, ...]
│  Model        │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Vector       │  余弦相似度搜索 → Top-K 相关文档
│  Database     │  Pinecone / Chroma / pgvector
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Reranker     │  精排：Cross-encoder 重新打分
│  (optional)   │  召回 20 篇 → 精排到 5 篇
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  LLM          │  Prompt = 系统指令 + 检索文档 + 用户问题
│  Generation   │  → 生成带引用的答案
└──────────────┘
```

## 技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| Embedding | text-embedding-3-small (OpenAI) | 性价比最高，1536维 |
| Vector DB | Chroma | 开源，Python 原生，零配置 |
| Chunking | LangChain RecursiveCharacterTextSplitter | 按段落+句子边界智能切分 |
| LLM | Claude 3.5 Sonnet | 引用能力强，幻觉率低 |
| Framework | 纯 Python + FastAPI | 避免 LangChain 的复杂抽象 |

## 核心实现

### 1. 文档摄入管道

这是 RAG 系统最容易被低估的部分。垃圾进，垃圾出。

```python
class DocumentPipeline:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
    
    async def ingest(self, file_path: str) -> list[Document]:
        # Step 1: 解析文件
        text = await self.parse_file(file_path)
        
        # Step 2: 清洗
        text = self.clean_text(text)
        
        # Step 3: 切块
        chunks = self.splitter.split_text(text)
        
        # Step 4: 添加元数据
        docs = []
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                content=chunk,
                metadata={
                    "source": file_path,
                    "chunk_index": i,
                    "char_start": i * self.chunk_size,
                }
            ))
        
        # Step 5: 向量化并存储
        embeddings = self.embedder.embed_documents([d.content for d in docs])
        self.vector_db.add(
            ids=[str(uuid.uuid4()) for _ in docs],
            embeddings=embeddings,
            documents=[d.content for d in docs],
            metadatas=[d.metadata for d in docs],
        )
        
        return docs
```

### 2. Chunking 策略 — 最关键的调参

Chunk 太大 → 检索精度低，LLM 被无关信息分散注意力
Chunk 太小 → 语义不完整，一个句子拆成两半

我的经验法则：
- **技术文档**：512 tokens，overlap 50
- **法律/合同**：256 tokens，overlap 100（精确匹配重要）
- **教程/博客**：1024 tokens，overlap 100（需要完整上下文）

**一个坑**：不要用固定字符数切分中文。中文字符密度高，500 个中文字符的信息量 ≈ 1500 个英文字符。所以我的 splitter 用 token count 而不是 character count。

### 3. 检索策略：不止向量搜索

纯向量搜索的召回率不够。我用了三层检索：

```
Layer 1: 向量搜索 (semantic similarity) → 召回 20 篇
Layer 2: BM25 关键词搜索 (lexical matching) → 召回 10 篇  
Layer 3: 合并去重 → Reranker 精排 → 取 Top 5
```

BM25 补足了向量搜索的盲区：专有名词、产品代码、版本号。这些词汇在 embedding 空间里往往没有好的向量表示。

```python
async def hybrid_search(query: str, top_k: int = 5) -> list[Document]:
    # Vector search
    query_embedding = embedder.embed_query(query)
    vector_results = vector_db.similarity_search_by_vector(
        query_embedding, k=20
    )
    
    # BM25 keyword search
    bm25_results = bm25_index.search(query, k=10)
    
    # Merge & deduplicate by content hash
    all_results = merge_and_dedup(vector_results, bm25_results)
    
    # Rerank with cross-encoder
    reranked = cross_encoder.rerank(query, all_results, top_k=top_k)
    
    return reranked
```

### 4. Prompt Engineering for RAG

RAG 的 prompt 设计和普通聊天完全不同。关键是设置"护栏"：

```
System Prompt:
你是一个基于知识库的问答助手。严格遵守以下规则：

1. 只能根据下方【参考文档】中的信息回答。如果文档中没有相关信息，
   明确说"知识库中没有找到相关信息"，不要编造。
2. 每个回答必须标注信息来源（文档名称 + 段落编号）。
3. 如果文档信息之间存在矛盾，指出矛盾并列出两方的说法。
4. 使用引用格式：[来源: 文档名, 段落 X]

【参考文档】
{retrieved_documents}

【用户问题】
{user_query}

【回答】
```

关键设计点：
- **第 1 条**：防止幻觉，比任何 prompt 技巧都重要
- **第 3 条**：实际上很少触发，但让用户对系统有信心
- **引用格式**：让用户可以溯源验证，是 RAG 的核心信任机制

## 开发中的三个关键教训

### 1. Embedding 模型的选择比想象中重要

开始时我用了一个开源的中文 embedding 模型（text2vec-large-chinese），效果很差。切换成 OpenAI 的 text-embedding-3-small 后，同样的向量库，Top-5 准确率从 62% 提升到 89%。

**教训**：不要为了省钱用差的 embedding 模型。Embedding 质量是 RAG 系统的天花板。

### 2. 文档更新是最头疼的问题

用户上传了 v1 的文档，后来更新了 v2。但向量库里还有 v1 的 chunks。结果：同一个问题得到两个矛盾的回答。

**解决方案**：
- 每个文档入库时记录 `doc_version` 和 `uploaded_at`
- 更新时：标记旧版本为 `stale`，重新摄入新版本
- 检索时：过滤 `stale` chunks
- 这本质上是一个 **向量数据库的版本管理** 问题

### 3. 用户不会问"正确"的问题

真实用户输入往往是：
- "那个上个月的报告里说的数字是多少？"（模糊指代）
- "帮我看看那个东西"（缺乏上下文）
- "为啥数据不对？"（期望系统理解隐含上下文）

**解决方案**：Query Rewriting。在检索之前，用 LLM 把用户问题改写为精确的搜索查询。这一个小步骤让检索准确率提升了约 30%。

```
用户: "那个上个月的报告里的数字是多少？"
  ↓ Query Rewriting
改写: "2026年5月月度销售报告中的关键数据指标"
```

## 性能数据

在我的测试集上（200 篇文档，10,000+ chunks）：

| 指标 | 数值 |
|------|------|
| Top-5 检索准确率 | 89.2% |
| 答案准确率（有引用） | 94.1% |
| 平均响应时间 | 2.3 秒 |
| 幻觉率 | 1.7%（几乎都发生在文档信息不足时） |
| 单次查询成本 | ~$0.005 |

## 总结

RAG 系统的难点不在于单个组件，而在于 **组件之间的集成质量**。Embedding 模型、chunking 策略、检索算法、prompt 设计——每个环节的质量都会影响最终答案。

一个反直觉的发现：**检索质量比生成质量重要得多**。如果检索到了正确的文档，即使简单的 prompt 也能得到好答案。如果检索结果不对，再好的 LLM 也没用。

这就是为什么我花了 70% 的精力在检索管道上，只有 30% 在 prompt 设计上。

---

**相关项目**: [AI Research Agent](https://github.com/Fhonglei/ai-research-agent) — 一个基于多智能体的自动化研究系统
