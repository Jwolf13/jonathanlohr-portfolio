"""
Unit tests for src/models.py data structures and utilities.

Tests:
  - EvidenceItem.to_dict() and from_dict() round-trip serialization
  - ScanResult.finalize() aggregation logic
  - ScanResult.evidence_by_control grouping property
  - generate_scan_id() format and uniqueness
"""

import pytest
from datetime import datetime, timezone
from src.models import (
    EvidenceItem,
    ScanResult,
    ControlAssessment,
    ControlStatus,
    CollectorResult,
    generate_scan_id,
    generate_drift_id,
)


class TestEvidenceItem:
    """Test EvidenceItem serialization and deserialization."""
    
    def test_to_dict_serializes_all_fields(self):
        """Test that to_dict() includes all fields."""
        now_iso = datetime.now(timezone.utc).isoformat()
        item = EvidenceItem(
            source="security_hub",
            finding_id="finding-123",
            title="Test Finding",
            status="PASSED",
            severity="HIGH",
            resource_type="AWS::S3::Bucket",
            resource_id="arn:aws:s3:::test-bucket",
            timestamp=now_iso,
            remediation="Fix the issue",
            control_ids=["AC-2", "SC-7"],
            raw_data={"key": "value"}
        )
        
        d = item.to_dict()
        
        assert d["source"] == "security_hub"
        assert d["finding_id"] == "finding-123"
        assert d["title"] == "Test Finding"
        assert d["status"] == "PASSED"
        assert d["severity"] == "HIGH"
        assert d["resource_type"] == "AWS::S3::Bucket"
        assert d["resource_id"] == "arn:aws:s3:::test-bucket"
        assert d["timestamp"] == now_iso
        assert d["remediation"] == "Fix the issue"
        assert d["control_ids"] == ["AC-2", "SC-7"]
        assert d["raw_data"] == {"key": "value"}
    
    def test_from_dict_reconstructs_object(self):
        """Test that from_dict() reconstructs EvidenceItem correctly."""
        now_iso = datetime.now(timezone.utc).isoformat()
        data = {
            "source": "config",
            "finding_id": "config-rule-123",
            "title": "Config Rule Evaluation",
            "status": "FAILED",
            "severity": "MEDIUM",
            "resource_type": "AWS::EC2::SecurityGroup",
            "resource_id": "arn:aws:ec2:us-east-1:123456789012:security-group/sg-123",
            "timestamp": now_iso,
            "remediation": "Update security group rules",
            "control_ids": ["SC-7"],
            "raw_data": {"compliance_type": "NON_COMPLIANT"}
        }
        
        item = EvidenceItem.from_dict(data)
        
        assert item.source == "config"
        assert item.finding_id == "config-rule-123"
        assert item.title == "Config Rule Evaluation"
        assert item.status == "FAILED"
        assert item.severity == "MEDIUM"
        assert item.resource_id == "arn:aws:ec2:us-east-1:123456789012:security-group/sg-123"
        assert item.control_ids == ["SC-7"]
    
    def test_to_dict_from_dict_round_trip(self):
        """Test that to_dict() -> from_dict() preserves all data."""
        now_iso = datetime.now(timezone.utc).isoformat()
        original = EvidenceItem(
            source="iam",
            finding_id="iam-check-456",
            title="IAM Access Key Age",
            status="FAILED",
            severity="LOW",
            resource_type="AWS::IAM::AccessKey",
            resource_id="arn:aws:iam::123456789012:user/testuser",
            timestamp=now_iso,
            remediation="Rotate the access key",
            control_ids=["IA-4"],
            raw_data={"age_days": 120}
        )
        
        # Serialize to dict and back
        d = original.to_dict()
        restored = EvidenceItem.from_dict(d)
        
        assert restored.source == original.source
        assert restored.finding_id == original.finding_id
        assert restored.title == original.title
        assert restored.status == original.status
        assert restored.severity == original.severity
        assert restored.resource_type == original.resource_type
        assert restored.resource_id == original.resource_id
        assert restored.timestamp == original.timestamp
        assert restored.remediation == original.remediation
        assert restored.control_ids == original.control_ids
        assert restored.raw_data == original.raw_data
    
    def test_from_dict_handles_missing_optional_fields(self):
        """Test that from_dict() handles missing optional fields gracefully."""
        data = {
            "source": "security_hub",
            "finding_id": "minimal-123",
            "title": "Minimal Finding",
            "status": "PASSED",
            "severity": "INFORMATIONAL",
            "resource_type": "AWS::Lambda::Function",
            "resource_id": "arn:aws:lambda:us-east-1:123456789012:function:test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Missing: remediation, control_ids, raw_data
        }
        
        item = EvidenceItem.from_dict(data)
        
        assert item.remediation == ""
        assert item.control_ids == []
        assert item.raw_data == {}


