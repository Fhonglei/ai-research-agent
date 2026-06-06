from typing import Any, Optional

from config import config, is_configured_value
from utils.logger import logger


class SearchTool:
    """Web search tool backed by Tavily with DuckDuckGo fallback."""

    def __init__(self, api_key: Optional[str] = None, ddgs_client: Optional[Any] = None):
        self._tavily_key = api_key if api_key is not None else config.TAVILY_API_KEY
        self._ddgs = ddgs_client

        if is_configured_value(self._tavily_key):
            logger.info("SearchTool initialized with Tavily")
        else:
            self._tavily_key = None
            if self._ddgs is None:
                from ddgs import DDGS

                self._ddgs = DDGS()
            logger.info("SearchTool initialized with DuckDuckGo fallback")

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        if not query or not query.strip():
            logger.warning("Search called with empty query")
            return []

        safe_max_results = max(1, min(max_results, 10))

        if is_configured_value(self._tavily_key):
            return self._search_tavily(query, safe_max_results)

        return self._search_duckduckgo(query, safe_max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[dict]:
        try:
            from tavily import TavilyClient  # pyright: ignore[reportMissingImports]

            client = TavilyClient(api_key=self._tavily_key)
            response = client.search(
                query=query.strip(),
                max_results=max_results,
                search_depth="basic",
            )
            results = [
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "score": 1.0 - (i * 0.1),
                }
                for i, item in enumerate(response.get("results", []))
            ]
            logger.info(f"Tavily returned {len(results)} results")
            return results
        except ImportError:
            logger.warning("tavily-python not installed; falling back to DuckDuckGo")
            return self._search_duckduckgo(query, max_results)
        except Exception as exc:
            logger.warning(f"Tavily search failed: {exc}; falling back to DuckDuckGo")
            return self._search_duckduckgo(query, max_results)

    def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        try:
            if self._ddgs is None:
                from ddgs import DDGS

                self._ddgs = DDGS()

            logger.info(f"DuckDuckGo search: '{query[:100]}...'")
            raw_results = list(self._ddgs.text(query.strip(), max_results=max_results))
            results = [
                {
                    "url": item.get("href", ""),
                    "title": item.get("title", ""),
                    "content": item.get("body", ""),
                    "score": 1.0 - (i * 0.1),
                }
                for i, item in enumerate(raw_results)
            ]

            logger.info(f"DuckDuckGo returned {len(results)} results")
            return results
        except Exception as exc:
            logger.error(f"DuckDuckGo search failed: {exc}")
            return []

    def search_raw(self, query: str, max_results: int = 5) -> dict:
        results = self.search(query, max_results)
        return {"results": results} if results else {}
