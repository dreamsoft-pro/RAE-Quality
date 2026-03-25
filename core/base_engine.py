# core/base_engine.py
from abc import ABC, abstractmethod
from models.report import ScanReport, QualityIssue
import logging

class BaseQualityEngine(ABC):
    """Abstrakcyjna baza dla wszystkich silników sprawdzania jakości."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.logger = logging.getLogger(f"RAE-Quality.{self.__class__.__name__}")

    @abstractmethod
    async def run(self) -> ScanReport:
        """Uruchamia proces skanowania i zwraca ustandaryzowany raport."""
        pass

    def report_to_lab(self, report: ScanReport):
        """Przesyła raport do RAE-Lab dla analizy Kaizen."""
        # W przyszłości: API call do RAE-Lab
        self.logger.info(f"Report generated for {report.project} with score {report.score}")
