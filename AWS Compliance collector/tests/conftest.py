"""
Pytest configuration and shared fixtures for AWS Compliance Evidence Collector tests.

Provides:
  - sample_evidence_items: Realistic EvidenceItem fixtures covering multiple controls
  - sample_scan_result: A complete ScanResult with aggregated evidence
  - sample_assessments: List of ControlAssessment with mixed statuses
  - previous_assessments: Same controls with different statuses for drift testing
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from src.models import (
    EvidenceItem,
    ScanResult,
    ControlAssessment,
    ControlStatus,
    CollectorResult,
    generate_scan_id,
)


# =============================================================================
# EVIDENCE FIXTURES
# =============================================================================

@pytest.fixture
def sample_evidence_items():
    """
    Create realistic evidence items covering multiple NIST 800-53 controls.
    
    Covers: AC-2, AU-2, SC-7, SC-8, SC-13, IA-2(1), IA-5(1), CM-6, SI-4
    Mix of PASSED and FAILED statuses with realistic severity levels.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    
    return [
        # AC-2: Account Management - FAILED
        EvidenceItem(
            source="iam",
            finding_id="root-account-access",
            title="Root account not using MFA",
            status="FAILED",
            severity="CRITICAL",
            resource_type="AWS::IAM::User",
            resource_id="arn:aws:iam::123456789012:root",
            timestamp=now_iso,
            remediation="Enable MFA on root account immediately",
            control_ids=["AC-2"],
            raw_data={"finding_type": "ROOT_MFA"}
        ),
        
        # AU-2: Audit Events - PASSED
        EvidenceItem(
            source="config",
            finding_id="cloudtrail-enabled-check",
            title="CloudTrail enabled and logging to S3",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::CloudTrail::Trail",
            resource_id="arn:aws:cloudtrail:us-east-1:123456789012:trail/main-trail",
            timestamp=now_iso,
            remediation="",
            control_ids=["AU-2"],
            raw_data={"is_logging": True, "s3_bucket": "compliance-logs"}
        ),
        
        # SC-8: Data in Transit - FAILED (public bucket)
        EvidenceItem(
            source="security_hub",
            finding_id="s3-public-bucket",
            title="S3 bucket is publicly accessible",
            status="FAILED",
            severity="CRITICAL",
            resource_type="AWS::S3::Bucket",
            resource_id="arn:aws:s3:::my-public-bucket",
            timestamp=now_iso,
            remediation="Block public access using bucket policies and ACLs",
            control_ids=["SC-7", "SC-8"],
            raw_data={"bucket_acl": "public-read"}
        ),
        
        # SC-8: Data in Transit - PASSED (SSL required)
        EvidenceItem(
            source="config",
            finding_id="s3-bucket-ssl-required",
            title="S3 bucket requires SSL/TLS for all connections",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::S3::Bucket",
            resource_id="arn:aws:s3:::secure-bucket",
            timestamp=now_iso,
            remediation="",
            control_ids=["SC-8"],
            raw_data={"ssl_required": True}
        ),
        
        # SC-13: Encryption at Rest - PASSED (both items passed)
        EvidenceItem(
            source="config",
            finding_id="rds-encryption-enabled",
            title="RDS database encryption enabled",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::RDS::DBInstance",
            resource_id="arn:aws:rds:us-east-1:123456789012:db:production-db",
            timestamp=now_iso,
            remediation="",
            control_ids=["SC-13"],
            raw_data={"storage_encrypted": True, "kms_key_id": "arn:aws:kms:..."}
        ),
        EvidenceItem(
            source="config",
            finding_id="ebs-encryption-by-default",
            title="EBS encryption enabled by default in account",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::EC2::Volume",
            resource_id="arn:aws:ec2:us-east-1:123456789012:volume/*",
            timestamp=now_iso,
            remediation="",
            control_ids=["SC-13"],
            raw_data={"encryption_enabled": True}
        ),
        
        # IA-2(1): MFA - PASSED
        EvidenceItem(
            source="iam",
            finding_id="mfa-enabled-console-users",
            title="All console users have MFA enabled",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::IAM::User",
            resource_id="arn:aws:iam::123456789012:user/*",
            timestamp=now_iso,
            remediation="",
            control_ids=["IA-2", "IA-2(1)"],
            raw_data={"mfa_devices_count": 5}
        ),
        
        # IA-5(1): Password Policy - PASSED
        EvidenceItem(
            source="iam",
            finding_id="password-policy-strength",
            title="Password policy enforces minimum 14 characters",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::IAM::AccountPasswordPolicy",
            resource_id="arn:aws:iam::123456789012:account-password-policy",
            timestamp=now_iso,
            remediation="",
            control_ids=["IA-5", "IA-5(1)"],
            raw_data={"min_length": 14, "require_symbols": True, "expiration_days": 90}
        ),
        
        # CM-6: Configuration Settings - FAILED
        EvidenceItem(
            source="security_hub",
            finding_id="sg-open-to-world",
            title="Security group allows unrestricted inbound access",
            status="FAILED",
            severity="HIGH",
            resource_type="AWS::EC2::SecurityGroup",
            resource_id="arn:aws:ec2:us-east-1:123456789012:security-group/sg-12345678",
            timestamp=now_iso,
            remediation="Restrict inbound rules to required IPs/ranges only",
            control_ids=["CM-6", "SC-7"],
            raw_data={"cidr_blocks": ["0.0.0.0/0"]}
        ),
        
        # SI-4: System Monitoring - PASSED
        EvidenceItem(
            source="guardduty",
            finding_id="guardduty-enabled",
            title="GuardDuty is enabled for threat detection",
            status="PASSED",
            severity="INFORMATIONAL",
            resource_type="AWS::GuardDuty::Detector",
            resource_id="arn:aws:guardduty:us-east-1:123456789012:detector/12345678",
            timestamp=now_iso,
            remediation="",
            control_ids=["SI-4"],
            raw_data={"status": "ENABLED", "finding_publishing_frequency": "FIFTEEN_MINUTES"}
        ),
    ]


