from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AutomationResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool
    message: str = ""
    data: Any = None


class AutomationRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must not be empty")
        return value
