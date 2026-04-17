from typing import Any, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    available_databases: list[str]
    session_id: str
    dataset: Optional[str] = None  # e.g. "crmarenapro" — used for db_path injection


class SubQuery(BaseModel):
    database_type: str  # "postgresql" | "sqlite" | "mongodb" | "duckdb" | "postgresql_crm"
    query: str
    intent: str
    db_path: Optional[str] = None       # for datasets with multiple SQLite/DuckDB files
    logical_name: Optional[str] = None  # e.g. "activities", "support" — used for schema lookup


class QueryTrace(BaseModel):
    timestamp: str
    sub_queries: list[SubQuery]
    databases_used: list[str]
    self_corrections: list[dict]
    raw_results: dict[str, Any]
    merge_operations: list[str]


class AgentResponse(BaseModel):
    answer: str
    query_trace: QueryTrace
    confidence: float  # 0.0–1.0
    error: Optional[str] = None
