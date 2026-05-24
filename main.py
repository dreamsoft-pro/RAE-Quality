# main.py
import asyncio
import logging
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from engines.security.sast import SastSecurityEngine
from engines.testing.coverage import CoverageEngine
from engines.governance.tribunal import QualityTribunal
from models.report import AuditResult, Verdict

# Import Bridge Handler
from rae_core.bridge.handler import register_bridge

# Import Enterprise Guard
from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

# Import TestIntegrityGuard
from src.test_integrity_guard import TestIntegrityGuard

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Quality")

class QualitySentinel:
    def __init__(self):
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-quality")
        self.tribunal = QualityTribunal()
        self.test_guard = TestIntegrityGuard()
        self.api_url = "http://rae-api-dev:8000"
        
        # Quality baseline defaults
        self.baseline_coverage = 80.0
        self.baseline_vulnerabilities = 0

    async def _enforce_verdict(self, result: AuditResult, code: str, project: str):
        """Autonomously triggers Phoenix repair if code is rejected."""
        if result.verdict == Verdict.REJECTED:
            logger.warning("enforcement_triggered", reason="Code rejected by Tribunal. Waking up Phoenix.")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(f"{self.api_url}/v2/bridge/interact", json={
                        "intent": "REFACTOR_CODE",
                        "source_agent": "rae-quality",
                        "target_agent": "rae-phoenix",
                        "payload": {
                            "project": project,
                            "faulty_code": code,
                            "tribunal_reasoning": result.reasoning,
                            "issues": [issue.dict() for issue in result.issues],
                            "instruction": "URGENT: Fix the provided code based on the Tribunal's reasoning to pass the Quality Gate."
                        }
                    }, headers={"X-Tenant-Id": "system-governance", "X-Project-Id": project})
            except Exception as e:
                logger.error("enforcement_dispatch_failed", error=str(e))

    @audited_operation(operation_name="run_quality_audit", impact_level="medium")
    async def perform_static_audit(self, project_path: str, baseline_code: str = None, proposed_code: str = None) -> str:
        """
        Executes a full security and coverage audit, enforcing baseline and test integrity checks.
        """
        # 1. Run SAST Security Engine
        sast = SastSecurityEngine(project_path)
        sast_report = await sast.run()
        
        # 2. Run Coverage Engine
        testing = CoverageEngine(project_path)
        test_report = await testing.run()
        
        # 3. Check Quality Baseline Regression
        rejection_reasons = []
        
        if test_report.score < self.baseline_coverage:
            rejection_reasons.append(f"Test coverage ({test_report.score}%) dropped below baseline ({self.baseline_coverage}%).")
            
        if sast_report.critical_count > self.baseline_vulnerabilities:
            rejection_reasons.append(f"Vulnerability count ({sast_report.critical_count}) exceeds baseline ({self.baseline_vulnerabilities}).")

        # 4. Enforce TestIntegrityGuard if test modification is proposed
        if baseline_code and proposed_code:
            passed, reason = self.test_guard.validate_test_integrity(baseline_code, proposed_code)
            if not passed:
                rejection_reasons.append(reason)

        if rejection_reasons:
            rejection_summary = " | ".join(rejection_reasons)
            logger.warning(f"Quality Gate REJECT: {rejection_summary}")
            return f"REJECTED. Reason: {rejection_summary}"
            
        return f"ACCEPTED. Security Score: {sast_report.score}, Coverage Score: {test_report.score}"

    @audited_operation(operation_name="run_tribunal_audit", impact_level="high")
    async def perform_tribunal_audit(self, code: str, project: str, importance: str = "medium") -> AuditResult:
        """Executes the advanced 3-tier tribunal audit and enforces policy."""
        result = await self.tribunal.run_audit(code, project, importance)
        
        # Enforce active Phoenix intervention
        asyncio.create_task(self._enforce_verdict(result, code, project))
        
        return result

# Inicjalizacja usług
sentinel = QualitySentinel()
mcp_server = Server("rae-quality")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="run_static_quality_audit",
            description="Executes SAST and Coverage scans, enforcing Quality Baseline and TestIntegrity checks. Audited.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "baseline_code": {"type": "string", "description": "Original test code before modifications"},
                    "proposed_code": {"type": "string", "description": "New proposed test code to evaluate"}
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="run_tribunal_audit",
            description="Executes the 3-Tier Quality Tribunal (Semantic + LLM) on a code snippet. High impact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "project": {"type": "string"},
                    "importance": {"type": "string", "enum": ["low", "medium", "critical"]}
                },
                "required": ["code", "project"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "run_static_quality_audit":
        path = arguments.get("project_path")
        baseline = arguments.get("baseline_code")
        proposed = arguments.get("proposed_code")
        result_text = await sentinel.perform_static_audit(path, baseline, proposed)
        return [TextContent(type="text", text=result_text)]
    
    if name == "run_tribunal_audit":
        code = arguments.get("code")
        project = arguments.get("project")
        importance = arguments.get("importance", "medium")
        result = await sentinel.perform_tribunal_audit(code, project, importance)
        return [TextContent(type="text", text=result.json())]
        
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
register_bridge(app, "rae-quality")
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.post("/v2/quality/audit")
async def api_tribunal_audit(payload: dict):
    """External API endpoint for RAE Suite to request semantic audits."""
    code = payload.get("code")
    project = payload.get("project")
    importance = payload.get("importance", "medium")
    return await sentinel.perform_tribunal_audit(code, project, importance)

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
