# RAE-Quality/tests/test_tribunal.py
import pytest
from unittest.mock import MagicMock
from engines.governance.tribunal import QualityTribunal
from models.report import Verdict, Severity

@pytest.mark.asyncio
async def test_tier1_rejects_todo(sample_code):
    """Tier 1 should immediately reject code with TODOs."""
    tribunal = QualityTribunal()
    result = await tribunal.run_audit(sample_code, project="test-proj")
    
    assert result.verdict == Verdict.REJECTED
    assert result.tier_reached == 1
    assert any("TODO" in issue.message for issue in result.issues)

@pytest.mark.asyncio
async def test_tier2_passes_clean_code(clean_code, mock_rae_api):
    """Tier 2 should pass clean code with local LLM consensus."""
    # Mocking Tier 2 Response from A2A Bridge
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "payload": {
            "interaction_data": {
                "verdict": "PASSED",
                "score": 0.95,
                "reasoning": "Clean, typed code with docstrings."
            }
        }
    }
    mock_rae_api.return_value = mock_response
    
    tribunal = QualityTribunal()
    result = await tribunal.run_audit(clean_code, project="test-proj", importance="medium")
    
    assert result.verdict == Verdict.PASSED
    assert result.tier_reached == 2
    assert result.score == 0.95

@pytest.mark.asyncio
async def test_tier3_escalation_for_critical(clean_code, mock_rae_api):
    """Critical code should escalate through all tiers to Tier 3."""
    # Mocking Responses for Tier 2 and Tier 3
    t2_resp = MagicMock()
    t2_resp.status_code = 200
    t2_resp.json.return_value = {"payload": {"interaction_data": {"verdict": "PASSED", "score": 0.8, "reasoning": "Local OK"}}}
    
    t3_resp = MagicMock()
    t3_resp.status_code = 200
    t3_resp.json.return_value = {"payload": {"interaction_data": {"verdict": "PASSED", "score": 1.0, "reasoning": "Supreme Court Approved"}}}
    
    # Mocking multiple POST calls
    mock_rae_api.side_effect = [t2_resp, t2_resp, t3_resp] # Guidelines retrieval + T2 + T3
    
    tribunal = QualityTribunal()
    result = await tribunal.run_audit(clean_code, project="test-proj", importance="critical")
    
    assert result.verdict == Verdict.PASSED
    assert result.tier_reached == 3
    assert "Supreme Court" in result.reasoning
