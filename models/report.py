# models/report.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class QualityIssue(BaseModel):
    id: str
    engine: str
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None

class ScanReport(BaseModel):
    project_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: float # 0.0 to 1.0
    issues: List[QualityIssue]
    metrics: Dict[str, Any]
    meta: Dict[str, Any] = {}

class TestResult(BaseModel):
    test_name: str
    status: str # passed, failed, skipped
    duration: float
    error_log: Optional[str] = None
