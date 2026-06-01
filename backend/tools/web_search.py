from typing import Optional
from tavily import TavilyClient
from config import config
from utils.logger import logger


class SearchTool:
    """
    Web search tool backed by the Tavily Search API.

    Provides a clean interface for executing web searches and returning
    structured results with url, title, content, and relevance score.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search tool with a Tavily API key.

        Args:
            api_key: Tavily API key. Falls back to TAVILY_API_KEY from config.
        """
        self.api_key = api_key or config.TAVILY_API_KEY
        self.client = TavilyClient(api_key=self.api_key)
        logger.info("SearchTool initialized")

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
            response = self.client.search(
                query=query.strip(),
                max_results=max_results,
                search_depth="advanced",
                include_raw_content=False,
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                })

            logger.info(f"Search returned {len(results)} results for query")
            return results

        except Exception as e:
            logger.error(f"Search failed for query '{query[:80]}...': {e}")
            return []

    def search_raw(self, query: str, max_results: int = 5) -> dict:
        """
        Execute a web search and return the raw API response dict.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.

        Returns:
            Raw response dict from Tavily, or an empty dict on failure.
        """
        if not query or not query.strip():
            logger.warning("search_raw called with empty query")
            return {}

        try:
            logger.info(f"Raw search for: '{query[:100]}...'")
            response = self.client.search(
                query=query.strip(),
                max_results=max_results,
                search_depth="advanced",
                include_raw_content=False,
            )
            return response

        except Exception as e:
            logger.error(f"Raw search failed for query '{query[:80]}...': {e}")
            return {}
