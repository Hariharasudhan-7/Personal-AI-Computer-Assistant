import logging
from collections.abc import Callable
from typing import Any

from app.config import Settings
from app.models.schemas import SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoSearchError(RuntimeError):
    """Raised when DuckDuckGo cannot complete a search."""


class DuckDuckGoService:
    def __init__(self, settings: Settings, search_client: Callable[..., Any] | None = None):
        self.settings = settings
        self._search_client = search_client

    def search(self, query: str) -> list[SearchResult]:
        try:
            if self._search_client is None:
                from ddgs import DDGS

                self._search_client = DDGS(timeout=self.settings.search_timeout_seconds).text
            raw_results = self._search_client(query, max_results=self.settings.max_results)
            results: list[SearchResult] = []
            for item in raw_results or []:
                title = str(item.get("title", "")).strip()
                url = str(item.get("href", item.get("url", ""))).strip()
                snippet = str(item.get("body", item.get("snippet", ""))).strip()
                if title and url:
                    results.append(SearchResult(title=title, url=url, snippet=snippet))
                if len(results) >= self.settings.max_results:
                    break
            if not results:
                raise DuckDuckGoSearchError("DuckDuckGo returned no results")
            logger.info("DuckDuckGo returned %d results", len(results))
            return results
        except Exception as exc:
            logger.exception("DuckDuckGo search failed")
            raise DuckDuckGoSearchError("DuckDuckGo search failed") from exc
