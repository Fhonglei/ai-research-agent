from typing import Optional
from anthropic import Anthropic
from config import config
from models.schemas import ResearchTask
from utils.logger import logger


class Synthesizer:
    """
    Synthesizes individual research task summaries into a cohesive,
    well-structured markdown report using Claude.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the synthesizer.

        Args:
            api_key: Anthropic API key. Falls back to config.
            model: Claude model to use. Falls back to config.MODEL.
        """
        self.client = Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY)
        self.model = model or config.MODEL
        logger.info(f"Synthesizer initialized with model={self.model}")

    def synthesize(self, topic: str, tasks: list[ResearchTask]) -> str:
        """
        Combine all task summaries into a comprehensive markdown report.

        The report includes:
        - Executive Summary
        - Sections for each subtopic
        - Key Takeaways
        - References section

        Args:
            topic: The original research topic.
            tasks: List of completed ResearchTask objects.

        Returns:
            A complete markdown report string.
        """
        if not topic or not topic.strip():
            logger.warning("synthesize called with empty topic")
            return self._empty_report()

        if not tasks:
            logger.warning("synthesize called with no tasks")
            return self._minimal_report(topic)

        # Filter to completed tasks with summaries
        valid_tasks = [t for t in tasks if t.summary and t.status == "complete"]
        failed_tasks = [t for t in tasks if t.status == "failed"]

        if not valid_tasks:
            logger.warning("No completed tasks with summaries to synthesize")
            return self._minimal_report(topic)

        try:
            logger.info(f"Synthesizing report for topic: '{topic[:100]}...' "
                        f"from {len(valid_tasks)} tasks")

            # Build task context for Claude
            task_context = self._build_task_context(valid_tasks)

            prompt = self._build_synthesis_prompt(topic, task_context, failed_tasks)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.6,
                system=(
                    "You are a senior research director at a top-tier research firm. "
                    "Your job is to synthesize individual research summaries into "
                    "a polished, professional research report in markdown format. "
                    "The report should be comprehensive yet readable, with clear "
                    "structure and actionable insights. Write in a confident, "
                    "authoritative voice while remaining objective and data-driven."
                ),
                messages=[{"role": "user", "content": prompt}],
            )

            markdown_report = response.content[0].text.strip()

            # Ensure the report starts with a proper H1 title
            if not markdown_report.startswith("# "):
                markdown_report = f"# Research Report: {topic}\n\n{markdown_report}"

            logger.info(f"Synthesis complete: {len(markdown_report)} characters")
            return markdown_report

        except Exception as e:
            logger.error(f"Synthesis failed for topic '{topic[:80]}...': {e}")
            # Fallback: manually assemble a report
            return self._fallback_synthesize(topic, valid_tasks, failed_tasks)

    def _build_task_context(self, tasks: list[ResearchTask]) -> str:
        """Build a structured context block from task summaries and sources."""
        parts = []
        for i, task in enumerate(tasks, start=1):
            parts.append(f"## SECTION {i}: {task.subtopic}")
            parts.append("")
            parts.append(f"SUMMARY:\n{task.summary}")
            parts.append("")
            if task.sources:
                parts.append("SOURCES:")
                for j, src in enumerate(task.sources, start=1):
                    parts.append(f"  [{j}] {src.title} — {src.url}")
            parts.append("")
            parts.append("---")
            parts.append("")
        return "\n".join(parts)

    def _build_synthesis_prompt(
        self,
        topic: str,
        task_context: str,
        failed_tasks: list[ResearchTask],
    ) -> str:
        """Build the full synthesis prompt for Claude."""
        failed_note = ""
        if failed_tasks:
            failed_subtopics = [t.subtopic for t in failed_tasks]
            failed_note = (
                "\nNOTE: The following subtopics could not be researched and should "
                f"be omitted from the report: {', '.join(failed_subtopics)}\n"
            )

        return f"""MAIN TOPIC: {topic}

Below are research summaries for each subtopic of this topic. Your task is to
synthesize them into a comprehensive, professional markdown research report.

{failed_note}
RESEARCH SUMMARIES:
{task_context[:12000]}

INSTRUCTIONS:
Produce a complete markdown research report with the following structure:

1. **Executive Summary** (## Executive Summary):
   - 3-5 paragraphs synthesizing ALL the research
   - Highlight the most important findings, trends, and insights
   - Write for an executive audience — clear, concise, high-level

2. **Section for each subtopic** (## Section Name):
   - Present the subtopic name as a clear H2 heading
   - 2-4 paragraphs summarizing findings with depth and nuance
   - Include specific data points, statistics, or examples when available
   - Note any limitations or gaps in the research

3. **Key Takeaways** (## Key Takeaways):
   - 5-8 bullet points of the most critical insights
   - Actionable where possible
   - Highlight strategic implications

4. **References** (## References):
   - Numbered list of all sources cited
   - Format: [N] Title — URL

Formatting rules:
- Use proper markdown: ## for H2, ### for H3, **bold** for emphasis
- Do not use H1 (#) headings — the title will be added separately
- Write in complete, well-crafted paragraphs
- Be objective and balanced
- Total report should be 1500-4000 words"""

    def _empty_report(self) -> str:
        """Return a minimal report for empty input."""
        return "# Research Report\n\n*No research topic provided.*\n"

    def _minimal_report(self, topic: str) -> str:
        """Return a minimal report when no research could be performed."""
        return (
            f"# Research Report: {topic}\n\n"
            "## Executive Summary\n\n"
            "*Unable to complete research. No research tasks produced valid results.*\n\n"
            "## Key Takeaways\n\n"
            "- Research could not be completed for this topic.\n\n"
            "## References\n\n"
            "*No sources were collected.*\n"
        )

    def _fallback_synthesize(
        self,
        topic: str,
        tasks: list[ResearchTask],
        failed_tasks: list[ResearchTask],
    ) -> str:
        """Manually assemble a report when Claude synthesis fails."""
        lines = [f"# Research Report: {topic}", ""]

        # Executive Summary — combine first paragraph of each task
        lines.append("## Executive Summary")
        lines.append("")
        for task in tasks:
            if task.summary:
                first_para = task.summary.split("\n\n")[0] if "\n\n" in task.summary else task.summary
                lines.append(first_para)
                lines.append("")
                break

        # Sections
        for task in tasks:
            if not task.subtopic:
                continue
            lines.append(f"## {task.subtopic}")
            lines.append("")
            if task.summary:
                lines.append(task.summary)
            else:
                lines.append("*No findings available.*")
            lines.append("")
            if task.sources:
                lines.append("**Sources:**")
                for src in task.sources:
                    if src.url:
                        lines.append(f"- [{src.title or 'Source'}]({src.url})")
                lines.append("")

        # Key Takeaways
        lines.append("## Key Takeaways")
        lines.append("")
        for task in tasks:
            if task.summary:
                first_sentence = task.summary.split(".")[0].strip()
                if first_sentence:
                    lines.append(f"- **{task.subtopic}:** {first_sentence}.")
        lines.append("")

        # References
        lines.append("## References")
        lines.append("")
        ref_num = 1
        for task in tasks:
            for src in task.sources:
                if src.url:
                    lines.append(f"{ref_num}. [{src.title or 'Source'}]({src.url})")
                    ref_num += 1
        lines.append("")

        return "\n".join(lines)
