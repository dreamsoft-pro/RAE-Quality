# main.py
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
from mcp.server.sse import SseServerTransport
from engines.security.sast import SastSecurityEngine
from engines.testing.coverage import CoverageEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Quality")

# Inicjalizacja serwera MCP (Low-level dla pełnej kontroli)
mcp_server = Server("rae-quality")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="run_quality_audit",
            description="Executes a full security and coverage audit for a given project.",
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
        sast = SastSecurityEngine(path)
        sast_report = await sast.run()
        testing = CoverageEngine(path)
        test_report = await testing.run()
        return [TextContent(type="text", text=f"Audit complete. Security: {sast_report.score}, Coverage: {test_report.score}")]
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
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