# =============================================================================
# SCAN RESULT FIXTURE
# =============================================================================

@pytest.fixture
def sample_scan_result(sample_evidence_items):
    """
    Create a complete ScanResult with aggregated evidence.
    
    Simulates output from ComplianceCollector.run_scan().
    """
    scan_id = generate_scan_id()
    scan_start = datetime.now(timezone.utc).isoformat()
    
    # Aggregate evidence into collector results
    security_hub_items = [e for e in sample_evidence_items if e.source == "security_hub"]
    config_items = [e for e in sample_evidence_items if e.source == "config"]
    iam_items = [e for e in sample_evidence_items if e.source == "iam"]
    guardduty_items = [e for e in sample_evidence_items if e.source == "guardduty"]
    
    collector_results = {
        "security_hub": CollectorResult(
            source="security_hub",
            status="SUCCESS",
            evidence_items=security_hub_items,
            raw_findings_count=len(security_hub_items),
            duration_ms=500,
        ),
        "config": CollectorResult(
            source="config",
            status="SUCCESS",
            evidence_items=config_items,
            raw_findings_count=len(config_items),
            duration_ms=400,
        ),
        "iam": CollectorResult(
            source="iam",
            status="SUCCESS",
            evidence_items=iam_items,
            raw_findings_count=len(iam_items),
            duration_ms=300,
        ),
        "guardduty": CollectorResult(
            source="guardduty",
            status="SUCCESS",
            evidence_items=guardduty_items,
            raw_findings_count=len(guardduty_items),
            duration_ms=200,
        ),
    }
    
    scan_result = ScanResult(
        scan_id=scan_id,
        scan_start=scan_start,
        status="IN_PROGRESS",
        collector_results=collector_results,
        account_id="123456789012",
        region="us-east-1",
    )
    
    # Finalize to aggregate all evidence
    scan_result.finalize()
    
    return scan_result


# =============================================================================
# ASSESSMENT FIXTURES
# =============================================================================

