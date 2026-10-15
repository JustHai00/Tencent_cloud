"""
test_verdictai.py — Unit tests for VerdictAI.

Covers:
  - JudgeAgent route-deviation logic (refund thresholds, valid reasons, confidence)
  - JudgeAgent no-show logic (grace period, fee waiver, confidence)
  - End-to-end verdicts on both mock disputes
  - Config policy integrity

Run:
    pytest test_verdictai.py -v
"""

import pytest

from agents import JudgeAgent, RiderAdvocate, DriverAdvocate
from config import RYDE_POLICY
from mock_data import SAMPLE_DISPUTES, fare_route_dispute, no_show_dispute


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def judge():
    return JudgeAgent()


@pytest.fixture
def rider_advocate():
    return RiderAdvocate()


@pytest.fixture
def driver_advocate():
    return DriverAdvocate()


# ---------------------------------------------------------------------------
# 1. Route Deviation Tests
# ---------------------------------------------------------------------------
class TestRouteDeviation:
    """Tests for JudgeAgent.check_deviation()."""

    def test_route_deviation_refund(self, judge):
        """Actual distance well above 20% threshold → partial_refund, high confidence."""
        result = judge.check_deviation(actual=18, expected=13)
        assert result["action"] == "partial_refund"
        assert result["confidence"] > 80
        assert result["refund_recommended"] is True

    def test_deviation_exactly_at_threshold(self, judge):
        """Exactly 20% over → NOT above threshold (strictly greater), no refund."""
        result = judge.check_deviation(actual=12, expected=10)  # 20% exactly
        assert result["action"] == "no_action"
        assert result["refund_recommended"] is False

    def test_deviation_just_above_threshold(self, judge):
        """25% over (just above 20%) → refund, confidence at least 75."""
        result = judge.check_deviation(actual=12.5, expected=10)  # 25%
        assert result["action"] == "partial_refund"
        assert result["confidence"] >= 75
        assert result["refund_recommended"] is True

    def test_deviation_no_action_when_under_threshold(self, judge):
        """10% over (under 20% threshold) → no refund."""
        result = judge.check_deviation(actual=11, expected=10)  # 10%
        assert result["action"] == "no_action"
        assert result["refund_recommended"] is False

    def test_deviation_with_valid_reason(self, judge):
        """Even if deviation is huge, a valid reason blocks the refund."""
        result = judge.check_deviation(actual=20, expected=10, reason="road_closure")
        assert result["action"] == "no_action"
        assert result["refund_recommended"] is False

    def test_deviation_with_invalid_reason(self, judge):
        """An unrecognised reason does NOT block the refund."""
        result = judge.check_deviation(actual=20, expected=10, reason="felt_like_it")
        assert result["action"] == "partial_refund"
        assert result["refund_recommended"] is True

    def test_deviation_confidence_capped(self, judge):
        """Confidence should never exceed 95."""
        result = judge.check_deviation(actual=100, expected=10)  # 900% over
        assert result["confidence"] <= 95

    def test_deviation_zero_expected(self, judge):
        """Edge case: expected=0 should not crash."""
        result = judge.check_deviation(actual=5, expected=0)
        assert result["action"] == "no_action"
        assert result["confidence"] == 100


# ---------------------------------------------------------------------------
# 2. No-Show Tests
# ---------------------------------------------------------------------------
class TestNoShow:
    """Tests for JudgeAgent.check_no_show()."""

    def test_no_show_waived_short_wait(self, judge):
        """Driver waited < 5 min → fee waived, confidence >= 70."""
        result = judge.check_no_show(wait_mins=3)
        assert result["action"] == "waive_fee"
        assert result["fee_waived"] is True
        assert result["confidence"] >= 70

    def test_no_show_waived_rider_nearby(self, judge):
        """Driver waited >= 5 min but rider was nearby → fee still waived."""
        result = judge.check_no_show(wait_mins=6, rider_nearby=True)
        assert result["action"] == "waive_fee"
        assert result["fee_waived"] is True

    def test_no_show_upheld_long_wait(self, judge):
        """Driver waited >= 5 min and rider not nearby → fee upheld."""
        result = judge.check_no_show(wait_mins=7, rider_nearby=False)
        assert result["action"] == "uphold_fee"
        assert result["fee_waived"] is False

    def test_no_show_confidence_capped(self, judge):
        """Confidence should never exceed 95."""
        result = judge.check_no_show(wait_mins=0)
        assert result["confidence"] <= 95


# ---------------------------------------------------------------------------
# 3. End-to-End Verdict on Mock Disputes
# ---------------------------------------------------------------------------
class TestEndToEnd:
    """Full pipeline: advocates build cases → judge delivers verdict."""

    def test_fare_route_dispute_verdict(self, judge, rider_advocate, driver_advocate):
        """D001: 17.8 km actual vs 13.2 km expected → rider claim upheld."""
        rider_case = rider_advocate.build_case(fare_route_dispute)
        driver_case = driver_advocate.build_defence(fare_route_dispute)

        verdict = judge.deliver_verdict(fare_route_dispute, rider_case, driver_case)

        assert verdict["verdict"] == "UPHOLD_RIDER_CLAIM"
        assert verdict["policy_applied"] == "Route Deviation Rule"
        assert verdict["refund_amount"] > 0
        assert verdict["confidence"] > 70
        assert verdict["currency"] == "CNY"

    def test_no_show_dispute_verdict(self, judge, rider_advocate, driver_advocate):
        """D002: driver waited only 5 min, rider nearby → fee waived."""
        rider_case = rider_advocate.build_case(no_show_dispute)
        driver_case = driver_advocate.build_defence(no_show_dispute)

        verdict = judge.deliver_verdict(no_show_dispute, rider_case, driver_case)

        assert verdict["verdict"] == "UPHOLD_RIDER_CLAIM"
        assert verdict["policy_applied"] == "No-Show Cancellation Rule"
        assert verdict["refund_amount"] > 0
        assert verdict["currency"] == "CNY"

    def test_advocates_produce_non_empty_cases(self, rider_advocate, driver_advocate):
        """Advocate outputs must be non-empty strings."""
        for d in SAMPLE_DISPUTES:
            rc = rider_advocate.build_case(d)
            dc = driver_advocate.build_defence(d)
            assert isinstance(rc, str) and len(rc) > 10
            assert isinstance(dc, str) and len(dc) > 10


# ---------------------------------------------------------------------------
# 4. Config Integrity Tests
# ---------------------------------------------------------------------------
class TestConfig:
    """Ensure config values are sensible and internally consistent."""

    def test_route_deviation_threshold_is_20(self):
        assert RYDE_POLICY["route_deviation"]["threshold_pct"] == 20

    def test_route_deviation_action_is_refund(self):
        assert RYDE_POLICY["route_deviation"]["action"] == "partial_refund"

    def test_no_show_grace_period_is_5(self):
        assert RYDE_POLICY["no_show"]["grace_period_mins"] == 5

    def test_no_show_action_is_waive(self):
        assert RYDE_POLICY["no_show"]["action"] == "waive_fee"

    def test_escalation_threshold_in_range(self):
        assert 0 < RYDE_POLICY["escalation_threshold"] <= 100

    def test_valid_reasons_not_empty(self):
        assert len(RYDE_POLICY["route_deviation"]["valid_reasons"]) > 0
