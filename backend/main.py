import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

from agents.orchestrator import Orchestrator
from config import config
from models.schemas import ResearchRequest
from utils.logger import logger


app = FastAPI(
    title="AI Research Agent API",
    version="1.2.0",
    description="Automated research, source collection, synthesis, and report generation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin_list or ["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = Path(config.REPORTS_DIR)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

orchestrator = Orchestrator()


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


@app.get("/")
async def root():
    return {
        "service": "ai-research-agent",
        "status_url": "/api/health",
        "docs_url": "/docs",
    }


@app.get("/api/health")
async def health_check():
    provider = config.LLM_PROVIDER.lower()
    llm_ok = config.llm_configured
    return {
        "status": "healthy" if llm_ok else "degraded",
        "version": "1.2.0",
        "provider": provider,
        "model": config.active_model,
        "llm_configured": llm_ok,
        "tavily_configured": config.tavily_configured,
        "supabase_configured": config.supabase_configured,
        "limits": {
            "max_topic_length": config.MAX_TOPIC_LENGTH,
            "search_max_results": config.SEARCH_MAX_RESULTS,
            "fetch_top_n": config.FETCH_TOP_N,
            "max_parallel_research_tasks": config.MAX_PARALLEL_RESEARCH_TASKS,
        },
    }


@app.post("/api/research")
async def start_research(request: ResearchRequest):
    topic = request.topic.strip()
    if len(topic) > config.MAX_TOPIC_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Research topic exceeds {config.MAX_TOPIC_LENGTH} characters.",
        )

    logger.info("Research requested: topic='%s', depth=%s", topic[:100], request.depth)

    async def event_generator():
        try:
            async for event in orchestrator.run_research(topic=topic, depth=request.depth):
                yield event
        except Exception as exc:
            logger.error("SSE stream error: %s", exc)
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Internal server error: {exc}"}),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    supabase_report = _get_supabase_report(report_id)
    if supabase_report:
        return JSONResponse(content=supabase_report)

    local_report = _read_local_report(report_id)
    if local_report:
        return JSONResponse(content=local_report)

    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")


@app.get("/api/report/{report_id}/quality")
async def get_report_quality(report_id: str):
    report = _get_supabase_report(report_id) or _read_local_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return JSONResponse(content=report.get("quality") or {})


@app.get("/api/report/{report_id}/markdown")
async def get_report_markdown(report_id: str):
    supabase_report = _get_supabase_report(report_id)
    if supabase_report and supabase_report.get("markdown_content"):
        return JSONResponse(
            content={
                "id": report_id,
                "markdown_content": supabase_report["markdown_content"],
            }
        )

    md_file = REPORTS_DIR / report_id / "report.md"
    if md_file.exists():
        return JSONResponse(
            content={
                "id": report_id,
                "markdown_content": md_file.read_text(encoding="utf-8"),
            }
        )

    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")


@app.get("/api/report/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query(default="pdf", description="File format: pdf or pptx"),
):
    if format not in ("pdf", "pptx"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'pptx'.")

    filename = f"report.{format}"
    content_type = (
        "application/pdf"
        if format == "pdf"
        else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    local_path = REPORTS_DIR / report_id / filename
    if local_path.exists():
        return FileResponse(
            path=str(local_path),
            media_type=content_type,
            filename=f"research_report.{format}",
        )

    client = _get_supabase_client()
    if client:
        try:
            data = client.storage.from_("reports").download(f"{report_id}/{filename}")
            file_bytes = data if isinstance(data, (bytes, bytearray)) else bytes(data)
            return Response(
                content=file_bytes,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="research_report.{format}"',
                },
            )
        except Exception as exc:
            logger.warning("Supabase download failed for %s: %s", report_id, exc)

    raise HTTPException(
        status_code=404,
        detail=f"Report file '{filename}' not found for report '{report_id}'.",
    )


@app.get("/api/history")
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    client = _get_supabase_client()
    if client:
        try:
            response = (
                client.table("research_reports")
                .select("*")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return JSONResponse(
                content={
                    "reports": response.data,
                    "total": len(response.data),
                    "limit": limit,
                    "offset": offset,
                }
            )
        except Exception as exc:
            logger.warning("Supabase history fetch failed: %s", exc)

    reports = _list_local_reports()
    paginated = reports[offset:offset + limit]
    return JSONResponse(
        content={
            "reports": paginated,
            "total": len(reports),
            "limit": limit,
            "offset": offset,
        }
    )


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("AI Research Agent Backend starting up")
    logger.info("Model: %s", config.active_model)
    logger.info("Host: %s:%s", config.BACKEND_HOST, config.BACKEND_PORT)
    logger.info("Supabase: %s", "Configured" if config.supabase_configured else "Not configured")
    logger.info("Reports directory: %s", REPORTS_DIR.absolute())
    logger.info("=" * 60)


def _get_supabase_client():
    if not config.supabase_configured:
        return None
    try:
        from supabase import create_client

        supabase_url = config.SUPABASE_URL
        supabase_key = config.SUPABASE_ANON_KEY
        if not supabase_url or not supabase_key:
            return None
        return create_client(supabase_url, supabase_key)
    except ImportError:
        logger.warning("Supabase SDK not installed")
        return None
    except Exception as exc:
        logger.error("Failed to create Supabase client: %s", exc)
        return None


def _get_supabase_report(report_id: str) -> dict[str, Any] | None:
    client = _get_supabase_client()
    if not client:
        return None
    try:
        response = client.table("research_reports").select("*").eq("id", report_id).execute()
        return response.data[0] if response.data else None
    except Exception as exc:
        logger.warning("Supabase fetch failed for report %s: %s", report_id, exc)
        return None


def _read_local_report(report_id: str) -> dict[str, Any] | None:
    report_dir = REPORTS_DIR / report_id
    if not report_dir.exists() or not report_dir.is_dir():
        return None

    meta_file = report_dir / "meta.json"
    if meta_file.exists():
        try:
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
            metadata["pdf_available"] = (report_dir / "report.pdf").exists()
            metadata["pptx_available"] = (report_dir / "report.pptx").exists()
            return metadata
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Invalid meta.json for %s: %s", report_id, exc)

    md_file = report_dir / "report.md"
    if md_file.exists():
        return {
            "id": report_id,
            "topic": report_id,
            "subtopics": [],
            "tasks": [],
            "quality": None,
            "markdown_content": md_file.read_text(encoding="utf-8"),
            "status": "complete",
            "created_at": datetime.fromtimestamp(
                md_file.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat(),
            "pdf_available": (report_dir / "report.pdf").exists(),
            "pptx_available": (report_dir / "report.pptx").exists(),
        }

    return None


def _list_local_reports() -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    if not REPORTS_DIR.exists():
        return reports

    entries = [entry for entry in REPORTS_DIR.iterdir() if entry.is_dir()]
    entries.sort(key=os.path.getmtime, reverse=True)

    for entry in entries:
        report = _read_local_report(entry.name)
        if report:
            reports.append(report)

    return reports


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        reload=True,
        log_level="info",
    )
