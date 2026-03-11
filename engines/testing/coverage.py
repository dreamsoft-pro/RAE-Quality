# engines/testing/coverage.py
import asyncio
import subprocess
import os
from core.base_engine import BaseQualityEngine
from models.report import ScanReport, QualityIssue, Severity

class CoverageEngine(BaseQualityEngine):
    """Silnik analizy pokrycia i generowania testów."""
    
    async def run(self) -> ScanReport:
        self.logger.info(f"Analyzing test coverage for {self.project_path}")
        
        try:
            # Uruchomienie pytest-cov
            # Musimy upewnić się, że ścieżka jest poprawna
            cmd = ["pytest", "--cov=" + self.project_path, "--cov-report=json", self.project_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            cov_file = "coverage.json"
            issues = []
            metrics = {}
            
            if os.path.exists(cov_file):
                with open(cov_file, 'r') as f:
                    data = json.load(f)
                    total_cov = data.get("totals", {}).get("percent_covered", 0)
                    metrics["total_coverage"] = total_cov
                    
                    # Generowanie issue dla plików z niskim pokryciem
                    for file, info in data.get("files", {}).items():
                        file_cov = info.get("summary", {}).get("percent_covered", 0)
                        if file_cov < 50:
                            issues.append(QualityIssue(
                                id="LOW_COVERAGE",
                                engine="Coverage",
                                severity=Severity.HIGH,
                                message=f"Krytycznie niskie pokrycie testami: {file_cov:.1f}%",
                                file_path=file,
                                fix_suggestion="Uruchom RAE-Phoenix w trybie CREATE_TEST dla tego pliku."
                            ))
                
                score = total_cov / 100.0
                return ScanReport(
                    project_id=self.project_path.split("/")[-1],
                    score=score,
                    issues=issues,
                    metrics=metrics
                )
            
            return ScanReport(project_id="none", score=0.0, issues=[], metrics={"error": "Coverage data not found"})
            
        except Exception as e:
            return ScanReport(project_id="error", score=0.0, issues=[], metrics={"error": str(e)})
