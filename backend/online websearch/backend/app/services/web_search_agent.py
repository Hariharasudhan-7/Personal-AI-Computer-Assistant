import logging

from app.config import Settings
from app.models.schemas import SearchResult, WebSearchResponse
from app.services.duckduckgo_service import DuckDuckGoSearchError, DuckDuckGoService
from app.services.gemini_service import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


class WebSearchAgentError(RuntimeError):
    """Raised when the web-search workflow cannot complete."""


class WebSearchAgent:
    def __init__(
        self,
        settings: Settings,
        gemini_service: GeminiService | None = None,
        duckduckgo_service: DuckDuckGoService | None = None,
    ):
        self.gemini = gemini_service or GeminiService(settings)
        self.duckduckgo = duckduckgo_service or DuckDuckGoService(settings)

    def run(self, query: str) -> WebSearchResponse:
        logger.info("Processing web-search request")
        try:
            search_query = self.gemini.generate_search_query(query)
            logger.info("Generated search query: %s", search_query)
            results = self.duckduckgo.search(search_query)
            logger.info("Retrieved %d results", len(results))
            answer = self.gemini.generate_final_answer(query, search_query, results)
            return WebSearchResponse(
                query=query,
                search_required=True,
                search_query=search_query,
                results=results,
                answer=answer,
            )
        except (GeminiServiceError, DuckDuckGoSearchError) as exc:
            raise WebSearchAgentError(str(exc)) from exc
        except Exception as exc:
            logger.exception("Unexpected web-search workflow failure")
            raise WebSearchAgentError("Web-search request could not be completed") from exc
