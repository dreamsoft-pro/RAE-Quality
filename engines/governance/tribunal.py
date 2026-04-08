# engines/governance/tribunal.py
import asyncio
import os
import httpx
import logging
from typing import Dict, Any, Optional
from models.report import AuditResult, Verdict, QualityIssue, Severity

logger = logging.getLogger("RAE-Quality.Tribunal")

class QualityTribunal:
    """Advanced 3-Tier Quality Tribunal for Silicon Oracle RAE Suite."""
    
    def __init__(self, rae_api_url: Optional[str] = None):
        self.api_url = rae_api_url or os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def run_audit(self, code: str, project: str, importance: str = "medium") -> AuditResult:
        """Executes the full 3-tier audit pipeline with Dynamic Consensus."""
        logger.info(f"tribunal_audit_started: project={project}, importance={importance}")
        
        # Determine if we need multi-model Council (3x3)
        complexity_score = self._calculate_complexity(code)
        use_council = (importance == "critical") or (complexity_score > 0.4)
        
        if use_council:
            logger.warning("DYNAMIC_CONSENSUS_ACTIVE: Activating 3-model Council for this audit.")

        # --- TIER 1: Deterministic Guards ---
        t1_result = self._run_tier1_checks(code)
        if t1_result.verdict == Verdict.REJECTED:
            return t1_result

        # --- TIER 2: Local Semantic Consensus (Context-Aware) ---
        # If use_council=True, we use 'council_l2' strategy (3 models)
        t2_result = await self._run_tier2_consensus(code, project, use_council=use_council)
        
        if t2_result.verdict == Verdict.REJECTED:
            return t2_result
            
        # Skip Tier 3 if it's not critical and Tier 2 passed
        if not use_council and importance != "critical":
            return t2_result

        # --- TIER 3: Supreme Court (SaaS Escalation via Bridge) ---
        return await self._run_tier3_escalation(code, project, t2_result, use_council=use_council)

    def _run_tier1_checks(self, code: str) -> AuditResult:
        """Fast, static, and deterministic checks."""
        issues = []
        if "TODO" in code.upper() or "FIXME" in code.upper():
            issues.append(QualityIssue(engine="Tier1", severity=Severity.MEDIUM, message="Code contains pending placeholders (TODO/FIXME)."))
        
        if len(code) < 10:
            issues.append(QualityIssue(engine="Tier1", severity=Severity.LOW, message="Code snippet is suspiciously short."))

        if issues:
            return AuditResult(verdict=Verdict.REJECTED, confidence=1.0, score=0.0, issues=issues, reasoning="Failed Tier 1 static guards.", tier_reached=1)
        
        return AuditResult(verdict=Verdict.PASSED, confidence=1.0, score=1.0, reasoning="Passed Tier 1 static guards.", tier_reached=1)

    def _calculate_complexity(self, code: str) -> float:
        """Simple heuristic for code complexity."""
        # Factor 1: Length
        length_score = min(len(code) / 2000, 1.0)
        # Factor 2: Control structures
        logic_keywords = ["if", "else", "for", "while", "switch", "try", "catch", "async", "await"]
        keyword_count = sum(1 for word in logic_keywords if word in code.lower())
        logic_score = min(keyword_count / 15, 1.0)
        
        return (length_score * 0.4) + (logic_score * 0.6)

    async def _run_tier2_consensus(self, code: str, project: str, use_council: bool = False) -> AuditResult:
        """Semantic review using Local LLM or 3-model Council."""
        try:
            guidelines = await self._fetch_project_guidelines(project)
            strategy = "council_l2" if use_council else "single"
            
            prompt = f"""
            SYSTEM: You are the RAE Tier 2 Quality Auditor (Mode: {strategy}).
            PROJECT CONTEXT: {guidelines}
            CODE TO AUDIT:
            ```
            {code}
            ```
            TASK: Evaluate for SOLID principles, readability, and context compliance.
            Respond ONLY in JSON: {{"verdict": "PASSED"|"REJECTED", "score": 0.0-1.0, "reasoning": "string"}}
            """
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                    "intent": "LOCAL_LLM_AUDIT",
                    "target_agent": "rae-local-reasoner",
                    "strategy": strategy, # This triggers the consensus in Broker
                    "payload": {"prompt": prompt}
                })
                
                if resp.status_code == 200:
                    data = resp.json().get("payload", {}).get("interaction_data", {})
                    return AuditResult(
                        verdict=Verdict.PASSED if data.get("verdict") == "PASSED" else Verdict.REJECTED,
                        confidence=0.95 if use_council else 0.85,
                        score=data.get("score", 0.5),
                        reasoning=data.get("reasoning", "Consensus reached."),
                        tier_reached=2
                    )
                return AuditResult(verdict=Verdict.ERROR, confidence=0.0, score=0.0, reasoning="Tier 2 Bridge error.", tier_reached=2)
        except Exception as e:
            return AuditResult(verdict=Verdict.ERROR, confidence=0.0, score=0.0, reasoning=f"Tier 2 Exception: {str(e)}", tier_reached=2)

    async def _run_tier3_escalation(self, code: str, project: str, t2_result: AuditResult, use_council: bool = False) -> AuditResult:
        """High-level reasoning using SaaS Models or 3-model Supreme Council."""
        strategy = "council_l3" if use_council else "single"
        logger.warning(f"tier3_escalation_initiated: strategy={strategy}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                    "intent": "SUPREME_COURT_AUDIT",
                    "target_agent": "rae-oracle-gemini",
                    "strategy": strategy,
                    "payload": {
                        "code": code,
                        "project": project,
                        "previous_reasoning": t2_result.reasoning
                    }
                })
                
                if resp.status_code == 200:
                    data = resp.json().get("payload", {}).get("interaction_data", {})
                    return AuditResult(
                        verdict=Verdict.PASSED if data.get("verdict") == "PASSED" else Verdict.REJECTED,
                        confidence=0.99 if use_council else 0.98,
                        score=data.get("score", 1.0),
                        reasoning=f"Supreme Court Verdict ({strategy}): {data.get('reasoning')}",
                        tier_reached=3
                    )
            return AuditResult(verdict=Verdict.ERROR, confidence=0.0, score=0.0, reasoning="Supreme Court error.", tier_reached=3)
        except Exception as e:
            return AuditResult(verdict=Verdict.ERROR, confidence=0.0, score=0.0, reasoning=f"Tier 3 Exception: {str(e)}", tier_reached=3)

    async def _fetch_project_guidelines(self, project: str) -> str:
        """Retrieves project-specific coding standards from RAE Memory."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": "coding standards and architectural guidelines",
                    "project": project,
                    "k": 3
                })
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    return " ".join([r.get("content", "") for r in results])
            return "General best practices."
        except:
            return "General best practices."
