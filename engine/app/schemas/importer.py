from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MappingCandidate(BaseModel):
    target: str
    source: str | None
    confidence: Literal["high", "medium", "none"]


class PreviewResponse(BaseModel):
    preview_id: str
    filename: str
    encoding: str
    delimiter: str
    columns: list[str]
    mappings: list[MappingCandidate]
    sample_rows: list[dict[str, str]]
    timezone_hint: str | None


class ImportCommitRequest(BaseModel):
    preview_id: str
    filename: str
    mapping: dict[str, str]
    timezone: str = "UTC"


class RowIssue(BaseModel):
    row_number: int
    message: str


class ImportResult(BaseModel):
    batch_id: int
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    error_rows: int
    issues: list[RowIssue]
