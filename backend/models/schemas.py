from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ResearchRequest(BaseModel):
    """Incoming research request from the frontend."""
    topic: str = Field(..., description="The research topic to investigate")
    depth: str = Field(
        default="standard",
        description="Research depth: 'quick', 'standard', or 'deep'"
    )


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


class ResearchReport(BaseModel):
    """The final compiled research report."""
    id: str = Field(default="", description="Unique report identifier")
    topic: str = Field(default="", description="Original research topic")
    subtopics: list[str] = Field(default_factory=list, description="List of subtopics investigated")
    markdown_content: str = Field(default="", description="Full markdown report content")
    tasks: list[ResearchTask] = Field(default_factory=list, description="All research tasks")
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
