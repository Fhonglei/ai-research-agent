import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import config
from models.schemas import ResearchRequest
from agents.orchestrator import Orchestrator
from utils.logger import logger

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Research Agent API",
    version="1.0.0",
    description="Backend API for the AI Research Agent — automated research, synthesis, and report generation.",
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure reports directory exists
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Dependencies / shared instances
# ---------------------------------------------------------------------------
orchestrator = Orchestrator()


def _get_supabase_client():
    """Get a Supabase client if configured, else None."""
    if not config.supabase_configured:
        return None
    try:
        from supabase import create_client
        return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
    except ImportError:
        logger.warning("Supabase SDK not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    provider = config.LLM_PROVIDER.lower()
    llm_ok = config.llm_configured
    status = "healthy" if llm_ok else "degraded"
    return {
        "status": status,
        "version": "1.1.0",
        "provider": provider,
        "model": config.active_model,
        "llm_configured": llm_ok,
        "tavily_configured": config.tavily_configured,
        "supabase_configured": config.supabase_configured,
    }


@app.post("/api/research")
async def start_research(request: ResearchRequest):
    """
    Start a new research project.

    Accepts a topic and optional depth, then streams progress events via
    Server-Sent Events (SSE) as the pipeline runs through decomposition,
    research, synthesis, and file generation stages.

    Returns an EventSourceResponse stream.
    """
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Research topic is required.")

    valid_depths = ("quick", "standard", "deep")
    if request.depth not in valid_depths:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid depth '{request.depth}'. Must be one of: {', '.join(valid_depths)}",
        )

    logger.info(f"Research requested: topic='{request.topic[:100]}', depth={request.depth}")

    async def event_generator():
        try:
            async for event in orchestrator.run_research(
                topic=request.topic.strip(),
                depth=request.depth,
            ):
                # event is a dict with "event" and "data" keys
                yield event
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": f"Internal server error: {str(e)}",
                }),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    """
    Get a research report by ID.

    Tries Supabase first (if configured), then falls back to local filesystem.
    """
    # Try Supabase first
    client = _get_supabase_client()
    if client:
        try:
            response = client.table("research_reports").select("*").eq("id", report_id).execute()
            if response.data:
                return JSONResponse(content=response.data[0])
        except Exception as e:
            logger.warning(f"Supabase fetch failed for report {report_id}: {e}")

    # Fallback: check local filesystem
    report_dir = REPORTS_DIR / report_id
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    meta_file = report_dir / "meta.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["pdf_available"] = (report_dir / "report.pdf").exists()
            metadata["pptx_available"] = (report_dir / "report.pptx").exists()
            return JSONResponse(content=metadata)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read meta.json for {report_id}: {e}")

    md_file = report_dir / "report.md"
    if md_file.exists():
        with open(md_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        return JSONResponse(content={
            "id": report_id,
            "topic": report_id,
            "subtopics": [],
            "tasks": [],
            "markdown_content": markdown_content,
            "status": "complete",
            "created_at": datetime.fromtimestamp(
                md_file.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
        })

    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")


@app.get("/api/report/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query(default="pdf", description="File format: pdf or pptx"),
):
    """
    Download a report file (PDF or PPTX).

    Tries Supabase Storage first, then local filesystem.
    """
    if format not in ("pdf", "pptx"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'pptx'.")

    filename = f"report.{format}"
    content_type = (
        "application/pdf"
        if format == "pdf"
        else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    # Check local filesystem first (fastest path)
    local_path = REPORTS_DIR / report_id / filename
    if local_path.exists():
        return FileResponse(
            path=str(local_path),
            media_type=content_type,
            filename=f"research_report.{format}",
        )

    # Try Supabase Storage
    client = _get_supabase_client()
    if client:
        try:
            from fastapi.responses import Response

            data = client.storage.from_("reports").download(f"{report_id}/{filename}")
            file_bytes = data if isinstance(data, (bytes, bytearray)) else bytes(data)
            return Response(
                content=file_bytes,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="research_report.{format}"',
                },
            )
        except Exception as e:
            logger.warning(f"Supabase download failed: {e}")

    raise HTTPException(
        status_code=404,
        detail=f"Report file '{filename}' not found for report '{report_id}'.",
    )


@app.get("/api/history")
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List all past research reports, most recent first.

    Returns from Supabase if configured, otherwise scans local filesystem.
    """
    # Try Supabase first
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
            return JSONResponse(content={
                "reports": response.data,
                "total": len(response.data),
                "limit": limit,
                "offset": offset,
            })
        except Exception as e:
            logger.warning(f"Supabase history fetch failed: {e}")

    # Fallback: scan local filesystem
    reports = []
    if REPORTS_DIR.exists():
        for entry in sorted(REPORTS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
            if not entry.is_dir():
                continue
            meta_file = entry / "meta.json"
            if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["pdf_available"] = (entry / "report.pdf").exists()
            metadata["pptx_available"] = (entry / "report.pptx").exists()
            reports.append(metadata)
            continue
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Invalid meta.json for {entry.name}: {e}")
            md_file = entry / "report.md"
            reports.append({
                "id": entry.name,
                "topic": entry.name,
                "subtopics": [],
                "markdown_content": "",
                "tasks": [],
                "status": "complete" if md_file.exists() else "unknown",
                "created_at": datetime.fromtimestamp(
                    entry.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })

    paginated = reports[offset:offset + limit]
    return JSONResponse(content={
        "reports": paginated,
        "total": len(reports),
        "limit": limit,
        "offset": offset,
    })


@app.get("/api/report/{report_id}/markdown")
async def get_report_markdown(report_id: str):
    """
    Get just the raw markdown content for a report.
    """
    # Try Supabase first
    client = _get_supabase_client()
    if client:
        try:
            response = client.table("research_reports").select("markdown_content, id").eq("id", report_id).execute()
            if response.data and response.data[0].get("markdown_content"):
                return JSONResponse(content={
                    "id": report_id,
                    "markdown_content": response.data[0]["markdown_content"],
                })
        except Exception as e:
            logger.warning(f"Supabase markdown fetch failed: {e}")

    # Fallback to local files
    md_file = REPORTS_DIR / report_id / "report.md"
    if md_file.exists():
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        return JSONResponse(content={"id": report_id, "markdown_content": content})

    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("AI Research Agent Backend starting up")
    logger.info(f"Model: {config.MODEL}")
    logger.info(f"Host: {config.BACKEND_HOST}:{config.BACKEND_PORT}")
    logger.info(f"Supabase: {'Configured' if config.supabase_configured else 'Not configured'}")
    logger.info(f"Reports directory: {REPORTS_DIR.absolute()}")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        reload=True,
        log_level="info",
    )
