import asyncio
import json
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from config import config
from models.schemas import ResearchReport, ResearchTask, SSEEvent
from agents.task_decomposer import TaskDecomposer
from agents.researcher import Researcher
from agents.synthesizer import Synthesizer
from tools.report_generator import generate_markdown, markdown_to_pdf, markdown_to_pptx
from utils.logger import logger


REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class Orchestrator:
    """
    Manages the full research pipeline from topic to published report.

    Coordinates task decomposition, parallel research, synthesis, and file
    generation. Yields SSE events at every stage so the frontend can display
    real-time progress.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the orchestrator and all sub-agents/tools.

        Args:
            api_key: DeepSeek API key. Falls back to config.
            model: Model to use. Falls back to config.MODEL.
        """
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.MODEL
        self.decomposer = TaskDecomposer(api_key=self.api_key, model=self.model)
        self.researcher = Researcher(api_key=self.api_key, model=self.model)
        self.synthesizer = Synthesizer(api_key=self.api_key, model=self.model)
        logger.info(f"Orchestrator initialized with model={self.model}")

    async def run_research(
        self,
        topic: str,
        depth: str = "standard",
    ) -> AsyncGenerator[dict, None]:
        """
        Run the complete research pipeline, yielding SSE events at each stage.

        This is an async generator that produces dicts with 'event' and 'data'
        keys, compatible with sse-starlette's EventSourceResponse.

        Pipeline stages:
        1. Decompose topic into subtopics
        2. Research each subtopic (parallelized)
        3. Synthesize findings into a report
        4. Generate PDF and PPTX files
        5. Optionally save to Supabase

        Args:
            topic: The research topic.
            depth: Research depth — "quick", "standard", or "deep".

        Yields:
            Dicts with 'event' and 'data' keys for SSE streaming.
        """
        report_id = str(uuid.uuid4())
        report = ResearchReport(
            id=report_id,
            topic=topic,
            depth=depth,
            status="in_progress",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            # ── Stage 1: Decomposition ──
            yield {
                "event": "decomposing",
                "data": json.dumps({
                    "message": f"Decomposing research topic into subtopics ({depth} depth)...",
                    "report_id": report_id,
                    "topic": topic,
                }),
            }

            subtopics = await asyncio.to_thread(
                self.decomposer.decompose, topic, depth
            )

            if not subtopics:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "Failed to decompose topic into subtopics.",
                        "report_id": report_id,
                    }),
                }
                report.status = "failed"
                return

            report.subtopics = subtopics

            yield {
                "event": "decomposed",
                "data": json.dumps({
                    "message": f"Topic broken into {len(subtopics)} subtopics.",
                    "subtopics": subtopics,
                    "report_id": report_id,
                }),
            }

            # ── Stage 2: Research (parallel) ──
            tasks: list[ResearchTask] = []

            # Yield "researching" events for each subtopic
            for i, subtopic in enumerate(subtopics):
                yield {
                    "event": "researching",
                    "data": json.dumps({
                        "message": f"Researching subtopic ({i + 1}/{len(subtopics)}): {subtopic[:100]}",
                        "subtopic": subtopic,
                        "index": i,
                        "total": len(subtopics),
                        "report_id": report_id,
                    }),
                }

            # Run all research tasks in parallel
            async def run_research_task(subtopic: str) -> ResearchTask:
                return await asyncio.to_thread(self.researcher.research, subtopic)

            research_coros = [run_research_task(st) for st in subtopics]
            tasks = await asyncio.gather(*research_coros, return_exceptions=True)

            # Process results
            resolved_tasks: list[ResearchTask] = []
            for i, (subtopic, result) in enumerate(zip(subtopics, tasks)):
                if isinstance(result, Exception):
                    logger.error(f"Research failed for '{subtopic[:80]}': {result}")
                    failed_task = ResearchTask(
                        id=str(uuid.uuid4()),
                        subtopic=subtopic,
                        summary=f"Research error: {str(result)}",
                        status="failed",
                    )
                    resolved_tasks.append(failed_task)
                    yield {
                        "event": "task_complete",
                        "data": json.dumps({
                            "message": f"Research failed for: {subtopic[:100]}",
                            "subtopic": subtopic,
                            "task_id": failed_task.id,
                            "status": "failed",
                            "index": i,
                            "total": len(subtopics),
                            "report_id": report_id,
                        }),
                    }
                else:
                    resolved_tasks.append(result)
                    yield {
                        "event": "task_complete",
                        "data": json.dumps({
                            "message": f"Completed research for: {subtopic[:100]}",
                            "subtopic": subtopic,
                            "task_id": result.id,
                            "status": result.status,
                            "index": i,
                            "total": len(subtopics),
                            "report_id": report_id,
                        }),
                    }

            report.tasks = resolved_tasks

            # ── Stage 3: Synthesis ──
            yield {
                "event": "synthesizing",
                "data": json.dumps({
                    "message": "Synthesizing all findings into a comprehensive report...",
                    "report_id": report_id,
                }),
            }

            succeeded = [t for t in resolved_tasks if t.status == "complete"]
            if not succeeded:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "All research tasks failed. Cannot synthesize report.",
                        "report_id": report_id,
                    }),
                }
                report.status = "failed"
                return

            markdown_content = await asyncio.to_thread(
                self.synthesizer.synthesize, topic, succeeded
            )

            report.markdown_content = markdown_content

            # ── Stage 4: Generate files ──
            yield {
                "event": "generating_files",
                "data": json.dumps({
                    "message": "Generating PDF and PowerPoint files...",
                    "report_id": report_id,
                }),
            }

            # Ensure reports directory exists
            report_dir = REPORTS_DIR / report_id
            report_dir.mkdir(parents=True, exist_ok=True)

            # Use the report generator to produce final markdown
            final_markdown = generate_markdown(report)
            report.markdown_content = final_markdown

            # Persist markdown + metadata locally (history / get_report without Supabase)
            md_path = report_dir / "report.md"
            md_path.write_text(final_markdown, encoding="utf-8")
            meta_path = report_dir / "meta.json"
            meta_path.write_text(
                json.dumps(
                    {
                        "id": report_id,
                        "topic": topic,
                        "subtopics": report.subtopics,
                        "markdown_content": final_markdown,
                        "depth": depth,
                        "status": "complete",
                        "created_at": report.created_at,
                        "tasks": [t.model_dump() for t in resolved_tasks],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Generate PDF
            pdf_path = str(report_dir / "report.pdf")
            pdf_result = await asyncio.to_thread(
                markdown_to_pdf, final_markdown, pdf_path
            )

            # Generate PPTX
            pptx_path = str(report_dir / "report.pptx")
            pptx_result = await asyncio.to_thread(
                markdown_to_pptx, final_markdown, pptx_path
            )

            # ── Stage 5: Save to Supabase (if configured) ──
            pdf_url = ""
            pptx_url = ""
            if config.SUPABASE_URL and config.SUPABASE_ANON_KEY:
                try:
                    yield {
                        "event": "saving",
                        "data": json.dumps({
                            "message": "Saving report to database...",
                            "report_id": report_id,
                        }),
                    }
                    pdf_url, pptx_url = await asyncio.to_thread(
                        self._save_to_supabase, report, pdf_path, pptx_path
                    )
                except Exception as e:
                    logger.warning(f"Supabase save failed (non-fatal): {e}")

            # ── Stage 6: Complete ──
            report.status = "complete"

            yield {
                "event": "complete",
                "data": json.dumps({
                    "message": "Research report complete!",
                    "report_id": report_id,
                    "topic": topic,
                    "subtopics": report.subtopics,
                    "markdown_content": final_markdown,
                    "pdf_available": bool(pdf_result),
                    "pptx_available": bool(pptx_result),
                    "pdf_url": pdf_url,
                    "pptx_url": pptx_url,
                    "tasks": [
                        {
                            "id": t.id,
                            "subtopic": t.subtopic,
                            "status": t.status,
                            "source_count": len(t.sources),
                        }
                        for t in resolved_tasks
                    ],
                    "created_at": report.created_at,
                }),
            }

        except Exception as e:
            logger.error(f"Pipeline error during research: {e}")
            report.status = "failed"
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": f"Research pipeline error: {str(e)}",
                    "report_id": report_id,
                }),
            }

    def _save_to_supabase(
        self,
        report: ResearchReport,
        pdf_path: str,
        pptx_path: str,
    ) -> tuple[str, str]:
        """
        Persist the report and its files to Supabase.

        Stores report metadata in the 'reports' table and uploads PDF/PPTX
        files to Supabase Storage.

        Args:
            report: The completed ResearchReport.
            pdf_path: Local path to the generated PDF.
            pptx_path: Local path to the generated PPTX.

        Returns:
            Tuple of (pdf_public_url, pptx_public_url). Empty strings if upload fails.
        """
        try:
            from supabase import create_client, Client

            supabase: Client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY,
            )

            # Insert report record
            report_data = {
                "id": report.id,
                "topic": report.topic,
                "subtopics": report.subtopics,
                "markdown_content": report.markdown_content,
                "depth": report.depth,
                "status": report.status,
                "created_at": report.created_at,
                "tasks": [t.model_dump() for t in report.tasks],
            }

            supabase.table("research_reports").upsert(report_data).execute()
            logger.info(f"Report {report.id} saved to Supabase")

            # Upload PDF
            pdf_url = ""
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                supabase.storage.from_("reports").upload(
                    path=f"{report.id}/report.pdf",
                    file=pdf_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"},
                )
                pdf_url = supabase.storage.from_("reports").get_public_url(
                    f"{report.id}/report.pdf"
                )
                logger.info(f"PDF uploaded for report {report.id}")

            # Upload PPTX
            pptx_url = ""
            if os.path.exists(pptx_path):
                with open(pptx_path, "rb") as f:
                    pptx_bytes = f.read()
                supabase.storage.from_("reports").upload(
                    path=f"{report.id}/report.pptx",
                    file=pptx_bytes,
                    file_options={
                        "content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "upsert": "true",
                    },
                )
                pptx_url = supabase.storage.from_("reports").get_public_url(
                    f"{report.id}/report.pptx"
                )
                logger.info(f"PPTX uploaded for report {report.id}")

            return (pdf_url, pptx_url)

        except ImportError:
            logger.warning("Supabase SDK not available; skipping persistence")
            return ("", "")
        except Exception as e:
            logger.error(f"Supabase save error: {e}")
            return ("", "")
