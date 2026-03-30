from rae_core.models.governance import QualityGate
from rae_core.models.behavior import BehaviorSignal

class QualityTribunal:
    """Manages v3 compliance verdicts."""
    
    def issue_verdict(self, gate_id: str, passed: bool, reason: str) -> BehaviorSignal:
        return BehaviorSignal(
            department="quality",
            signal_kind="policy_signal",
            guarantee_id=gate_id,
            reason=reason,
            severity_hint="low" if passed else "high"
        )
