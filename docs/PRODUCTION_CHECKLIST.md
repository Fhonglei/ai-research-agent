# Production Checklist

This checklist tracks what is already implemented and what still requires real credentials, domains, or storage infrastructure.

## Done

- Frontend deployed on Vercel.
- Backend deployed on Railway.
- Railway backend health endpoint.
- Dockerfile and Railway config for backend deployment.
- Docker Compose local startup.
- SSE streaming progress for long-running research.
- Multi-step agent pipeline: decomposition, search, fetch, summarize, synthesize, export.
- Report quality metrics: source count, citation coverage, domain diversity, success rate, confidence score.
- Frontend quality panel on completed reports.
- SSRF-aware content fetching for local/private host rejection.
- Configurable search size, fetch size, topic length, and concurrency limits.
- Backend pytest coverage for parsing, mocked search, report generation, and quality scoring.
- Frontend lint/typecheck/build checks.
- GitHub Actions CI for backend and frontend checks.
- README with online demo links, architecture overview, and setup instructions.
- Technical notes in `docs/TECHNICAL_NOTES.md`.
- Set `DEEPSEEK_API_KEY` on Railway.
- Set `TAVILY_API_KEY` on Railway.
- Confirm health check returns:
  - `"llm_configured": true`
  - `"tavily_configured": true`

## Required Before Public Demo

- Run one quick research task end to end.
- Record a GIF or short video using `docs/DEMO_SCRIPT.md`.
- Add the screenshot/GIF to README.

## Strong Next Steps

- Connect Vercel and Railway directly to GitHub for automatic deployments.
- Add Supabase persistence for report history.
- Add Supabase Storage, S3, or Cloudflare R2 for generated PDF/PPTX files.
- Add user login and per-user report isolation.
- Add a queue worker for deep research jobs.
- Add rate limits to prevent API abuse and cost spikes.
- Add Sentry or another error monitoring tool.
- Add a custom domain.

## Project Summary

Accurate:

> Built and deployed a full-stack AI research agent that decomposes topics, searches live web sources, extracts source content, synthesizes cited reports, streams task progress with SSE, exports Markdown/PDF/PPTX, and evaluates report quality.

Avoid overstating:

> Fully autonomous production research platform.

Better wording:

> Deployed AI research automation prototype with production-oriented quality metrics and clear hardening roadmap.
