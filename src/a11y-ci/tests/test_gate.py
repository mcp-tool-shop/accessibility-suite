"""Tests for the gate module."""

from pathlib import Path

import pytest

from a11y_ci.allowlist import Allowlist
from a11y_ci.gate import gate
from a11y_ci.scorecard import Scorecard

FIX = Path(__file__).parent / "fixtures"


class TestGateBasic:
    """Basic gate tests without baseline."""

    def test_gate_passes_without_serious(self):
        """Gate passes when no findings at/above threshold."""
        current = Scorecard.load(str(FIX / "current_ok.json"))
        result = gate(current=current, baseline=None, fail_on="serious", allowlist=None)
        assert result.ok
        assert result.current_blocking_ids == []

    def test_gate_fails_on_serious_in_current(self):
        """Gate fails when current has findings at/above threshold."""
        current = Scorecard.load(str(FIX / "current_fail.json"))
        result = gate(current=current, baseline=None, fail_on="serious", allowlist=None)
        assert not result.ok
        assert "Current run has" in " ".join(result.reasons)
        assert "CLI.COLOR.ONLY" in result.current_blocking_ids

    def test_gate_passes_when_below_threshold(self):
        """Gate passes when findings are below the threshold."""
        current = Scorecard.load(str(FIX / "current_fail.json"))
        # fail_on=critical means serious is allowed
        result = gate(current=current, baseline=None, fail_on="critical", allowlist=None)
        assert result.ok


class TestGateWithBaseline:
    """Gate tests with baseline comparison."""

    def test_gate_regression_vs_baseline_counts_and_ids(self):
        """Gate fails on regression from baseline."""
        baseline = Scorecard.load(str(FIX / "baseline_ok.json"))
        current = Scorecard.load(str(FIX / "current_regresses.json"))
        result = gate(current=current, baseline=baseline, fail_on="serious", allowlist=None)
        assert not result.ok
        assert result.new_blocking_ids  # new serious+ IDs
        assert "CLI.COLOR.ONLY" in result.new_blocking_ids
        assert "CLI.ERROR.STRUCTURE" in result.new_blocking_ids

    def test_gate_no_regression_when_same(self):
        """Gate passes when current matches baseline."""
        baseline = Scorecard.load(str(FIX / "baseline_ok.json"))
        current = Scorecard.load(str(FIX / "current_ok.json"))
        result = gate(current=current, baseline=baseline, fail_on="serious", allowlist=None)
        assert result.ok


class TestGateWithAllowlist:
    """Gate tests with allowlist."""

    def test_allowlist_suppresses_ids(self):
        """Allowlist suppresses matching finding IDs."""
        baseline = Scorecard.load(str(FIX / "baseline_ok.json"))
        current = Scorecard.load(str(FIX / "current_fail.json"))
        allow = Allowlist.load(str(FIX / "allowlist_ok.json"))

        result = gate(current=current, baseline=baseline, fail_on="serious", allowlist=allow)
        # suppression should remove the only serious finding, leaving gate pass
        assert result.ok

    def test_expired_allowlist_is_reported_as_reason(self):
        """Expired allowlist entries cause gate failure."""
        current = Scorecard.load(str(FIX / "current_fail.json"))
        allow = Allowlist.load(str(FIX / "allowlist_expired.json"))
        result = gate(current=current, baseline=None, fail_on="serious", allowlist=allow)
        # Even though it's suppressed, expired allowlist should create a reason
        assert not result.ok
        assert any("expired" in r.lower() for r in result.reasons)


class TestScorecardLoading:
    """Tests for scorecard loading and counts."""

    def test_scorecard_loads_findings(self):
        """Scorecard correctly loads findings."""
        sc = Scorecard.load(str(FIX / "current_ok.json"))
        assert len(sc.findings) == 1
        assert sc.findings[0]["rule_id"] == "CLI.LINE.LENGTH"

    def test_scorecard_counts_from_summary(self):
        """Scorecard uses summary when present."""
        sc = Scorecard.load(str(FIX / "baseline_ok.json"))
        counts = sc.counts()
        assert counts["moderate"] == 1
        assert counts["serious"] == 0

    def test_scorecard_counts_from_findings(self):
        """Scorecard computes counts from findings when no summary."""
        sc = Scorecard.load(str(FIX / "current_regresses.json"))
        counts = sc.counts()
        assert counts["serious"] == 2

    def test_ids_at_or_above(self):
        """ids_at_or_above returns correct finding IDs."""
        sc = Scorecard.load(str(FIX / "current_regresses.json"))
        ids = sc.ids_at_or_above("serious")
        assert "CLI.COLOR.ONLY" in ids
        assert "CLI.ERROR.STRUCTURE" in ids


class TestAllowlistLoading:
    """Tests for allowlist loading and validation."""

    def test_allowlist_loads_entries(self):
        """Allowlist correctly loads entries."""
        allow = Allowlist.load(str(FIX / "allowlist_ok.json"))
        assert len(allow.entries) == 1
        assert allow.entries[0].finding_id == "CLI.COLOR.ONLY"
        assert allow.entries[0].expires == "2026-12-31"

    def test_allowlist_suppressed_ids(self):
        """suppressed_ids returns correct set."""
        allow = Allowlist.load(str(FIX / "allowlist_ok.json"))
        assert "CLI.COLOR.ONLY" in allow.suppressed_ids()

    def test_allowlist_expired_entries(self):
        """expired_entries detects expired suppressions."""
        allow = Allowlist.load(str(FIX / "allowlist_expired.json"))
        expired = allow.expired_entries()
        assert len(expired) == 1
        assert expired[0].finding_id == "CLI.COLOR.ONLY"
