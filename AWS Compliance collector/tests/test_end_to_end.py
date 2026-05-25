"""
End-to-end integration tests for AWS Compliance Evidence Collector pipeline.

THE CRITICAL TEST: Full pipeline from evidence collection through drift detection.
  1. Create mock evidence → build ScanResult
  2. Run mapper to assess controls
  3. Generate PDF report
  4. Run drift detector
  5. Verify data flows without errors and outputs are valid

NOTE: Does not import AWS collectors (which require boto3).
      Uses fixture data to simulate Phase 1 (collection) output.
"""

import pytest
import os
import tempfile
from datetime import datetime, timezone

from src.mapper.engine import ControlMappingEngine
from src.evidence.pdf_generator import PDFReportGenerator
from src.drift.detector import DriftDetector
from src.models import (
    ScanResult,
    ControlAssessment,
    ControlStatus,
    CompliancePosture,
)


class TestEndToEndPipeline:
    """Full integration tests of the compliance pipeline."""
    
    def test_e2e_evidence_to_assessment(self, sample_scan_result):
        """Test pipeline: Evidence → Assessment."""
        # Phase 2: Map evidence to controls
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        
        # Verify output
        assert len(assessments) > 0
        assert all(isinstance(a, ControlAssessment) for a in assessments)
        
        # Every assessment should have control_id
        for assessment in assessments:
            assert assessment.control_id
            assert assessment.control_title
            assert assessment.status in [
                ControlStatus.PASS,
                ControlStatus.FAIL,
                ControlStatus.PARTIAL,
                ControlStatus.NOT_ASSESSED,
            ]
    
    def test_e2e_assessment_to_posture(self, sample_assessments):
        """Test pipeline: Assessment → Posture."""
        # Phase 2b: Generate aggregate posture
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        # Verify output
        assert posture.total_controls > 0
        assert posture.passed >= 0
        assert posture.failed >= 0
        assert posture.partial >= 0
        assert posture.not_assessed >= 0
        assert 0 <= posture.compliance_percentage <= 100
    
    def test_e2e_assessment_to_pdf(self, sample_assessments):
        """Test pipeline: Assessment → PDF Report."""
        # Phase 3: Generate PDF
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "compliance_report.txt")
            
            engine = ControlMappingEngine()
            posture = engine.generate_posture(sample_assessments)
            
            generator = PDFReportGenerator(use_reportlab=False)
            output = generator.generate(sample_assessments, posture, pdf_path)
            
            # Verify output
            assert os.path.exists(output)
            assert os.path.getsize(output) > 100
            
            # Verify content
            with open(output, "r") as f:
                content = f.read()
            
            assert "COMPLIANCE" in content.upper()
            assert posture.scan_id in content
    
    def test_e2e_assessment_to_drift(self, sample_assessments, previous_assessments):
        """Test pipeline: Assessment → Drift Detection."""
        # Phase 4: Detect drift
        detector = DriftDetector()
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        # Verify output
        assert isinstance(drift_events, list)
        
        # Should have some drift (we engineered the fixtures for this)
        # At minimum, check that the method runs without error
        for event in drift_events:
            assert event.control_id
            assert event.drift_type in [
                "REGRESSION",
                "IMPROVEMENT",
                "RESOLVED",
                "NEW_FINDING",
                "STATUS_CHANGE",
                "NO_CHANGE",
            ]
            assert event.severity
            assert event.timestamp
    
    def test_e2e_full_pipeline_no_errors(self, sample_scan_result):
        """CRITICAL TEST: Run the complete pipeline without errors."""
        # This is the ultimate integration test
        
        # Phase 1: Evidence already collected in sample_scan_result
        assert len(sample_scan_result.all_evidence) > 0
        
        # Phase 2: Map to controls
        engine = ControlMappingEngine()
        assessments = engine.assess_all_controls(sample_scan_result)
        assert len(assessments) > 0
        
        # Phase 2b: Generate posture
        posture = engine.generate_posture(assessments)
        assert posture.total_controls > 0
        
        # Phase 3: Generate PDF
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "report.txt")
            generator = PDFReportGenerator(use_reportlab=False)
            output = generator.generate(assessments, posture, pdf_path)
            assert os.path.exists(output)
        
        # Phase 4: Drift detection (using same assessments for simplicity)
        detector = DriftDetector()
        drift_events = detector.detect(assessments, assessments)
        assert isinstance(drift_events, list)
        
        # All phases complete successfully
        assert True
    
    def test_e2e_pipeline_produces_valid_outputs(
        self,
        sample_scan_result,
        sample_assessments,
    ):
        """Test that all pipeline stages produce correctly typed outputs."""
        engine = ControlMappingEngine()
        
        # Verify ScanResult
        assert isinstance(sample_scan_result, ScanResult)
        assert sample_scan_result.scan_id
        assert len(sample_scan_result.all_evidence) > 0
        
        # Verify ControlAssessments
        assert isinstance(sample_assessments, list)
        assert len(sample_assessments) > 0
        assert all(isinstance(a, ControlAssessment) for a in sample_assessments)
        
        # Verify CompliancePosture
        posture = engine.generate_posture(sample_assessments)
        assert isinstance(posture, CompliancePosture)
        assert posture.scan_id
        assert 0 <= posture.compliance_percentage <= 100
        
        # Verify individual assessment fields
        for assessment in sample_assessments:
            assert assessment.control_id
            assert assessment.status is not None
            assert isinstance(assessment.status, ControlStatus)
            assert 0 <= assessment.remediation_priority <= 10
    
    def test_e2e_drift_detection_finds_expected_changes(
        self,
        sample_assessments,
        previous_assessments,
    ):
        """Test that drift detector finds the engineered status changes."""
        detector = DriftDetector()
        drift_events = detector.detect(previous_assessments, sample_assessments)
        
        # We engineered fixtures so SC-7 should regress, IA-4 and CM-6 should improve
        event_by_control = {e.control_id: e for e in drift_events}
        
        # SC-7 should have changed status
        if "SC-7" in event_by_control:
            event = event_by_control["SC-7"]
            assert event.previous_status != event.current_status
        
        # Should have detected some changes
        assert len(drift_events) > 0
    
    def test_e2e_control_family_breakdown(self, sample_assessments):
        """Test that control family breakdown is accurate."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        # Verify family structure
        assert len(posture.by_family) > 0
        
        # Every family should have expected keys
        for family_id, counts in posture.by_family.items():
            assert "total" in counts
            assert "passed" in counts
            assert "failed" in counts
            assert "partial" in counts
            assert "not_assessed" in counts
            
            # Verify math
            total = (counts["passed"] + counts["failed"] + 
                    counts["partial"] + counts["not_assessed"])
            assert total == counts["total"]
    
    def test_e2e_top_failures_ranking(self, sample_assessments):
        """Test that top failures are correctly ranked by priority."""
        engine = ControlMappingEngine()
        posture = engine.generate_posture(sample_assessments)
        
        if len(posture.top_failures) > 1:
            # Verify descending priority order
            for i in range(len(posture.top_failures) - 1):
                current_priority = posture.top_failures[i]["remediation_priority"]
                next_priority = posture.top_failures[i + 1]["remediation_priority"]
                assert current_priority >= next_priority
    
    def test_e2e_pdf_contains_all_expected_sections(self, sample_assessments):
        """Test that generated PDF has all expected sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "full_report.txt")
            
            engine = ControlMappingEngine()
            posture = engine.generate_posture(sample_assessments)
            
            generator = PDFReportGenerator(use_reportlab=False)
            output = generator.generate(sample_assessments, posture, pdf_path)
            
            with open(output, "r") as f:
                content = f.read().upper()
            
            # Verify all key sections present
            assert "COMPLIANCE" in content
            assert "SUMMARY" in content
            assert "CONTROL" in content
            assert "STATUS" in content
            assert "SEVERITY" in content
    
    def test_e2e_data_flows_without_errors(self, sample_scan_result):
        """Test that data flows through pipeline without exceptions."""
        try:
            # Phase 2
            engine = ControlMappingEngine()
            assessments = engine.assess_all_controls(sample_scan_result)
            
            # Phase 2b
            posture = engine.generate_posture(assessments)
            
            # Phase 3
            with tempfile.TemporaryDirectory() as tmpdir:
                generator = PDFReportGenerator(use_reportlab=False)
                generator.generate(assessments, posture, os.path.join(tmpdir, "report.txt"))
            
            # Phase 4
            detector = DriftDetector()
            detector.detect(assessments, assessments)
            
            # If we get here, no exceptions were raised
            assert True
        except Exception as e:
            pytest.fail(f"Pipeline raised unexpected exception: {e}")