class TestScanResult:
    """Test ScanResult aggregation and grouping."""
    
    def test_finalize_aggregates_all_evidence(self):
        """Test that finalize() collects evidence from all collectors."""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        evidence1 = [
            EvidenceItem(
                source="security_hub", finding_id="f1", title="Finding 1",
                status="PASSED", severity="LOW",
                resource_type="AWS::S3::Bucket", resource_id="arn:aws:s3:::bucket1",
                timestamp=now_iso, control_ids=["AC-2"]
            )
        ]
        evidence2 = [
            EvidenceItem(
                source="config", finding_id="f2", title="Finding 2",
                status="FAILED", severity="HIGH",
                resource_type="AWS::EC2::SecurityGroup", resource_id="arn:aws:ec2:sg-123",
                timestamp=now_iso, control_ids=["SC-7"]
            )
        ]
        
        scan = ScanResult(
            scan_id="test-scan-123",
            scan_start=now_iso,
            account_id="123456789012",
            region="us-east-1",
            collector_results={
                "security_hub": CollectorResult(
                    source="security_hub",
                    status="SUCCESS",
                    evidence_items=evidence1
                ),
                "config": CollectorResult(
                    source="config",
                    status="SUCCESS",
                    evidence_items=evidence2
                ),
            }
        )
        
        scan.finalize()
        
        assert len(scan.all_evidence) == 2
        assert scan.all_evidence[0].finding_id == "f1"
        assert scan.all_evidence[1].finding_id == "f2"
        assert scan.status == "COMPLETED"
        assert scan.scan_end != ""
    
    def test_finalize_marks_errors_in_status(self):
        """Test that finalize() sets COMPLETED_WITH_ERRORS when errors exist."""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        scan = ScanResult(
            scan_id="test-scan-456",
            scan_start=now_iso,
            account_id="123456789012",
            region="us-east-1",
            errors=["Collector error: connection timeout"]
        )
        
        scan.finalize()
        
        assert scan.status == "COMPLETED_WITH_ERRORS"
        assert len(scan.errors) == 1
    
    def test_evidence_by_control_groups_by_control_id(self):
        """Test that evidence_by_control property groups evidence correctly."""
        now_iso = datetime.now(timezone.utc).isoformat()
        
        evidence = [
            EvidenceItem(
                source="security_hub", finding_id="f1", title="Finding 1",
                status="PASSED", severity="LOW",
                resource_type="AWS::S3::Bucket", resource_id="arn:aws:s3:::bucket1",
                timestamp=now_iso, control_ids=["AC-2"]
            ),
            EvidenceItem(
                source="config", finding_id="f2", title="Finding 2",
                status="FAILED", severity="HIGH",
                resource_type="AWS::EC2::SecurityGroup", resource_id="arn:aws:ec2:sg-123",
                timestamp=now_iso, control_ids=["SC-7", "SC-8"]
            ),
            EvidenceItem(
                source="iam", finding_id="f3", title="Finding 3",
                status="PASSED", severity="LOW",
                resource_type="AWS::IAM::User", resource_id="arn:aws:iam::123456789012:user/test",
                timestamp=now_iso, control_ids=["AC-2"]
            ),
        ]
        
        scan = ScanResult(
            scan_id="test-scan-789",
            scan_start=now_iso,
            account_id="123456789012",
            region="us-east-1",
            all_evidence=evidence
        )
        
        by_control = scan.evidence_by_control
        
        assert "AC-2" in by_control
        assert len(by_control["AC-2"]) == 2
        assert by_control["AC-2"][0].finding_id == "f1"
        assert by_control["AC-2"][1].finding_id == "f3"
        
        assert "SC-7" in by_control
        assert len(by_control["SC-7"]) == 1
        assert by_control["SC-7"][0].finding_id == "f2"
        
        assert "SC-8" in by_control
        assert len(by_control["SC-8"]) == 1


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_generate_scan_id_format(self):
        """Test that generate_scan_id() produces correctly formatted IDs."""
        scan_id = generate_scan_id()
        
        # Format: {timestamp}_{uuid}
        parts = scan_id.split("_")
        assert len(parts) == 2
        
        timestamp_part = parts[0]
        uuid_part = parts[1]
        
        # Timestamp should be ISO format with time separators
        assert "T" in timestamp_part
        assert "Z" in timestamp_part
        
        # UUID part should be alphanumeric
        assert len(uuid_part) == 8
        assert uuid_part.isalnum() or "-" in uuid_part
    
    def test_generate_scan_id_uniqueness(self):
        """Test that multiple calls to generate_scan_id() produce unique IDs."""
        ids = set()
        for _ in range(100):
            ids.add(generate_scan_id())
        
        assert len(ids) == 100, "All generated IDs should be unique"
    
    def test_generate_drift_id_format(self):
        """Test that generate_drift_id() produces correctly formatted IDs."""
        drift_id = generate_drift_id()
        
        assert drift_id.startswith("drift-")
        assert len(drift_id) > 6


class TestControlAssessment:
    """Test ControlAssessment serialization."""
    
    def test_to_dict_serializes_status_as_value(self):
        """Test that to_dict() serializes ControlStatus as string value."""
        now_iso = datetime.now(timezone.utc).isoformat()
        assessment = ControlAssessment(
            control_id="AC-2",
            control_title="Account Management",
            control_family="AC",
            family_name="Access Control",
            status=ControlStatus.PASS,
            scan_id="scan-123",
            timestamp=now_iso
        )
        
        d = assessment.to_dict()
        
        assert d["status"] == "PASS"  # Value, not enum
        assert isinstance(d["status"], str)
    
    def test_from_dict_converts_status_string_to_enum(self):
        """Test that from_dict() converts status string to ControlStatus enum."""
        now_iso = datetime.now(timezone.utc).isoformat()
        data = {
            "control_id": "SC-7",
            "control_title": "Boundary Protection",
            "control_family": "SC",
            "family_name": "System and Communications Protection",
            "status": "FAIL",  # String value
            "scan_id": "scan-456",
            "timestamp": now_iso
        }
        
        assessment = ControlAssessment.from_dict(data)
        
        assert assessment.status == ControlStatus.FAIL
        assert isinstance(assessment.status, ControlStatus)
