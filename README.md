# 🔬 AI Research Agent

> AI-powered automated research — enter a topic, get a comprehensive report in minutes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)

**🌐 Live Demo**: [fhonglei.github.io/ai-research-agent](https://fhonglei.github.io/ai-research-agent/) *(deploy your own in 5 min — see [Deployment Guide](docs/DEPLOYMENT.md))*

## 📖 Overview

The **AI Research Agent** automates the research workflow end-to-end. You provide a topic, and the system:

1. **Decomposes** the topic into focused subtopics using Claude AI
2. **Searches** the web for relevant, up-to-date information via Tavily
3. **Fetches & analyzes** source content with intelligent extraction
4. **Summarizes** each subtopic with key insights and citations
5. **Synthesizes** everything into a professional report
6. **Exports** to **Markdown**, **PDF**, and **PowerPoint**

### Example

```
Input:  "Research the AI internship market in 2026"

Output:
  ├── Executive Summary
  ├── Industry Trends & Market Overview
  ├── Top Companies Hiring AI Interns
  ├── In-Demand Skills & Technologies
  ├── Compensation & Benefits Landscape
  ├── Recommended Learning Roadmap
  ├── Key Takeaways
  └── References (with clickable links)
```

## 📸 Screenshots

### Research Form
![Research Form](docs/screenshots/research-form.png)
*Enter any research topic and select depth (Quick / Standard / Deep)*

### Real-time Progress
![Research Progress](docs/screenshots/research-progress.png)
*Watch each step: decomposition → searching → summarizing → file generation*

### Generated Report
![Report](docs/screenshots/report.png)
*Professional Markdown report with citations, rendered beautifully*

### Download Options
![Download](docs/screenshots/download.png)
*Export to PDF or PowerPoint with one click*

> **Note**: If screenshots are not yet uploaded, run the app locally (`npm run dev` + `uvicorn main:app`) to capture your own.

## ✨ Core Features

- 🤖 **Multi-Agent Pipeline** — Task decomposition, parallel research, synthesis
- 🔍 **Real Web Search** — Uses Tavily API for live, sourced information
- 📊 **Multiple Export Formats** — Markdown, PDF, PowerPoint
- 📡 **Real-time Progress** — SSE streaming shows every step as it happens
- 📚 **Research History** — All past reports saved and searchable
- 🎨 **Polished UI** — Clean, responsive design with dark mode support
- 🐳 **Docker Ready** — One-command local deployment

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Browser                       │
│              (Next.js Frontend — Vercel)             │
└────────────────────────┬────────────────────────────┘
                         │ SSE Stream
┌────────────────────────▼────────────────────────────┐
│              FastAPI Backend (Railway)                │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │Orchestrator│  │Researcher│  │ Report Generator │  │
│  └─────┬────┘  └────┬─────┘  └────────┬─────────┘  │
│        │             │                  │             │
│  ┌─────▼────┐  ┌────▼─────┐  ┌────────▼─────────┐  │
│  │Decomposer│  │SearchTool│  │ MD/PDF/PPTX Gen  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
         │              │                 │
    ┌────▼────┐   ┌────▼────┐    ┌───────▼──────┐
    │ DeepSeek │   │ Tavily   │    │  Supabase    │
    │ (LLM)    │   │ (Search) │    │  (Storage)   │
    └─────────┘   └─────────┘    └──────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed design document with data flow diagrams and design decisions.

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Frontend** | Next.js 14, Tailwind CSS, shadcn/ui | React UI with SSR |
| **Backend** | FastAPI, Python 3.12 | Async REST API |
| **AI/LLM** | DeepSeek V4-Pro (via OpenAI SDK) | Agent reasoning & summarization |
| **Search** | Tavily Search API | Real-time web search |
| **Database** | Supabase (PostgreSQL) | Report persistence & history |
| **Report Gen** | WeasyPrint, python-pptx | PDF & PowerPoint export |
| **Streaming** | SSE (Server-Sent Events) | Real-time progress updates |
| **Deployment** | Vercel + Railway + Docker | Production hosting |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- API keys for [Anthropic](https://console.anthropic.com/), [Tavily](https://app.tavily.com/), and optionally [Supabase](https://app.supabase.com/)

### 1. Clone & Configure

```bash
git clone https://github.com/Fhonglei/ai-research-agent.git
cd ai-research-agent

cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the App

Visit **http://localhost:3000** — enter a research topic and click "Start Research"!

### Docker (All-in-One)

```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## 📡 API Design

### `POST /api/research`

Start a new research task. Returns SSE stream.

```json
// Request
{ "topic": "AI internship market 2026", "depth": "standard" }

// SSE Events
event: decomposing
data: {"message": "Analyzing research topic..."}

event: decomposed
data: {"subtopics": ["Industry Trends", "Top Companies", ...]}

event: researching
data: {"message": "Researching: Industry Trends (1/5)"}

event: task_complete
data: {"subtopic": "Industry Trends", "status": "complete"}

event: complete
data: {"report_id": "abc-123", "markdown_content": "# Report...", ...}
```

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/report/{id}` | Retrieve a completed report |
| `GET` | `/api/report/{id}/download?format=pdf\|pptx` | Download as PDF or PPTX |
| `GET` | `/api/history` | List all past reports |
| `GET` | `/api/health` | Health check |

| Depth | Subtopic Count | Description |
|-------|---------------|-------------|
| `quick` | 2-3 | Brief overview for quick answers |
| `standard` | 4-5 | Balanced depth (default) |
| `deep` | 6-8 | Exhaustive research with more sources |

See [API.md](docs/API.md) for full API reference with request/response examples.

## 🗂️ Project Structure

```
ai-research-agent/
├── backend/
│   ├── agents/           # Agent logic (orchestrator, decomposer, researcher, synthesizer)
│   ├── tools/            # Tools (web_search, content_fetcher, report_generator)
│   ├── models/           # Pydantic schemas
│   ├── utils/            # Logging & helpers
│   ├── main.py           # FastAPI application
│   ├── config.py         # Environment configuration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages (home, history)
│   │   ├── components/   # React components
│   │   ├── lib/          # API client & utilities
│   │   └── types/        # TypeScript type definitions
│   └── package.json
├── docs/                 # Extended documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── blog-post.md
├── supabase/
│   └── schema.sql        # Database schema
├── docker-compose.yml
└── .env.example
```

## 🎯 Use Cases

- **Students** — Research papers, literature reviews, market analysis
- **Job Seekers** — Industry research, company analysis, skill gap assessment
- **Product Managers** — Competitive analysis, market research, trend reports
- **Content Creators** — Fact-checked article drafts, newsletter research
- **Developers** — Technology evaluation, framework comparison, best practices research

## 🐛 Problems Encountered & Solutions

### 1. Web Content Extraction Quality

**Problem**: Many web pages have messy HTML — navigation bars, ads, cookie banners, and comment sections get mixed with the actual content. Initial attempts with naive `body.get_text()` produced unusable noise that degraded Claude's summary quality.

**Solution**: Built a multi-step content extraction pipeline in `content_fetcher.py`:
- Target semantic HTML5 elements (`<article>`, `<main>`) first
- Strip non-content tags (`<script>`, `<style>`, `<nav>`, `<footer>`)
- Filter hidden elements via `aria-hidden` and `display:none` detection
- Truncate to 5000 characters to avoid token waste
- Always set a 10-second timeout to prevent pipeline stalls

### 2. SSE Event Type Mismatch Between Frontend and Backend

**Problem**: The backend sends SSE events with types like `decomposing`, `decomposed`, `researching`, but the frontend was looking for `decomposition`, `task_start`, `task_progress`. Events were silently dropped, and the UI showed no progress.

**Solution**: Designed a unified SSE event protocol. The backend event types became the single source of truth. The frontend API client (`api.ts`) was updated to parse both the `event:` line (for type) and `data:` line (for payload) from the raw SSE stream, then the page component dispatches to the correct state update handler.

### 3. PDF Generation on Different OS

**Problem**: WeasyPrint requires system libraries (Pango, Cairo, GDK-Pixbuf) that differ between macOS, Linux, and Windows. Running `pip install weasyprint` alone fails on clean systems. On Windows, the situation is even more complex.

**Solution**: The `Dockerfile` explicitly installs all required system dependencies (`libpango`, `libpangocairo`, `libgdk-pixbuf`, `libffi`, `libcairo`). For local development without Docker, the README recommends using the Docker Compose setup. WeasyPrint errors are caught gracefully — the report is always available as Markdown even if PDF generation fails.

### 4. Token Cost Management

**Problem**: Each research task involves multiple Claude API calls (decomposition + N× summarization + synthesis). Without careful prompt design, token usage could spiral — especially when feeding full web page content to Claude.

**Solution**:
- Content is truncated to 5000 chars before being sent to Claude
- Search results are capped at 5 per subtopic, only top 3 are deep-fetched
- Depth levels (`quick`/`standard`/`deep`) control subtopic count
- Claude's `max_tokens` is set to 4096 for summaries, preventing runaway generation
- Average cost per standard research: ~$0.03-0.08

### 5. Parallel Research Tasks Error Isolation

**Problem**: When 5 research tasks run in parallel via `asyncio.gather()`, one failing task could crash the entire pipeline. Early versions had no error isolation — a single 403 from a website would discard all other valid results.

**Solution**: Used `asyncio.gather(..., return_exceptions=True)` so exceptions are captured rather than raised. Each task failure is logged individually and surfaced as a `task_complete` event with `status: "failed"`. The synthesizer gracefully handles partial results — even if only 2 of 5 tasks succeed, it produces a useful report from available data.

## 🔮 Future Roadmap

- [ ] Support for additional LLMs (OpenAI, Gemini, local models)
- [ ] Academic paper search (arXiv, Google Scholar integration)
- [ ] Collaborative research sessions
- [ ] Custom report templates
- [ ] Scheduled recurring research
- [ ] Voice input support
- [ ] Browser extension for research-on-the-go
- [ ] RAG-based knowledge base with vector search (Pinecone/Chroma)

## 📚 Related Blog Posts

- [我是如何做一个 AI Research Agent 的](docs/blog-post.md)
- [我是如何做一个 RAG 知识库系统的](docs/blog-rag.md)
- [我是如何用 AI 自动化内容生产流程的](docs/blog-automation.md)

## 📄 License

MIT © 2026 — See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Built with ❤️ using DeepSeek, FastAPI, Next.js, and Tavily</b>
</p>
