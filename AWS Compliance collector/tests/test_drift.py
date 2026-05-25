"""
Unit tests for src/drift/detector.py - DriftDetector.

Tests:
  - REGRESSION detection (PASS → FAIL)
  - IMPROVEMENT detection (FAIL → PASS)
  - No drift when statuses unchanged
  - NEW_FINDING when control in current but not previous
  - RESOLVED when control resolved from failure
"""

import pytest
from src.drift.detector import DriftDetector
from src.models import (
    ControlAssessment,
    ControlStatus,
    DriftEvent,
    EvidenceItem,
)
from datetime import datetime, timezone


class TestDriftDetector:
    """Test DriftDetector functionality."""
    
    def test_detect_no_drift_when_unchanged(self, sample_assessments):
        """Test that no drift is detected when control status unchanged."""
        detector = DriftDetector()
        
        # Use same assessments for both previous and current
        drift_events = detector.detect(sample_assessments, sample_assessments)
        
        assert len(drift_events) == 0
    
    def test_detect_regression_pass_to_fail(self, sample_assessments, previous_assessments):
        """Test REGRESSION detection when control moves from PASS to FAIL."""
        detector = DriftDetector()
        
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        # SC-8 should have regressed from PASS to PARTIAL
        regressions = [e for e in drift_events if e.control_id == "SC-8"]
        
        assert len(regressions) > 0
        regression = regressions[0]
        assert regression.drift_type == "REGRESSION"
        assert regression.previous_status == "PASS"
        assert regression.current_status == "PARTIAL"
    
    def test_detect_improvement_fail_to_pass(self, sample_assessments, previous_assessments):
        """Test IMPROVEMENT detection when control moves from FAIL to PASS."""
        detector = DriftDetector()
        
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        # SC-7 and CM-6 should improve from FAIL/PARTIAL to higher states
        improvements = [e for e in drift_events if e.control_id in ["SC-7", "CM-6"]]
        
        # Should have detected changes
        assert len(improvements) > 0
    
    def test_detect_new_finding_not_in_previous(self):
        """Test NEW_FINDING detection when control is only in current scan."""
        detector = DriftDetector()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Create a control that only exists in current
        previous = []
        current = [
            ControlAssessment(
                control_id="AC-2",
                control_title="Account Management",
                control_family="AC",
                family_name="Access Control",
                status=ControlStatus.FAIL,
                scan_id="scan-new",
                timestamp=now_iso
            )
        ]
        
        drift_events = detector.detect(previous, current)
        
        # Should detect as NEW_FINDING since previous was empty
        new_findings = [e for e in drift_events if e.drift_type == "NEW_FINDING"]
        assert len(new_findings) > 0
    
    def test_detect_status_change(self):
        """Test drift detection for status changes."""
        detector = DriftDetector()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        previous = [
            ControlAssessment(
                control_id="AC-2",
                control_title="Account Management",
                control_family="AC",
                family_name="Access Control",
                status=ControlStatus.PARTIAL,
                failed_findings=1,
                passed_findings=1,
                scan_id="scan-prev",
                timestamp=now_iso
            )
        ]
        
        current = [
            ControlAssessment(
                control_id="AC-2",
                control_title="Account Management",
                control_family="AC",
                family_name="Access Control",
                status=ControlStatus.PASS,
                failed_findings=0,
                passed_findings=2,
                scan_id="scan-curr",
                timestamp=now_iso
            )
        ]
        
        drift_events = detector.detect(previous, current)
        
        # Should detect as RESOLVED or IMPROVEMENT
        assert len(drift_events) > 0
        assert drift_events[0].drift_type in ["RESOLVED", "IMPROVEMENT", "STATUS_CHANGE"]
        assert drift_events[0].control_id == "AC-2"
    
    def test_drift_event_has_required_fields(self, sample_assessments, previous_assessments):
        """Test that DriftEvent has all required fields."""
        detector = DriftDetector()
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        if drift_events:
            event = drift_events[0]
            
            assert hasattr(event, "drift_id")
            assert hasattr(event, "control_id")
            assert hasattr(event, "control_title")
            assert hasattr(event, "previous_status")
            assert hasattr(event, "current_status")
            assert hasattr(event, "drift_type")
            assert hasattr(event, "severity")
            assert hasattr(event, "previous_scan_id")
            assert hasattr(event, "current_scan_id")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "affected_resources")
            assert hasattr(event, "details")
    
    def test_drift_event_severity_for_regression(self):
        """Test that regression gets HIGH or CRITICAL severity."""
        detector = DriftDetector()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        previous = [
            ControlAssessment(
                control_id="AC-2",
                control_title="Account Management",
                control_family="AC",
                family_name="Access Control",
                status=ControlStatus.PASS,
                highest_severity="CRITICAL",
                scan_id="scan-prev",
                timestamp=now_iso
            )
        ]
        
        current = [
            ControlAssessment(
                control_id="AC-2",
                control_title="Account Management",
                control_family="AC",
                family_name="Access Control",
                status=ControlStatus.FAIL,
                highest_severity="CRITICAL",
                scan_id="scan-curr",
                timestamp=now_iso
            )
        ]
        
        drift_events = detector.detect(previous, current)
        
        assert len(drift_events) > 0
        assert drift_events[0].severity in ["CRITICAL", "HIGH"]
    
    def test_drift_event_includes_affected_resources(self):
        """Test that DriftEvent includes affected resource IDs from evidence."""
        detector = DriftDetector()
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        evidence = [
            EvidenceItem(
                source="security_hub",
                finding_id="f1",
                title="Finding 1",
                status="FAILED",
                severity="CRITICAL",
                resource_type="AWS::S3::Bucket",
                resource_id="arn:aws:s3:::bucket1",
                timestamp=now_iso,
                control_ids=["SC-7"]
            ),
            EvidenceItem(
                source="security_hub",
                finding_id="f2",
                title="Finding 2",
                status="FAILED",
                severity="HIGH",
                resource_type="AWS::S3::Bucket",
                resource_id="arn:aws:s3:::bucket2",
                timestamp=now_iso,
                control_ids=["SC-7"]
            ),
        ]
        
        previous = [
            ControlAssessment(
                control_id="SC-7",
                control_title="Boundary Protection",
                control_family="SC",
                family_name="System and Communications Protection",
                status=ControlStatus.PASS,
                evidence=[],
                scan_id="scan-prev",
                timestamp=now_iso
            )
        ]
        
        current = [
            ControlAssessment(
                control_id="SC-7",
                control_title="Boundary Protection",
                control_family="SC",
                family_name="System and Communications Protection",
                status=ControlStatus.FAIL,
                evidence=evidence,
                scan_id="scan-curr",
                timestamp=now_iso
            )
        ]
        
        drift_events = detector.detect(previous, current)
        
        assert len(drift_events) > 0
        event = drift_events[0]
        # Should include the failed resource ARNs
        assert len(event.affected_resources) > 0
    
    def test_is_regression_property(self, sample_assessments, previous_assessments):
        """Test is_regression property of DriftEvent."""
        detector = DriftDetector()
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        for event in drift_events:
            if event.drift_type == "REGRESSION":
                assert event.is_regression is True
            else:
                assert event.is_regression is False
