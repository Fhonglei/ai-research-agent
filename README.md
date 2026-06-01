# 🔬 AI Research Agent

> AI-powered automated research — enter a topic, get a comprehensive report in minutes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)

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
│  │ Orchestrator│  │Researcher│  │ Report Generator │  │
│  └─────┬────┘  └────┬─────┘  └────────┬─────────┘  │
│        │             │                  │             │
│  ┌─────▼────┐  ┌────▼─────┐  ┌────────▼─────────┐  │
│  │Decomposer│  │SearchTool│  │ MD/PDF/PPTX Gen  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
         │              │                 │
    ┌────▼────┐   ┌────▼────┐    ┌───────▼──────┐
    │ Claude   │   │ Tavily   │    │  Supabase    │
    │ (LLM)    │   │ (Search) │    │  (Storage)   │
    └─────────┘   └─────────┘    └──────────────┘
```

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Frontend** | Next.js 14, Tailwind CSS, shadcn/ui | React UI with SSR |
| **Backend** | FastAPI, Python 3.12 | Async REST API |
| **AI/LLM** | Claude API (Anthropic SDK) | Agent reasoning & summarization |
| **Search** | Tavily Search API | Real-time web search |
| **Database** | Supabase (PostgreSQL) | Report persistence & history |
| **Report Gen** | WeasyPrint, python-pptx | PDF & PowerPoint export |
| **Streaming** | SSE (Server-Sent Events) | Real-time progress updates |
| **Deployment** | Vercel + Railway + Docker | Production hosting |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- API keys for [Anthropic](https://console.anthropic.com/), [Tavily](https://app.tavily.com/), and [Supabase](https://app.supabase.com/)

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/ai-research-agent.git
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

## 📡 API Reference

### `POST /api/research`

Start a new research task. Returns SSE stream.

```json
// Request
{ "topic": "AI internship market 2026", "depth": "standard" }

// SSE Events
event: progress
data: {"type": "decomposing", "message": "Analyzing research topic..."}

event: progress
data: {"type": "researching", "task": "Industry Trends", "progress": 2}

event: complete
data: {"type": "complete", "report_id": "abc-123", "report": {...}}
```

### `GET /api/report/{report_id}`

Retrieve a completed research report.

### `GET /api/report/{report_id}/download?format=pdf`

Download report as PDF or PPTX (`format=pdf|pptx`).

### `GET /api/history`

List all past research reports.

| Depth | Subtopic Count | Description |
|-------|---------------|-------------|
| `quick` | 2-3 | Brief overview for quick answers |
| `standard` | 4-5 | Balanced depth (default) |
| `deep` | 6-8 | Exhaustive research with more sources |

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
│   └── DEPLOYMENT.md
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

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ANTHROPIC_API_KEY not set` | Add your key to `.env` |
| `TAVILY_API_KEY not set` | Get a free key at [tavily.com](https://tavily.com) |
| PDF generation fails | Ensure system dependencies installed (see Dockerfile) |
| Search returns no results | Check Tavily API quota |
| Frontend can't reach backend | Verify `NEXT_PUBLIC_API_URL` in `.env` |

## 🔮 Future Roadmap

- [ ] Support for additional LLMs (OpenAI, Gemini, local models)
- [ ] Academic paper search (arXiv, Google Scholar integration)
- [ ] Collaborative research sessions
- [ ] Custom report templates
- [ ] Scheduled recurring research
- [ ] Voice input support
- [ ] Browser extension for research-on-the-go

## 📄 License

MIT © 2026 — See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Built with ❤️ using Claude, FastAPI, Next.js, and Tavily</b>
</p>
