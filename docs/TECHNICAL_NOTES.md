# Technical Notes

This document summarizes the main engineering decisions behind AI Research Agent.

## System Shape

The application is split into a Next.js frontend and a FastAPI backend. The frontend handles topic input, research depth selection, streaming progress display, report rendering, quality metrics, and downloads. The backend owns orchestration, search, content extraction, LLM calls, report generation, storage, and quality evaluation.

The main research flow is:

1. Validate the incoming research request.
2. Decompose the topic into focused research tracks.
3. Search the web with Tavily when configured, with DuckDuckGo fallback.
4. Fetch readable source content while rejecting local and private network targets.
5. Summarize each research track with citations.
6. Synthesize a final markdown report.
7. Generate export artifacts.
8. Evaluate report quality.
9. Persist the report locally or through Supabase when configured.

## Why SSE Is Used

Research jobs can take longer than a normal request-response interaction. Server-Sent Events let the backend stream each stage to the frontend while the job is running, so the UI can show progress without polling or waiting for a single final response.

## Quality Evaluation

The backend computes lightweight quality metrics for each report:

- Source count.
- Unique source domains.
- Citation count.
- Citation coverage.
- Task success rate.
- Confidence score.
- Warnings for thin source coverage or failed research tracks.

These metrics are heuristic, but they make report quality visible and easier to improve.

## Cost And Runtime Controls

The backend exposes configuration for:

- `SEARCH_MAX_RESULTS`: search results per research track.
- `FETCH_TOP_N`: pages fetched per track.
- `MAX_PARALLEL_RESEARCH_TASKS`: concurrent research tracks.
- `CONTENT_FETCH_MAX_CHARS`: extracted content size limit.
- `REQUIRE_LLM_FOR_RESEARCH`: fail early when no LLM key is configured.

These settings keep the system easier to operate across local development, demos, and hosted deployments.

## Production Gaps

The project is ready for demonstration and further hardening, but a production deployment should add:

- Durable object storage for generated PDF and PPTX files.
- User accounts and per-user report isolation.
- Queue-based workers for deep research jobs.
- Rate limiting and API abuse protection.
- Error monitoring and structured observability.
- Stronger citation verification against fetched source text.