@pytest.fixture
def sample_assessments(sample_scan_result):
    """
    Create ControlAssessment list with mixed PASS/FAIL/PARTIAL statuses.
    
    These would be output from ControlMappingEngine.assess_all_controls().
    """
    scan_id = sample_scan_result.scan_id
    now_iso = datetime.now(timezone.utc).isoformat()
    
    assessments = [
        # AC-2: FAIL (root account MFA issue)
        ControlAssessment(
            control_id="AC-2",
            control_title="Account Management",
            control_family="AC",
            family_name="Access Control",
            status=ControlStatus.FAIL,
            evidence=[e for e in sample_scan_result.all_evidence if "AC-2" in e.control_ids],
            total_findings=1,
            failed_findings=1,
            passed_findings=0,
            highest_severity="CRITICAL",
            fedramp_baseline="MODERATE",
            remediation_priority=9,
            assessment_criteria="All accounts must be managed with proper access controls and MFA enabled",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # AC-3: NOT_ASSESSED (no evidence)
        ControlAssessment(
            control_id="AC-3",
            control_title="Access Enforcement",
            control_family="AC",
            family_name="Access Control",
            status=ControlStatus.NOT_ASSESSED,
            evidence=[],
            total_findings=0,
            failed_findings=0,
            passed_findings=0,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=2,
            assessment_criteria="Security groups, IAM policies, and bucket policies must properly restrict access",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # AU-2: PASS
        ControlAssessment(
            control_id="AU-2",
            control_title="Audit Events",
            control_family="AU",
            family_name="Audit and Accountability",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "AU-2" in e.control_ids],
            total_findings=1,
            failed_findings=0,
            passed_findings=1,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="CloudTrail must be enabled and logging to secure storage",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # AU-12: NOT_ASSESSED (no evidence)
        ControlAssessment(
            control_id="AU-12",
            control_title="Audit Generation",
            control_family="AU",
            family_name="Audit and Accountability",
            status=ControlStatus.NOT_ASSESSED,
            evidence=[],
            total_findings=0,
            failed_findings=0,
            passed_findings=0,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=2,
            assessment_criteria="ALB/ELB logging must be configured",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # CM-2: NOT_ASSESSED (no evidence)
        ControlAssessment(
            control_id="CM-2",
            control_title="Baseline Configuration",
            control_family="CM",
            family_name="Configuration Management",
            status=ControlStatus.NOT_ASSESSED,
            evidence=[],
            total_findings=0,
            failed_findings=0,
            passed_findings=0,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="AWS Systems Manager must maintain baselines",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # CM-3: NOT_ASSESSED
        ControlAssessment(
            control_id="CM-3",
            control_title="Change Control",
            control_family="CM",
            family_name="Configuration Management",
            status=ControlStatus.NOT_ASSESSED,
            evidence=[],
            total_findings=0,
            failed_findings=0,
            passed_findings=0,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="Configuration drift must be detected and monitored",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # CM-6: FAIL (security group issue)
        ControlAssessment(
            control_id="CM-6",
            control_title="Security Configuration Management",
            control_family="CM",
            family_name="Configuration Management",
            status=ControlStatus.FAIL,
            evidence=[e for e in sample_scan_result.all_evidence if "CM-6" in e.control_ids],
            total_findings=1,
            failed_findings=1,
            passed_findings=0,
            highest_severity="HIGH",
            fedramp_baseline="MODERATE",
            remediation_priority=6,
            assessment_criteria="All security groups must restrict access to minimum necessary",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # IA-2: PASS
        ControlAssessment(
            control_id="IA-2",
            control_title="Authentication",
            control_family="IA",
            family_name="Identification and Authentication",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "IA-2" in e.control_ids],
            total_findings=1,
            failed_findings=0,
            passed_findings=1,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="MFA must be enabled for all users",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # IA-2(1): PASS
        ControlAssessment(
            control_id="IA-2(1)",
            control_title="Multi-Factor Authentication",
            control_family="IA",
            family_name="Identification and Authentication",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "IA-2(1)" in e.control_ids],
            total_findings=1,
            failed_findings=0,
            passed_findings=1,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="All privileged users must use MFA",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # IA-4: NOT_ASSESSED
        ControlAssessment(
            control_id="IA-4",
            control_title="Identifier Management",
            control_family="IA",
            family_name="Identification and Authentication",
            status=ControlStatus.NOT_ASSESSED,
            evidence=[],
            total_findings=0,
            failed_findings=0,
            passed_findings=0,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="Access keys must be rotated every 90 days",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # IA-5(1): PASS
        ControlAssessment(
            control_id="IA-5(1)",
            control_title="Password-based Authentication",
            control_family="IA",
            family_name="Identification and Authentication",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "IA-5(1)" in e.control_ids],
            total_findings=1,
            failed_findings=0,
            passed_findings=1,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="Password policy must enforce minimum 14 chars, complexity, 90-day rotation",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # SC-7: FAIL (public bucket + security group failures)
        ControlAssessment(
            control_id="SC-7",
            control_title="Boundary Protection",
            control_family="SC",
            family_name="System and Communications Protection",
            status=ControlStatus.FAIL,
            evidence=[e for e in sample_scan_result.all_evidence if "SC-7" in e.control_ids],
            total_findings=2,
            failed_findings=2,
            passed_findings=0,
            highest_severity="CRITICAL",
            fedramp_baseline="MODERATE",
            remediation_priority=9,
            assessment_criteria="Data boundaries must be protected with encryption and access controls",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # SC-8: PARTIAL (one failed, one passed)
        ControlAssessment(
            control_id="SC-8",
            control_title="Transmission Confidentiality and Integrity",
            control_family="SC",
            family_name="System and Communications Protection",
            status=ControlStatus.PARTIAL,
            evidence=[e for e in sample_scan_result.all_evidence if "SC-8" in e.control_ids],
            total_findings=2,
            failed_findings=1,
            passed_findings=1,
            highest_severity="CRITICAL",
            fedramp_baseline="MODERATE",
            remediation_priority=8,
            assessment_criteria="All data in transit must use TLS/SSL encryption",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # SC-13: PASS (both encrypted)
        ControlAssessment(
            control_id="SC-13",
            control_title="Cryptographic Protection",
            control_family="SC",
            family_name="System and Communications Protection",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "SC-13" in e.control_ids],
            total_findings=2,
            failed_findings=0,
            passed_findings=2,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="Encryption at rest must be enabled for all data stores",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
        
        # SI-4: PASS
        ControlAssessment(
            control_id="SI-4",
            control_title="Information System Monitoring",
            control_family="SI",
            family_name="System and Information Integrity",
            status=ControlStatus.PASS,
            evidence=[e for e in sample_scan_result.all_evidence if "SI-4" in e.control_ids],
            total_findings=1,
            failed_findings=0,
            passed_findings=1,
            highest_severity="INFORMATIONAL",
            fedramp_baseline="MODERATE",
            remediation_priority=1,
            assessment_criteria="GuardDuty must be enabled for threat detection",
            scan_id=scan_id,
            timestamp=now_iso,
        ),
    ]
    
    return assessments


# =============================================================================
# DRIFT TESTING FIXTURES
# =============================================================================

@pytest.fixture
def previous_assessments(sample_assessments):
    """
    Create assessment list with different statuses for drift testing.
    
    Simulates a previous scan state with some improvements and regressions.
    """
    previous = []
    
    for assessment in sample_assessments:
        prev_assessment = ControlAssessment(
            control_id=assessment.control_id,
            control_title=assessment.control_title,
            control_family=assessment.control_family,
            family_name=assessment.family_name,
            status=assessment.status,  # Copy status initially
            evidence=assessment.evidence,
            total_findings=assessment.total_findings,
            failed_findings=assessment.failed_findings,
            passed_findings=assessment.passed_findings,
            highest_severity=assessment.highest_severity,
            fedramp_baseline=assessment.fedramp_baseline,
            remediation_priority=assessment.remediation_priority,
            assessment_criteria=assessment.assessment_criteria,
            scan_id="scan_previous_xyz",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        # Alter some statuses to test drift detection
        if assessment.control_id == "SC-7":
            # This one will IMPROVE: FAIL -> PASS (fixed the public bucket issue)
            prev_assessment.status = ControlStatus.PARTIAL
            prev_assessment.failed_findings = 2
            prev_assessment.passed_findings = 0
        elif assessment.control_id == "SC-8":
            # This one will REGRESS: PASS -> PARTIAL (new issue found)
            prev_assessment.status = ControlStatus.PASS
            prev_assessment.failed_findings = 0
            prev_assessment.passed_findings = 2
        elif assessment.control_id == "CM-6":
            # This one will IMPROVE: FAIL -> PASS (security group fixed)
            prev_assessment.status = ControlStatus.FAIL
            prev_assessment.failed_findings = 1
            prev_assessment.passed_findings = 0
        
        previous.append(prev_assessment)
    
    return previous
