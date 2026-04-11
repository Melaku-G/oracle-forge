import json
import httpx
from agent.models import SubQuery

MCP_BASE_URL = "http://localhost:5000"

# Maps DB type to MCP tool name (must match tools.yaml exactly)
DB_TYPE_TO_TOOL = {
    "mongodb":    "mongo_aggregate",
    "duckdb":     "duckdb_query",
    "postgresql": "postgres_query",
    "sqlite":     "sqlite_query",
}


class QueryExecutor:

    def __init__(self, mcp_base_url: str = MCP_BASE_URL, timeout: float = 30.0):
        self.base_url = mcp_base_url.rstrip("/")
        self.timeout = timeout

    def execute(self, sub_query: SubQuery) -> dict:
        """Execute a sub-query via MCP Toolbox. Raises on error — caller handles retry."""
        tool_name = DB_TYPE_TO_TOOL.get(sub_query.database_type)
        if not tool_name:
            raise ValueError(f"No MCP tool mapped for db_type '{sub_query.database_type}'")

        payload = self._build_payload(sub_query, tool_name)
        response = httpx.post(
            f"{self.base_url}/v1/tools/{tool_name}:invoke",
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"MCP tool '{tool_name}' returned HTTP {response.status_code}: {response.text}"
            )

        result = response.json()
        if result.get("error"):
            raise RuntimeError(result["error"])

        return result.get("result", result)

    def _build_payload(self, sub_query: SubQuery, tool_name: str) -> dict:
        """Build the tool invocation payload based on DB type."""
        if sub_query.database_type == "mongodb":
            # query field contains JSON pipeline string
            try:
                pipeline = json.loads(sub_query.query)
                collection = pipeline.pop(0).get("$collection", "business") if pipeline and "$collection" in pipeline[0] else "business"
            except (json.JSONDecodeError, IndexError):
                pipeline = sub_query.query
                collection = "business"
            return {"collection": collection, "pipeline": json.dumps(pipeline)}

        # SQL-based tools (postgresql, sqlite, duckdb)
        return {"sql": sub_query.query}

    def merge(self, left: dict, right: dict, left_key: str, right_key: str,
              left_db: str, right_db: str) -> dict:
        """Call cross_db_merge tool to join two result sets with key normalisation."""
        payload = {
            "left_results": json.dumps(left),
            "right_results": json.dumps(right),
            "left_key": left_key,
            "right_key": right_key,
            "left_db": left_db,
            "right_db": right_db,
        }
        response = httpx.post(
            f"{self.base_url}/v1/tools/cross_db_merge:invoke",
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(f"cross_db_merge returned HTTP {response.status_code}: {response.text}")
        return response.json().get("result", {})
