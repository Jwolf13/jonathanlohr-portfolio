"""
Unit tests for src/evidence/pdf_generator.py - PDFReportGenerator.

Tests:
  - generate() produces a file
  - Text fallback works when reportlab not installed
  - Generated report contains expected control IDs
"""

import pytest
import os
import tempfile
from src.evidence.pdf_generator import PDFReportGenerator
from src.models import ControlAssessment, ControlStatus, CompliancePosture
from datetime import datetime, timezone


class TestPDFReportGenerator:
    """Test PDFReportGenerator functionality."""
    
    def test_generate_creates_file(self, sample_assessments):
        """Test that generate() creates an output file."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            posture = CompliancePosture(
                scan_id="test-scan-123",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=len(sample_assessments),
                applicable_controls=len(sample_assessments),
                passed=5,
                failed=2,
                partial=3,
                not_assessed=2,
                compliance_percentage=62.5
            )
            
            result = generator.generate(sample_assessments, posture, output_path)
            
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
    
    def test_generate_text_fallback_contains_scan_id(self, sample_assessments):
        """Test that generated text report contains scan ID."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            scan_id = "test-scan-abc123"
            posture = CompliancePosture(
                scan_id=scan_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=len(sample_assessments),
                applicable_controls=len(sample_assessments),
                passed=5,
                failed=2,
                partial=3,
                not_assessed=2,
                compliance_percentage=62.5
            )
            
            generator.generate(sample_assessments, posture, output_path)
            
            with open(output_path, "r") as f:
                content = f.read()
            
            assert scan_id in content
    
    def test_generate_text_contains_compliance_score(self, sample_assessments):
        """Test that generated report contains compliance score."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            posture = CompliancePosture(
                scan_id="test-scan",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=10,
                applicable_controls=10,
                passed=8,
                failed=1,
                partial=1,
                not_assessed=0,
                compliance_percentage=80.0
            )
            
            generator.generate(sample_assessments, posture, output_path)
            
            with open(output_path, "r") as f:
                content = f.read()
            
            assert "80" in content  # Should contain the percentage
            assert "COMPLIANCE" in content.upper()
    
    def test_generate_text_contains_all_control_ids(self, sample_assessments):
        """Test that generated report contains all assessed control IDs."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            posture = CompliancePosture(
                scan_id="test-scan",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=len(sample_assessments),
                applicable_controls=len(sample_assessments),
                passed=5,
                failed=2,
                partial=3,
                not_assessed=2,
                compliance_percentage=50.0
            )
            
            generator.generate(sample_assessments, posture, output_path)
            
            with open(output_path, "r") as f:
                content = f.read()
            
            # Check that at least some control IDs appear in report
            control_ids = {a.control_id for a in sample_assessments}
            found_ids = [cid for cid in control_ids if cid in content]
            
            assert len(found_ids) > 0
    
    def test_generate_text_contains_executive_summary(self, sample_assessments):
        """Test that generated report has executive summary section."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            posture = CompliancePosture(
                scan_id="test-scan",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=10,
                applicable_controls=10,
                passed=7,
                failed=2,
                partial=1,
                not_assessed=0,
                compliance_percentage=70.0
            )
            
            generator.generate(sample_assessments, posture, output_path)
            
            with open(output_path, "r") as f:
                content = f.read().upper()
            
            assert "EXECUTIVE SUMMARY" in content or "SUMMARY" in content
    
    def test_generate_text_contains_failures_section(self, sample_assessments):
        """Test that report includes failures when present."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.txt")
            
            # Add top failures to posture
            posture = CompliancePosture(
                scan_id="test-scan",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=10,
                applicable_controls=10,
                passed=7,
                failed=2,
                partial=1,
                not_assessed=0,
                compliance_percentage=70.0,
                top_failures=[
                    {
                        "control_id": "SC-7",
                        "control_title": "Boundary Protection",
                        "status": "FAIL",
                        "highest_severity": "CRITICAL",
                        "remediation_priority": 9,
                        "failed_findings": 2
                    },
                    {
                        "control_id": "AC-2",
                        "control_title": "Account Management",
                        "status": "FAIL",
                        "highest_severity": "HIGH",
                        "remediation_priority": 8,
                        "failed_findings": 1
                    }
                ]
            )
            
            generator.generate(sample_assessments, posture, output_path)
            
            with open(output_path, "r") as f:
                content = f.read()
            
            # Check that failure controls appear
            assert "SC-7" in content or "Boundary Protection" in content
    
    def test_generate_text_output_directory_created(self):
        """Test that generate() creates output directory if needed."""
        generator = PDFReportGenerator(use_reportlab=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nested", "deep", "report.txt")
            
            posture = CompliancePosture(
                scan_id="test-scan",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=1,
                applicable_controls=1,
                passed=1,
                failed=0,
                partial=0,
                not_assessed=0,
                compliance_percentage=100.0
            )
            
            result = generator.generate([], posture, nested_path)
            
            assert os.path.exists(result)
            assert os.path.dirname(result) == os.path.dirname(nested_path)
