# 📡 API Reference

Base URL: `http://localhost:8000`

## Endpoints

### `POST /api/research`

Start a new research task. Returns an **SSE stream** of progress events.

**Request Body:**

```json
{
  "topic": "Research the AI internship market in 2026",
  "depth": "standard"
}
```

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| `topic` | string | ✅ | any | The research topic or question |
| `depth` | string | ❌ | `quick`, `standard`, `deep` | Research depth (default: `standard`) |

**Response:** `text/event-stream` (SSE)

**SSE Event Types:**

| Type | When | Data Payload |
|------|------|-------------|
| `decomposing` | Starting topic analysis | `{"message": "Analyzing..."}` |
| `decomposed` | Subtopics identified | `{"subtopics": ["...", "..."]}` |
| `researching` | Starting a subtopic | `{"task": "Subtopic name", "progress": 1, "total": 5}` |
| `task_complete` | Subtopic finished | `{"task": {ResearchTask}}` |
| `synthesizing` | Combining results | `{"message": "Generating report..."}` |
| `complete` | Report ready | `{"report_id": "uuid", "report": {ResearchReport}}` |
| `error` | Error occurred | `{"message": "Error description"}` |

**Example (curl):**

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI trends 2026", "depth": "standard"}' \
  --no-buffer
```

**Example (JavaScript fetch with SSE parsing):**

```typescript
const response = await fetch('http://localhost:8000/api/research', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic: 'AI trends 2026', depth: 'standard' })
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      console.log(event.type, event.message);
    }
  }
}
```

---

### `GET /api/report/{report_id}`

Retrieve a completed research report by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_id` | UUID | The report ID returned by the research endpoint |

**Response:**

```json
{
  "id": "abc-123-def-456",
  "topic": "AI internship market 2026",
  "subtopics": ["Industry trends", "Top companies", "Skills required"],
  "markdown_content": "# AI Internship Market 2026\n\n...",
  "tasks": [
    {
      "id": "task-1",
      "subtopic": "Industry trends",
      "summary": "The AI internship market in 2026...",
      "sources": [
        {
          "url": "https://example.com/article",
          "title": "AI Internships Boom in 2026",
          "snippet": "The market has grown 40%..."
        }
      ],
      "status": "complete"
    }
  ],
  "status": "complete",
  "created_at": "2026-06-01T12:00:00Z"
}
```

---

### `GET /api/report/{report_id}/download`

Download report in a specific format.

**Query Parameters:**

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| `format` | string | ✅ | `pdf`, `pptx` | Output format |

**Response:** Binary file download

- `format=pdf` → `application/pdf`
- `format=pptx` → `application/vnd.openxmlformats-officedocument.presentationml.presentation`

**Example:**

```bash
curl -o report.pdf "http://localhost:8000/api/report/abc-123/download?format=pdf"
curl -o report.pptx "http://localhost:8000/api/report/abc-123/download?format=pptx"
```

---

### `GET /api/history`

List all past research reports (most recent first).

**Response:**

```json
[
  {
    "id": "abc-123",
    "topic": "AI internship market 2026",
    "status": "complete",
    "subtopics": ["...", "..."],
    "created_at": "2026-06-01T12:00:00Z"
  },
  {
    "id": "def-456",
    "topic": "Quantum computing applications",
    "status": "complete",
    "subtopics": ["...", "..."],
    "created_at": "2026-05-30T09:30:00Z"
  }
]
```

---

### `GET /api/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-01T12:00:00Z"
}
```

## Data Models

### ResearchReport

```typescript
interface ResearchReport {
  id: string;
  topic: string;
  subtopics: string[];
  markdown_content: string;
  tasks: ResearchTask[];
  status: 'pending' | 'decomposing' | 'researching' | 'synthesizing' | 'complete' | 'error';
  error_message?: string;
  created_at: string;
}
```

### ResearchTask

```typescript
interface ResearchTask {
  id: string;
  subtopic: string;
  summary: string;
  sources: Source[];
  status: 'pending' | 'searching' | 'summarizing' | 'complete' | 'error';
}
```

### Source

```typescript
interface Source {
  url: string;
  title: string;
  snippet: string;
  content?: string;
}
```

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid topic, missing field) |
| 404 | Report not found |
| 500 | Internal server error (check logs) |
| 503 | External API unavailable (Claude/Tavily) |

## Rate Limits

- **Research**: 10 concurrent requests recommended
- **Downloads**: No limit
- **History**: No limit

Heavy usage may be limited by your Claude API and Tavily API rate limits.
