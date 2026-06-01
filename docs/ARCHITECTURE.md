# 🏗️ System Architecture

## High-Level Overview

The AI Research Agent is a **multi-agent pipeline** that automates research end-to-end. It follows a modular, tool-based architecture where each stage of the research process is handled by a specialized agent component.

```
┌──────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Next.js 14 Frontend                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│  │  │Research  │ │Progress  │ │Report Viewer     │   │  │
│  │  │Form      │ │Tracker   │ │(Markdown/PDF)    │   │  │
│  │  └──────────┘ └──────────┘ └──────────────────┘   │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ SSE Stream
┌────────────────────────▼─────────────────────────────────┐
│                    API LAYER                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │  FastAPI (Python)                                   │  │
│  │  • POST /api/research      (SSE streaming)         │  │
│  │  • GET  /api/report/{id}    (report retrieval)     │  │
│  │  • GET  /api/report/{id}/download (PDF/PPTX)       │  │
│  │  • GET  /api/history        (past reports)         │  │
│  │  • GET  /api/health         (health check)         │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                   AGENT LAYER                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Orchestrator                                       │  │
│  │  ┌──────────┐                                      │  │
│  │  │ Control  │── Manages the full pipeline flow      │  │
│  │  │ Loop     │── Emits SSE progress events           │  │
│  │  └────┬─────┘                                      │  │
│  │       │                                             │  │
│  │  ┌────▼─────┐  ┌──────────┐  ┌────────────────┐   │  │
│  │  │ Task     │  │Researcher│  │  Synthesizer   │   │  │
│  │  │Decomposer│──│ (per     │──│  (combines     │   │  │
│  │  │          │  │ subtopic)│  │   all results) │   │  │
│  │  └──────────┘  └────┬─────┘  └────────┬───────┘   │  │
│  │                     │                  │            │  │
│  └─────────────────────┼──────────────────┼───────────┘  │
└────────────────────────┼──────────────────┼──────────────┘
                         │                  │
┌────────────────────────▼──────────────────▼──────────────┐
│                    TOOLS LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │  Web     │  │ Content  │  │  Report Generator    │   │
│  │  Search  │  │ Fetcher  │  │  • MD → HTML         │   │
│  │(Tavily)  │  │(httpx+BS)│  │  • HTML → PDF        │   │
│  │          │  │          │  │  • Bullets → PPTX     │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                 EXTERNAL SERVICES                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐           │
│  │  Claude   │  │  Tavily   │  │  Supabase    │           │
│  │  API      │  │  Search   │  │  PostgreSQL  │           │
│  └──────────┘  └──────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────┘
```

## Research Pipeline (Step by Step)

### 1. Task Decomposition

**Agent**: `TaskDecomposer`
**Input**: User's research topic + depth level
**Process**: Claude analyzes the topic and generates 3-7 targeted subtopics

```
Input: "AI internship market 2026"
Output:
  1. Industry trends & market size
  2. Top companies hiring AI interns
  3. Required skills & technologies
  4. Compensation & benefits data
  5. Application process & interview tips
```

**Depth levels** control granularity:
- `quick` → 2-3 subtopics for rapid overview
- `standard` → 4-5 subtopics for balanced coverage
- `deep` → 6-8 subtopics for exhaustive research

### 2. Parallel Research

**Agent**: `Researcher` (one instance per subtopic)
**Process**: For each subtopic:

1. **Web Search** (`SearchTool`): Query Tavily API with optimized search terms
2. **Content Fetching** (`ContentFetcher`): Retrieve top 3 results, extract text content via BeautifulSoup
3. **Summarization** (Claude): Generate a 2-3 paragraph summary with key insights, citing specific sources

```
Subtopic: "Top companies hiring AI interns"
  ├── Search: "AI internship companies 2026 hiring"
  ├── Fetch: 3 article contents extracted
  ├── Summarize: "The top companies hiring AI interns in 2026
  │    include Google DeepMind, OpenAI, Anthropic, Microsoft
  │    Research, and Meta AI. These companies are particularly
  │    focused on candidates with LLM and agent-building
  │    experience. [Source: techcrunch.com, ...]"
  └── Sources: [url, title, date for each]
```

### 3. Synthesis

**Agent**: `Synthesizer`
**Input**: All completed `ResearchTask` objects
**Process**: Claude combines all summaries into a cohesive markdown report with:

- **Executive Summary** — 2-3 paragraph overview
- **Section per Subtopic** — expanded with cross-references
- **Key Takeaways** — actionable bullet points
- **References** — all cited sources with URLs

### 4. Report Generation

**Tool**: `ReportGenerator`
**Output formats**:

| Format | Method | Features |
|--------|--------|----------|
| Markdown | Direct text generation | Headers, tables, code blocks, links |
| PDF | Markdown → HTML → WeasyPrint | Professional CSS, page numbers, TOC |
| PPTX | python-pptx | Title slide + bullet slides per section |

## Streaming Protocol (SSE)

The backend uses **Server-Sent Events** (SSE) for real-time progress:

```
data: {"type":"decomposing","message":"Analyzing research topic...","data":{}}

data: {"type":"decomposed","message":"Found 5 subtopics","data":{"subtopics":["..."]}}

data: {"type":"researching","message":"Researching: Industry trends","data":{"task":"Industry trends","progress":1,"total":5}}

data: {"type":"task_complete","message":"Completed: Industry trends","data":{"task":{...}}}

data: {"type":"synthesizing","message":"Combining results into report...","data":{}}

data: {"type":"complete","message":"Report generated","data":{"report_id":"abc-123","report":{...}}}
```

## Database Schema

```sql
research_reports
├── id (UUID, PK)
├── topic (TEXT)
├── subtopics (JSONB)
├── markdown_content (TEXT)
├── search_results (JSONB)
├── status (TEXT)  -- pending|decomposing|researching|synthesizing|complete|error
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

research_tasks
├── id (UUID, PK)
├── report_id (UUID, FK → research_reports)
├── subtopic (TEXT)
├── summary (TEXT)
├── sources (JSONB)
├── status (TEXT)  -- pending|searching|summarizing|complete|error
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

## Design Decisions

### Why Custom Agent Loop (not LangChain)?

We opted for a **custom agent loop** using the Anthropic SDK directly rather than LangChain/LangGraph because:

1. **Simplicity** — fewer abstractions, easier to debug
2. **Control** — full control over prompts and tool calling behavior
3. **Performance** — no framework overhead
4. **Portability** — no vendor lock-in to a specific agent framework

### Why SSE over WebSockets?

- SSE is **simpler** — one-directional server→client stream
- No need for bidirectional communication in this use case
- Native browser support via `EventSource` API
- Works through most proxies without special configuration

### Why Tavily over Google/Bing API?

Tavily is **purpose-built for AI agents** — it returns clean, structured results optimized for LLM consumption, unlike general search APIs that return raw HTML.
