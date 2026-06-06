from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime, timezone


class ResearchRequest(BaseModel):
    """Incoming research request from the frontend."""
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The research topic to investigate",
    )
    depth: Literal["quick", "standard", "deep"] = Field(
        default="standard",
        description="Research depth: 'quick', 'standard', or 'deep'"
    )

    @field_validator("topic")
    @classmethod
    def topic_must_be_clear(cls, value: str) -> str:
        topic = " ".join(value.strip().split())
        if len(topic) < 3:
            raise ValueError("Research topic must contain at least 3 characters.")
        return topic


class Source(BaseModel):
    """A single source used in research."""
    url: str = Field(default="", description="Source URL")
    title: str = Field(default="", description="Source title")
    snippet: str = Field(default="", description="Short description or snippet")
    content: str = Field(default="", description="Full fetched content (truncated)")


class ResearchTask(BaseModel):
    """An individual research task for a subtopic."""
    id: str = Field(default="", description="Unique task identifier")
    subtopic: str = Field(default="", description="The subtopic being researched")
    summary: str = Field(default="", description="Research summary for this subtopic")
    sources: list[Source] = Field(default_factory=list, description="Sources used")
    status: str = Field(default="pending", description="Task status: pending, in_progress, complete, failed")


class ResearchQuality(BaseModel):
    """Quality signals for an AI-generated research report."""
    source_count: int = Field(default=0, description="Total collected sources")
    unique_domain_count: int = Field(default=0, description="Number of unique source domains")
    citation_count: int = Field(default=0, description="Inline citation markers found in summaries/report")
    citation_coverage: float = Field(default=0.0, description="Share of completed tasks with citations")
    success_rate: float = Field(default=0.0, description="Share of research tracks completed successfully")
    confidence_score: float = Field(default=0.0, description="0-100 heuristic quality score")
    warnings: list[str] = Field(default_factory=list, description="Quality issues to review")


class ResearchReport(BaseModel):
    """The final compiled research report."""
    id: str = Field(default="", description="Unique report identifier")
    topic: str = Field(default="", description="Original research topic")
    subtopics: list[str] = Field(default_factory=list, description="List of subtopics investigated")
    markdown_content: str = Field(default="", description="Full markdown report content")
    tasks: list[ResearchTask] = Field(default_factory=list, description="All research tasks")
    quality: ResearchQuality | None = Field(default=None, description="Research quality metrics")
    depth: str = Field(default="standard", description="Research depth: quick, standard, or deep")
    status: str = Field(default="pending", description="Report status: pending, in_progress, complete, failed")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 creation timestamp"
    )


class SSEEvent(BaseModel):
    """Server-Sent Event structure."""
    type: str = Field(..., description="Event type identifier")
    message: str = Field(default="", description="Human-readable message")
    data: dict = Field(default_factory=dict, description="Event payload data")
