from pydantic import BaseModel, ConfigDict, Field, field_validator


class WebSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must not be empty")
        return value


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    search_required: bool
    search_query: str | None = None
    results: list[SearchResult] = Field(default_factory=list)
    answer: str
