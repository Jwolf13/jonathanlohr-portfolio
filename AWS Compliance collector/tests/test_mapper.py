"""
Unit tests for src/mapper/engine.py - ControlMappingEngine.

Tests:
  - assess_all_controls() assesses all controls from evidence
  - PASS status when all evidence passed
  - FAIL status when any evidence failed
  - PARTIAL when mixed results
  - NOT_ASSESSED when no evidence
  - generate_posture() calculates compliance metrics
  - remediation_priority scoring logic
"""

import pytest
from src.mapper.engine import ControlMappingEngine
from src.models import (
    ScanResult,
    ControlAssessment,
    ControlStatus,
    EvidenceItem,
    CollectorResult,
)


class TestControlMappingEngine:
    """Test ControlMappingEngine functionality."""
    
    def test_assess_all_controls_returns_assessments(self, sample_scan_result):
        """Test that assess_all_controls() returns ControlAssessment list."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        assert isinstance(assessments, list)
        assert len(assessments) > 0
        assert all(isinstance(a, ControlAssessment) for a in assessments)
    
    def test_assess_all_controls_creates_one_per_catalog_control(self, sample_scan_result):
        """Test that one assessment is created per control in catalog."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # Catalog now has 24 controls across 8 families
        from src.mapper.control_catalog import NIST_CONTROL_CATALOG
        assert len(assessments) == len(NIST_CONTROL_CATALOG)
        
        control_ids = {a.control_id for a in assessments}
        assert "AC-2" in control_ids
        assert "AC-3" in control_ids
        assert "SC-7" in control_ids
        assert "SI-4" in control_ids
    
    def test_assess_control_fail_when_any_evidence_failed(self, sample_scan_result):
        """Test that control status is FAIL when any evidence failed."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # AC-2 has one FAILED finding (root MFA)
        ac2 = next(a for a in assessments if a.control_id == "AC-2")
        
        assert ac2.status == ControlStatus.FAIL
        assert ac2.failed_findings > 0
    
    def test_assess_control_pass_when_all_evidence_passed(self, sample_scan_result):
        """Test that control status is PASS when all evidence passed."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # AU-2 has only PASSED findings
        au2 = next(a for a in assessments if a.control_id == "AU-2")
        
        assert au2.status == ControlStatus.PASS
        assert au2.failed_findings == 0
        assert au2.passed_findings > 0
    
    def test_assess_control_partial_when_mixed_evidence(self, sample_scan_result):
        """Test that control status is PARTIAL with mixed passed/failed."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # SC-7 has mixed evidence (public bucket failed, but other checks may pass)
        sc7 = next(a for a in assessments if a.control_id == "SC-7")
        
        # SC-7 should either be PARTIAL or FAIL based on evidence
        assert sc7.status in [ControlStatus.PARTIAL, ControlStatus.FAIL]
    
    def test_assess_control_not_assessed_when_no_evidence(self, sample_scan_result):
        """Test that control status is NOT_ASSESSED with no evidence."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # CM-2 has no evidence in sample data
        cm2 = next((a for a in assessments if a.control_id == "CM-2"), None)
        
        if cm2:  # Control exists in catalog
            assert cm2.status == ControlStatus.NOT_ASSESSED
            assert cm2.total_findings == 0
    
    def test_assess_control_highest_severity_critical(self, sample_scan_result):
        """Test that highest_severity is correctly identified."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # AC-2 has CRITICAL severity finding
        ac2 = next(a for a in assessments if a.control_id == "AC-2")
        
        assert ac2.highest_severity == "CRITICAL"
    
    def test_assess_control_remediation_priority_fail(self, sample_scan_result):
        """Test that remediation_priority is high for FAIL status."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # AC-2 has FAIL status
        ac2 = next(a for a in assessments if a.control_id == "AC-2")
        
        # Priority should be > 5 for FAIL with CRITICAL severity
        assert ac2.remediation_priority > 5
    
    def test_assess_control_remediation_priority_pass(self, sample_scan_result):
        """Test that remediation_priority is low for PASS status."""
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # AU-2 has PASS status
        au2 = next(a for a in assessments if a.control_id == "AU-2")
        
        # Priority should be low for PASS
        assert au2.remediation_priority <= 2
    
    def test_generate_posture_calculates_compliance_percentage(self, sample_assessments):
        """Test that generate_posture() calculates compliance percentage."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        # With our sample data, should have some passed controls
        assert posture.compliance_percentage >= 0.0
        assert posture.compliance_percentage <= 100.0
        
        # Verify percentage calculation: passed / applicable * 100
        expected_percentage = (posture.passed / posture.applicable_controls * 100) if posture.applicable_controls > 0 else 0
        assert posture.compliance_percentage == round(expected_percentage, 2)
    
    def test_generate_posture_counts_statuses(self, sample_assessments):
        """Test that generate_posture() counts control statuses correctly."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        # Verify counts
        assert posture.passed == sum(1 for a in sample_assessments if a.status == ControlStatus.PASS)
        assert posture.failed == sum(1 for a in sample_assessments if a.status == ControlStatus.FAIL)
        assert posture.partial == sum(1 for a in sample_assessments if a.status == ControlStatus.PARTIAL)
        assert posture.not_assessed == sum(1 for a in sample_assessments if a.status == ControlStatus.NOT_ASSESSED)
    
    def test_generate_posture_calculates_family_breakdown(self, sample_assessments):
        """Test that generate_posture() breaks down by family."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        assert "AC" in posture.by_family
        assert "SC" in posture.by_family
        assert "IA" in posture.by_family
        
        # Verify AC family has correct counts
        ac_family = posture.by_family["AC"]
        assert "total" in ac_family
        assert "passed" in ac_family
        assert "failed" in ac_family
        assert "partial" in ac_family
    
    def test_generate_posture_includes_top_failures(self, sample_assessments):
        """Test that generate_posture() includes top failures."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        # Should have some failures
        assert len(posture.top_failures) > 0
        
        # Each failure should have required fields
        for failure in posture.top_failures:
            assert "control_id" in failure
            assert "control_title" in failure
            assert "status" in failure
            assert "remediation_priority" in failure
    
    def test_generate_posture_limits_failures_to_ten(self, sample_assessments):
        """Test that top_failures list is limited to 10 items."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        assert len(posture.top_failures) <= 10
    
    def test_generate_posture_empty_assessments(self):
        """Test that generate_posture() handles empty assessment list."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture([])
        
        assert posture.total_controls == 0
        assert posture.compliance_percentage == 0.0


