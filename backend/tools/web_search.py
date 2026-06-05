from typing import Optional

from config import config
from utils.logger import logger


class SearchTool:
    """
    Web search tool backed by Tavily (when configured) with DuckDuckGo fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._tavily_key = api_key or config.TAVILY_API_KEY
        self._ddgs = None

        if self._tavily_key and self._tavily_key.strip():
            logger.info("SearchTool initialized (Tavily)")
        else:
            from ddgs import DDGS
            self._ddgs = DDGS()
            logger.info("SearchTool initialized (DuckDuckGo — no Tavily key)")

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        if not query or not query.strip():
            logger.warning("Search called with empty query")
            return []

        if self._tavily_key and self._tavily_key.strip():
            return self._search_tavily(query, max_results)

        return self._search_duckduckgo(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[dict]:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self._tavily_key)
            response = client.search(
                query=query.strip(),
                max_results=max_results,
                search_depth="basic",
            )
            results = []
            for i, item in enumerate(response.get("results", [])):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "score": 1.0 - (i * 0.1),
                })
            logger.info(f"Tavily returned {len(results)} results")
            return results
        except ImportError:
            logger.warning("tavily-python not installed; falling back to DuckDuckGo")
            return self._search_duckduckgo(query, max_results)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}; falling back to DuckDuckGo")
            return self._search_duckduckgo(query, max_results)

    def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        try:
            from ddgs import DDGS

            if self._ddgs is None:
                self._ddgs = DDGS()

            logger.info(f"DuckDuckGo search: '{query[:100]}...'")
            raw_results = list(self._ddgs.text(query.strip(), max_results=max_results))

            results = []
            for i, item in enumerate(raw_results):
                results.append({
                    "url": item.get("href", ""),
                    "title": item.get("title", ""),
                    "content": item.get("body", ""),
                    "score": 1.0 - (i * 0.1),
                })

            logger.info(f"DuckDuckGo returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def search_raw(self, query: str, max_results: int = 5) -> dict:
        results = self.search(query, max_results)
        return {"results": results} if results else {}
