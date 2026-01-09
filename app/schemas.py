from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="default")
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
