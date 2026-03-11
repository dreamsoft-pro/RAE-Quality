# engines/security/sast.py
import asyncio
import json
import subprocess
from core.base_engine import BaseQualityEngine
from models.report import ScanReport, QualityIssue, Severity

class SastSecurityEngine(BaseQualityEngine):
    """Silnik Statycznej Analizy Bezpieczeństwa (SAST)."""
    
    async def run(self) -> ScanReport:
        self.logger.info("Starting SAST Scan...")
        issues = []
        
        try:
            # Uruchomienie Bandit w trybie JSON
            cmd = ["bandit", "-r", self.project_path, "-f", "json", "-q"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            if stdout:
                data = json.loads(stdout.decode())
                for result in data.get("results", []):
                    issues.append(QualityIssue(
                        id=result["test_id"],
                        engine="Bandit",
                        severity=self._map_severity(result["issue_severity"]),
                        message=result["issue_text"],
                        file_path=result["filename"],
                        line_number=result["line_number"],
                        fix_suggestion=result.get("more_info")
                    ))

            score = 1.0 - (len(issues) * 0.05) # Prosty algorytm punktacji
            return ScanReport(
                project_id=self.project_path.split("/")[-1],
                score=max(0.0, score),
                issues=issues,
                metrics={"vulnerabilities_found": len(issues)}
            )
        except Exception as e:
            self.logger.error(f"SAST failed: {e}")
            return ScanReport(project_id="error", score=0.0, issues=[], metrics={"error": str(e)})

    def _map_severity(self, bandit_sev: str) -> Severity:
        mapping = {
            "LOW": Severity.LOW,
            "MEDIUM": Severity.MEDIUM,
            "HIGH": Severity.HIGH,
            "CRITICAL": Severity.CRITICAL
        }
        return mapping.get(bandit_sev, Severity.LOW)
