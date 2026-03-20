# main.py
import asyncio
import logging
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from engines.security.sast import SastSecurityEngine
from engines.testing.coverage import CoverageEngine

# Import Bridge Handler
from rae_core.bridge.handler import register_bridge

# Import Enterprise Guard
from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

class QualitySentinel:
    def __init__(self):
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-quality")

    @audited_operation(operation_name="run_quality_audit", impact_level="medium")
    async def perform_audit(self, project_path: str):
        """Executes a full security and coverage audit for a given project."""
        sast = SastSecurityEngine(project_path)
        sast_report = await sast.run()
        
        testing = CoverageEngine(project_path)
        test_report = await testing.run()
        
        return f"Audit complete. Security: {sast_report.score}, Coverage: {test_report.score}"

# Inicjalizacja usług
sentinel = QualitySentinel()
mcp_server = Server("rae-quality")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="run_quality_audit",
            description="Executes a full security and coverage audit for a given project. Audited operation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"}
                },
                "required": ["project_path"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "run_quality_audit":
        path = arguments.get("project_path")
        result_text = await sentinel.perform_audit(path)
        return [TextContent(type="text", text=result_text)]
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
register_bridge(app, "rae-quality")
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