class TestCP9Control:
    """Tests for the CP-9 (System Backup) control added in Exercise 2."""

    def _make_scan_with_cp9(self, status: str, severity: str) -> ScanResult:
        """Helper: build a minimal ScanResult with one CP-9 evidence item."""
        scan = ScanResult(
            scan_id="test-scan-cp9",
            scan_start="2024-01-15T10:00:00Z",
            account_id="123456789012",
            region="us-east-1",
        )
        scan.collector_results["config"] = CollectorResult(
            source="config",
            status="SUCCESS",
            evidence_items=[
                EvidenceItem(
                    source="config",
                    finding_id="config-rds-backup-enabled",
                    title="Config: rds-backup-enabled",
                    status=status,
                    severity=severity,
                    resource_type="AWS::RDS::DBInstance",
                    resource_id="my-db",
                    timestamp="2024-01-15T10:00:00Z",
                    control_ids=["CP-9"],
                )
            ],
            raw_findings_count=1,
        )
        scan.finalize()
        return scan

    def test_cp9_exists_in_catalog(self):
        """CP-9 must be present in the control catalog."""
        from src.mapper.control_catalog import NIST_CONTROL_CATALOG
        assert "CP-9" in NIST_CONTROL_CATALOG
        assert NIST_CONTROL_CATALOG["CP-9"]["family"] == "CP"

    def test_cp9_in_fedramp_moderate_baseline(self):
        """CP-9 applies to FedRAMP Moderate (our primary target market)."""
        from src.mapper.control_catalog import NIST_CONTROL_CATALOG
        assert "MODERATE" in NIST_CONTROL_CATALOG["CP-9"]["fedramp_baselines"]

    def test_cp9_assessed_as_fail_when_backup_missing(self):
        """CP-9 should be FAIL when backup evidence is FAILED."""
        engine = ControlMappingEngine()
        scan = self._make_scan_with_cp9(status="FAILED", severity="HIGH")
        assessments = engine.assess_all_controls(scan)
        cp9 = next(a for a in assessments if a.control_id == "CP-9")
        assert cp9.status == ControlStatus.FAIL
        assert cp9.failed_findings > 0

    def test_cp9_assessed_as_pass_when_backup_configured(self):
        """CP-9 should be PASS when backup evidence is PASSED."""
        engine = ControlMappingEngine()
        scan = self._make_scan_with_cp9(status="PASSED", severity="INFORMATIONAL")
        assessments = engine.assess_all_controls(scan)
        cp9 = next(a for a in assessments if a.control_id == "CP-9")
        assert cp9.status == ControlStatus.PASS
        assert cp9.failed_findings == 0

    def test_cp9_config_rules_mapped(self):
        """Config collector must map backup rules to CP-9."""
        from src.collector.config_collector import ConfigCollector
        backup_rules = [
            rule for rule, controls in ConfigCollector.RULE_TO_NIST_MAP.items()
            if "CP-9" in controls
        ]
        assert len(backup_rules) > 0, "No Config rules mapped to CP-9"


class TestRemediationPriority:
    """Test remediation priority calculation."""
    
    def test_priority_fail_critical(self):
        """Test that FAIL with CRITICAL severity gets high priority."""
        engine = ControlMappingEngine()
        priority = engine._calculate_priority(ControlStatus.FAIL, "CRITICAL", 1)
        
        assert priority > 8
    
    def test_priority_partial_high(self):
        """Test that PARTIAL with HIGH severity gets moderate priority."""
        engine = ControlMappingEngine()
        priority = engine._calculate_priority(ControlStatus.PARTIAL, "HIGH", 1)
        
        assert priority >= 5
        assert priority <= 7
    
    def test_priority_pass_low(self):
        """Test that PASS status gets low priority."""
        engine = ControlMappingEngine()
        priority = engine._calculate_priority(ControlStatus.PASS, "MEDIUM", 1)
        
        # PASS gets base score of 2, no severity bump for MEDIUM
        assert priority == 2
    
    def test_priority_not_assessed_minimum(self):
        """Test that NOT_ASSESSED gets minimum priority."""
        engine = ControlMappingEngine()
        priority = engine._calculate_priority(ControlStatus.NOT_ASSESSED, "INFORMATIONAL", 1)
        
        # NOT_ASSESSED gets base score of 1
        assert priority == 1
    
    def test_priority_clamped_to_range(self):
        """Test that priority is always between 1 and 10."""
        engine = ControlMappingEngine()
        
        for status in [ControlStatus.FAIL, ControlStatus.PARTIAL, ControlStatus.PASS, ControlStatus.NOT_ASSESSED]:
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]:
                priority = engine._calculate_priority(status, severity, 100)
                assert 1 <= priority <= 10
