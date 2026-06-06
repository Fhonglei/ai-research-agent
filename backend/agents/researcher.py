import uuid
from typing import Optional
from config import config
from llm.client import LLMClient
from models.schemas import ResearchTask, Source
from tools.web_search import SearchTool
from tools.content_fetcher import ContentFetcher
from utils.logger import logger


class Researcher:
    """
    Researches a single subtopic by searching the web, fetching top results,
    and synthesizing findings into a concise summary using an LLM.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        search_tool: Optional[SearchTool] = None,
        content_fetcher: Optional[ContentFetcher] = None,
    ):
        """
        Initialize the researcher.

        Args:
            api_key: DeepSeek API key. Falls back to config.
            model: Model to use. Falls back to config.MODEL.
            search_tool: Pre-configured SearchTool instance (created if not provided).
            content_fetcher: Pre-configured ContentFetcher instance (created if not provided).
        """
        self.llm = LLMClient(api_key=api_key, model=model)
        self.model = self.llm.model
        self.search_tool = search_tool or SearchTool()
        self.content_fetcher = content_fetcher or ContentFetcher()
        logger.info(f"Researcher initialized with model={self.model}")

    def research(self, subtopic: str) -> ResearchTask:
        """
        Research a subtopic: search, fetch content, and summarize with LLM.

        Args:
            subtopic: The subtopic string to research.

        Returns:
            A ResearchTask with summary, sources, and status='complete'.
            On failure, returns a ResearchTask with status='failed' and an
            error message in the summary.
        """
        task_id = str(uuid.uuid4())
        task = ResearchTask(
            id=task_id,
            subtopic=subtopic,
            status="in_progress",
        )

        if not subtopic or not subtopic.strip():
            logger.warning("research called with empty subtopic")
            task.status = "failed"
            task.summary = "No subtopic provided."
            return task

        logger.info(f"Researching subtopic: '{subtopic[:100]}...'")

        try:
            # Step 1: Search the web
            search_results = self.search_tool.search(
                query=subtopic,
                max_results=config.SEARCH_MAX_RESULTS,
            )
            if not search_results:
                broader_query = f"{subtopic} overview analysis sources"
                search_results = self.search_tool.search(
                    query=broader_query,
                    max_results=config.SEARCH_MAX_RESULTS,
                )
            if not search_results:
                task.status = "failed"
                task.summary = f"No search results found for '{subtopic}'."
                logger.warning(f"No search results for subtopic: {subtopic}")
                return task

            # Step 2: Fetch content from top results
            sources: list[Source] = []
            top_results = search_results[:config.FETCH_TOP_N]
            for result in top_results:
                url = result.get("url", "")
                title = result.get("title", "")
                snippet = result.get("content", "")

                # Fetch full page content
                fetched_content = ""
                if url:
                    fetched_content = self.content_fetcher.fetch_content(url)

                source = Source(
                    url=url,
                    title=title,
                    snippet=snippet,
                    content=fetched_content,
                )
                sources.append(source)

            # Filter to sources that have some content
            valid_sources = [s for s in sources if s.content or s.snippet]
            if not valid_sources:
                valid_sources = sources  # Use what we have

            # Step 3: Compile context for LLM
            context_parts = []
            for i, src in enumerate(valid_sources, start=1):
                context_parts.append(f"SOURCE {i}: {src.title}")
                context_parts.append(f"URL: {src.url}")
                context_parts.append(f"Content: {src.content or src.snippet}")
                context_parts.append("---")

            context = "\n".join(context_parts)

            # Step 4: Ask LLM to summarize
            summary = self._summarize_with_llm(subtopic, context)

            task.summary = summary
            task.sources = sources
            task.status = "complete"
            logger.info(f"Research complete for subtopic: '{subtopic[:80]}...' "
                        f"({len(sources)} sources, {len(summary)} chars summary)")
            return task

        except Exception as e:
            logger.error(f"Research failed for subtopic '{subtopic[:80]}...': {e}")
            task.status = "failed"
            task.summary = f"Research failed: {str(e)}"
            return task

    def _summarize_with_llm(self, subtopic: str, context: str) -> str:
        """
        Use the LLM to synthesize search results into a research summary.

        Args:
            subtopic: The subtopic being researched.
            context: Compiled source text.

        Returns:
            A 2-3 paragraph summary with key insights.
        """
        prompt = f"""You are a research analyst summarizing findings for the following subtopic:

SUBTOPIC: {subtopic}

Below are search results and fetched web content related to this subtopic.
Synthesize this information into a concise, professional research summary.

Guidelines:
- Write 2-3 well-structured paragraphs
- Include the most important facts, data points, and insights
- Cite sources inline by number (e.g., [1], [2]) when referencing specific information
- Be objective and balanced — present multiple perspectives if they exist
- Avoid fluff and filler; every sentence should add value
- Mention any notable gaps or conflicting information in the sources
- End with a one-sentence bottom-line takeaway

SOURCE MATERIAL:
{context[:8000]}"""

        try:
            summary = self.llm.complete(
                system=(
                    "You are an expert research analyst. You synthesize information "
                    "from multiple web sources into clear, factual research summaries. "
                    "Your writing is professional, objective, and concise. Always cite "
                    "sources when presenting specific claims."
                ),
                user=prompt,
                max_tokens=2048,
                temperature=0.5,
            )
            return summary.strip()

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            # Fallback: return a simple extraction-based summary
            sentences = [s.strip() for s in context.split(".") if len(s.strip()) > 30]
            summary = "Summary of findings for " + subtopic + ":\n\n"
            summary += "Key information extracted from sources:\n"
            for i, sentence in enumerate(sentences[:6], start=1):
                if sentence:
                    summary += f"- {sentence.strip()}.\n"
            return summary
