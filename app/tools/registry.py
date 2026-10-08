from __future__ import annotations
from typing import Callable, Any
from app.core.types import ToolRequest
from app.execution.sql import validate_read_only_sql

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable):
        self._tools[name] = fn

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(self, request: ToolRequest) -> Any:
        fn = self.get(request.tool_name)
        if not fn:
            raise KeyError(f"Tool not found: {request.tool_name}")
        result = fn(**request.arguments)
        if hasattr(result, "__await__"):
            result = await result
        return result

def query_readonly_database_handler(sql: str) -> dict:
    valid, reason = validate_read_only_sql(sql)
    if not valid:
        return {"status": "blocked", "error": f"SQL validation failed: {reason}", "read_only": False}
    return {"status": "executed", "sql": sql, "rows": [], "read_only": True}

async def run_python_sandbox_handler(code: str) -> dict:
    from app.execution.sandbox import DockerSandbox
    sandbox = DockerSandbox()
    return await sandbox.run_python(code)

def build_default_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register("read_ticket", lambda ticket_id: {"ticket_id": ticket_id, "status": "open", "mock": True})
    r.register("search_tickets", lambda query: {"query": query, "results": []})
    r.register("query_readonly_database", query_readonly_database_handler)
    r.register("update_ticket", lambda ticket_id, status: {"ticket_id": ticket_id, "status": status, "mock": True})
    r.register("delete_customer", lambda customer_id: {"customer_id": customer_id, "deleted": True, "mock": True})
    r.register("run_python_sandbox", run_python_sandbox_handler)
    return r
