# Demo Script

Use this script to record a 60-90 second product demo.

## Demo URLs

- Frontend: https://ai-research-agent-frontend.vercel.app
- Backend health: https://ai-research-agent-api-production.up.railway.app/api/health

## Before Recording

1. Configure `DEEPSEEK_API_KEY` on Railway.
2. Configure `TAVILY_API_KEY` on Railway for better search quality.
3. Confirm `/api/health` returns `"llm_configured": true`.
4. Open the frontend in a fresh browser tab.

## Suggested Research Topics

Use one of these topics:

- `Competitive analysis of AI research assistant products`
- `How small teams can evaluate RAG system quality`
- `Market analysis of AI document automation tools`

Use `quick` depth for a short demo.

## Recording Flow

1. Open the frontend.
2. Enter the topic.
3. Select `Quick`.
4. Start research.
5. Show live progress: decomposition, searching, synthesis, export.
6. Open the final report tab.
7. Show the quality panel: Quality, Sources, Citations, Success.
8. Open the sources tab to show source-backed research.
9. Download Markdown; optionally show PDF/PPTX if generated.
10. Open the backend health URL in another tab.

## Architecture Summary

This is not a simple prompt-to-answer app. It is a multi-step research pipeline: task decomposition, web search, content extraction, per-track summarization, final synthesis, export generation, and quality evaluation. The frontend uses SSE to show long-running task progress in real time.

## Known Production Gaps

- Requires real LLM/search API keys for full demo quality.
- Local report files on Railway can be lost after redeploy unless Supabase or object storage is configured.
- Long-running deep research should eventually move to a queue-based worker.
