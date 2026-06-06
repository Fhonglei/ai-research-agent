# API Reference

Base URL for local development: `http://localhost:8000`

## GET /api/health

Returns service status and runtime configuration.

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "llm_configured": true,
  "tavily_configured": true,
  "supabase_configured": false,
  "limits": {
    "max_topic_length": 500,
    "search_max_results": 5,
    "fetch_top_n": 3,
    "max_parallel_research_tasks": 4
  }
}
```

## POST /api/research

Starts a research task and returns an SSE stream.

Request:

```json
{
  "topic": "AI internship market in 2026",
  "depth": "standard"
}
```

`depth` must be one of:

| Value | Use case |
| --- | --- |
| `quick` | Fast overview |
| `standard` | Balanced research |
| `deep` | More subtopics and sources |

SSE events:

| Event | Description |
| --- | --- |
| `decomposing` | Topic is being split into research tracks |
| `decomposed` | Subtopics are available |
| `researching` | A subtopic research task has started |
| `task_complete` | A subtopic task completed or failed |
| `synthesizing` | Final report synthesis is running |
| `generating_files` | Markdown/PDF/PPTX files are being generated |
| `saving` | Optional Supabase persistence is running |
| `complete` | Report is ready |
| `error` | The pipeline failed |

Example event:

```text
event: complete
data: {"report_id":"...","topic":"...","markdown_content":"...","quality":{"confidence_score":92.5}}
```

## GET /api/history

Lists reports from Supabase when configured, otherwise from local disk.

Query parameters:

| Name | Default | Description |
| --- | --- | --- |
| `limit` | `20` | 1-100 |
| `offset` | `0` | Pagination offset |

## GET /api/report/{report_id}

Returns report metadata, markdown content, tasks, export availability, and quality metrics.

## GET /api/report/{report_id}/quality

Returns only the quality metrics.

```json
{
  "source_count": 12,
  "unique_domain_count": 8,
  "citation_count": 18,
  "citation_coverage": 0.83,
  "success_rate": 1.0,
  "confidence_score": 91.2,
  "warnings": []
}
```

## GET /api/report/{report_id}/markdown

Returns raw markdown.

```json
{
  "id": "report-id",
  "markdown_content": "# Research Report..."
}
```

## GET /api/report/{report_id}/download

Downloads generated files.

Query parameters:

| Name | Values |
| --- | --- |
| `format` | `pdf` or `pptx` |

Examples:

```bash
curl -o report.pdf "http://localhost:8000/api/report/{report_id}/download?format=pdf"
curl -o report.pptx "http://localhost:8000/api/report/{report_id}/download?format=pptx"
```
