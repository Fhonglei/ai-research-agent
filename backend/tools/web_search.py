from typing import Optional
from ddgs import DDGS
from utils.logger import logger


class SearchTool:
    """
    Web search tool backed by DuckDuckGo (free, no API key required).

    Provides a clean interface for executing web searches and returning
    structured results with url, title, content, and relevance score.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search tool.

        Args:
            api_key: Ignored (kept for interface compatibility). DuckDuckGo
                     does not require an API key.
        """
        self.ddgs = DDGS()
        logger.info("SearchTool initialized (DuckDuckGo)")

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Execute a web search and return structured results.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return (default 5).

        Returns:
            A list of dicts, each with keys: url, title, content, score.
            Returns an empty list on failure.
        """
        if not query or not query.strip():
            logger.warning("Search called with empty query")
            return []

        try:
            logger.info(f"Searching web for: '{query[:100]}...'")
            raw_results = list(self.ddgs.text(
                query.strip(),
                max_results=max_results,
            ))

            results = []
            for i, item in enumerate(raw_results):
                results.append({
                    "url": item.get("href", ""),
                    "title": item.get("title", ""),
                    "content": item.get("body", ""),
                    "score": 1.0 - (i * 0.1),  # Simple relevance scoring by position
                })

            logger.info(f"Search returned {len(results)} results for query")
            return results

        except Exception as e:
            logger.error(f"Search failed for query '{query[:80]}...': {e}")
            return []

    def search_raw(self, query: str, max_results: int = 5) -> dict:
        """
        Execute a web search and return the raw response dict.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.

        Returns:
            Raw response dict, or an empty dict on failure.
        """
        results = self.search(query, max_results)
        return {"results": results} if results else {}
