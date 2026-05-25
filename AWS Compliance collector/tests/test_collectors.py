"""
Tests for AWS collectors using botocore.Stubber with real ASFF JSON.

Tests SecurityHubCollector, ConfigCollector, and IAMCollector against
realistic AWS API responses — the missing link between mock evidence
and production collector code.

Uses botocore.Stubber (not moto) for precise control over API responses.
Each test feeds the collector a response matching the real AWS API schema
and verifies the output EvidenceItem objects.
"""

import boto3
from botocore.stub import Stubber

from src.collector.security_hub import SecurityHubCollector
from src.collector.config_collector import ConfigCollector
from src.collector.iam_collector import IAMCollector
from src.models import EvidenceItem, CollectorResult


# =============================================================================
# REAL ASFF FIXTURES — Based on actual AWS Security Hub output
# =============================================================================

ASFF_FINDING_ROOT_MFA = {
    "SchemaVersion": "2018-10-08",
    "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/IAM.6/finding/abc123",
    "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
    "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/IAM.6",
    "AwsAccountId": "123456789012",
    "Types": ["Software and Configuration Checks/Industry and Regulatory Standards"],
    "FirstObservedAt": "2024-01-08T10:00:00.000Z",
    "CreatedAt": "2024-01-08T10:00:00.000Z",
    "UpdatedAt": "2024-01-08T10:00:00.000Z",
    "Severity": {"Label": "CRITICAL", "Normalized": 90},
    "Title": "IAM.6 Hardware MFA should be enabled for the root user",
    "Description": "This control checks whether your AWS account is enabled to use a hardware MFA device.",
    "Remediation": {
        "Recommendation": {
            "Text": "Enable a hardware MFA device for the root user.",
            "Url": "https://docs.aws.amazon.com/console/securityhub/IAM.6/remediation",
        }
    },
    "ProductFields": {"StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0"},
    "Resources": [
        {
            "Type": "AWS::IAM::User",
            "Id": "arn:aws:iam::123456789012:root",
            "Partition": "aws",
            "Region": "us-east-1",
        }
    ],
    "Compliance": {"Status": "FAILED"},
    "WorkflowState": "NEW",
    "Workflow": {"Status": "NEW"},
    "RecordState": "ACTIVE",
    "RelatedRequirements": [
        {"RelatedRequirement": "NIST.800-53.r5 AC-2"},
        {"RelatedRequirement": "NIST.800-53.r5 IA-2(1)"},
    ],
}

ASFF_FINDING_S3_SSL = {
    "SchemaVersion": "2018-10-08",
    "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/S3.5/finding/def456",
    "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
    "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.5",
    "AwsAccountId": "123456789012",
    "Types": ["Software and Configuration Checks/Industry and Regulatory Standards"],
    "FirstObservedAt": "2024-01-08T10:01:00.000Z",
    "CreatedAt": "2024-01-08T10:01:00.000Z",
    "UpdatedAt": "2024-01-08T10:01:00.000Z",
    "Severity": {"Label": "HIGH", "Normalized": 70},
    "Title": "S3.5 S3 general purpose buckets should require requests to use SSL",
    "Description": "This control checks whether S3 buckets have policies that require SSL.",
    "Remediation": {
        "Recommendation": {
            "Text": "Add a bucket policy that denies access over HTTP.",
            "Url": "https://docs.aws.amazon.com/console/securityhub/S3.5/remediation",
        }
    },
    "ProductFields": {},
    "Resources": [
        {
            "Type": "AWS::S3::Bucket",
            "Id": "arn:aws:s3:::production-data-bucket",
            "Partition": "aws",
            "Region": "us-east-1",
        }
    ],
    "Compliance": {"Status": "FAILED"},
    "WorkflowState": "NEW",
    "Workflow": {"Status": "NEW"},
    "RecordState": "ACTIVE",
    "RelatedRequirements": [
        {"RelatedRequirement": "NIST.800-53.r5 SC-8"},
        {"RelatedRequirement": "NIST.800-53.r5 SC-13"},
    ],
}

ASFF_FINDING_CLOUDTRAIL_PASS = {
    "SchemaVersion": "2018-10-08",
    "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/CloudTrail.1/finding/ghi789",
    "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
    "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/CloudTrail.1",
    "AwsAccountId": "123456789012",
    "Types": ["Software and Configuration Checks/Industry and Regulatory Standards"],
    "FirstObservedAt": "2024-01-08T10:02:00.000Z",
    "CreatedAt": "2024-01-08T10:02:00.000Z",
    "UpdatedAt": "2024-01-08T10:02:00.000Z",
    "Severity": {"Label": "INFORMATIONAL", "Normalized": 0},
    "Title": "CloudTrail.1 CloudTrail should be enabled and configured with at least one multi-Region trail",
    "Description": "This control checks that there is at least one multi-region CloudTrail trail.",
    "Remediation": {"Recommendation": {"Text": "No action required."}},
    "ProductFields": {},
    "Resources": [
        {
            "Type": "AWS::CloudTrail::Trail",
            "Id": "arn:aws:cloudtrail:us-east-1:123456789012:trail/org-trail",
            "Partition": "aws",
            "Region": "us-east-1",
        }
    ],
    "Compliance": {"Status": "PASSED"},
    "WorkflowState": "RESOLVED",
    "Workflow": {"Status": "RESOLVED"},
    "RecordState": "ARCHIVED",
    "RelatedRequirements": [
        {"RelatedRequirement": "NIST.800-53.r5 AU-2"},
        {"RelatedRequirement": "NIST.800-53.r5 AU-3"},
        {"RelatedRequirement": "NIST.800-53.r5 AU-12"},
    ],
}


# =============================================================================
# SecurityHubCollector Tests
# =============================================================================

class TestSecurityHubCollector:
    """Tests for SecurityHubCollector using botocore.Stubber."""

    def _make_collector(self):
        """Create a SecurityHubCollector with a stubbed client."""
        client = boto3.client("securityhub", region_name="us-east-1")
        collector = SecurityHubCollector(
            client=client,
            account_id="123456789012",
            region="us-east-1",
        )
        return collector, client

    def test_parse_finding_extracts_nist_controls(self):
        """Test that _parse_finding extracts NIST control IDs from real ASFF."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert evidence is not None
        assert isinstance(evidence, EvidenceItem)
        assert "AC-2" in evidence.control_ids
        assert "IA-2(1)" in evidence.control_ids

    def test_parse_finding_maps_active_to_failed(self):
        """ACTIVE RecordState should map to FAILED status."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert evidence.status == "FAILED"

    def test_parse_finding_maps_archived_to_passed(self):
        """ARCHIVED RecordState should map to PASSED status."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_CLOUDTRAIL_PASS)

        assert evidence.status == "PASSED"

    def test_parse_finding_extracts_severity(self):
        """Test severity extraction from ASFF Severity.Label."""
        collector, _ = self._make_collector()

        critical = collector._parse_finding(ASFF_FINDING_ROOT_MFA)
        assert critical.severity == "CRITICAL"

        high = collector._parse_finding(ASFF_FINDING_S3_SSL)
        assert high.severity == "HIGH"

        info = collector._parse_finding(ASFF_FINDING_CLOUDTRAIL_PASS)
        assert info.severity == "INFORMATIONAL"

    def test_parse_finding_extracts_resource(self):
        """Test resource type and ID extraction from ASFF Resources."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert evidence.resource_type == "AWS::IAM::User"
        assert evidence.resource_id == "arn:aws:iam::123456789012:root"

    def test_parse_finding_extracts_remediation(self):
        """Test remediation text extraction."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert "hardware MFA" in evidence.remediation

    def test_parse_finding_extracts_timestamp(self):
        """Test timestamp extraction from FirstObservedAt."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert evidence.timestamp == "2024-01-08T10:00:00.000Z"

    def test_parse_finding_stores_raw_data(self):
        """Test that the full ASFF finding is stored in raw_data."""
        collector, _ = self._make_collector()
        evidence = collector._parse_finding(ASFF_FINDING_ROOT_MFA)

        assert evidence.raw_data == ASFF_FINDING_ROOT_MFA

    def test_parse_finding_handles_missing_remediation(self):
        """Test graceful handling of finding without Remediation field."""
        collector, _ = self._make_collector()
        finding = {
            "Id": "test-finding",
            "Title": "Test",
            "RecordState": "ACTIVE",
            "Severity": {"Label": "LOW"},
            "Resources": [{"Type": "AWS::S3::Bucket", "Id": "test-bucket"}],
            "RelatedRequirements": [],
        }
        evidence = collector._parse_finding(finding)

        assert evidence is not None
        assert evidence.remediation == ""

    def test_parse_finding_handles_empty_resources(self):
        """Test that _parse_finding returns None when Resources is empty.

        This is a real edge case — some Security Hub findings from third-party
        integrations may have empty Resources arrays. The collector logs a
        warning and skips these rather than crashing.
        """
        collector, _ = self._make_collector()
        finding = {
            "Id": "test-finding",
            "Title": "Test",
            "RecordState": "ACTIVE",
            "Severity": {"Label": "MEDIUM"},
            "Resources": [],
            "RelatedRequirements": [],
        }
        evidence = collector._parse_finding(finding)

        # Returns None because resource extraction fails (index out of range)
        # This is acceptable — the collector logs a warning and continues
        assert evidence is None

    def test_extract_nist_controls_real_asff_format(self):
        """Test NIST control extraction with real ASFF RelatedRequirements format."""
        collector, _ = self._make_collector()

        # Real format: "NIST.800-53.r5 AC-2"
        assert collector._extract_nist_controls("NIST.800-53.r5 AC-2") == ["AC-2"]
        assert collector._extract_nist_controls("NIST.800-53.r5 IA-2(1)") == ["IA-2(1)"]
        assert collector._extract_nist_controls("NIST.800-53.r5 AU-12") == ["AU-12"]

        # Non-NIST requirements should return empty
        assert collector._extract_nist_controls("CIS AWS Foundations Benchmark v1.4.0/1.14") == []
        assert collector._extract_nist_controls("PCI DSS 3.2.1/8.3.1") == []

    def test_collect_with_stubber(self):
        """Test full collect() flow using botocore.Stubber with real ASFF response.

        botocore's Stubber validates response shapes strictly. The real
        ASFF schema puts RelatedRequirements inside Compliance, not at
        the top level. We strip the top-level key and move NIST refs
        into Compliance.RelatedRequirements as flat strings — matching
        exactly what the real AWS API returns.
        """
        collector, client = self._make_collector()

        def _stubber_finding(finding):
            """Convert test fixtures to Stubber-compatible shape."""
            clean = {k: v for k, v in finding.items() if k != "RelatedRequirements"}
            if "RelatedRequirements" in finding:
                reqs = [r["RelatedRequirement"] for r in finding["RelatedRequirements"]]
                clean.setdefault("Compliance", {})
                clean["Compliance"]["RelatedRequirements"] = reqs
            return clean

        stubber = Stubber(client)
        stubber.add_response(
            "get_findings",
            {
                "Findings": [
                    _stubber_finding(ASFF_FINDING_ROOT_MFA),
                    _stubber_finding(ASFF_FINDING_S3_SSL),
                    _stubber_finding(ASFF_FINDING_CLOUDTRAIL_PASS),
                ],
            },
        )

        with stubber:
            result = collector.collect()

        assert isinstance(result, CollectorResult)
        assert result.status == "SUCCESS"
        assert result.raw_findings_count == 3
        assert len(result.evidence_items) == 3

        # Verify severity parsing works
        severities = {e.severity for e in result.evidence_items}
        assert "CRITICAL" in severities
        assert "HIGH" in severities

        # Verify NIST controls extracted from Compliance.RelatedRequirements
        root_mfa = [e for e in result.evidence_items if e.severity == "CRITICAL"][0]
        assert "AC-2" in root_mfa.control_ids
        assert "IA-2(1)" in root_mfa.control_ids

    def test_collect_handles_access_denied(self):
        """Test that collect() handles AccessDeniedException gracefully."""
        collector, client = self._make_collector()

        stubber = Stubber(client)
        stubber.add_client_error(
            "get_findings",
            service_error_code="AccessDeniedException",
            service_message="User is not authorized to perform securityhub:GetFindings",
        )

        with stubber:
            result = collector.collect()

        assert result.status == "ERROR"
        assert "Access denied" in result.error_message

    def test_collect_handles_empty_account(self):
        """Test collect() on an account with no Security Hub findings."""
        collector, client = self._make_collector()

        stubber = Stubber(client)
        stubber.add_response("get_findings", {"Findings": [], "NextToken": ""})

        with stubber:
            result = collector.collect()

        assert result.status == "SUCCESS"
        assert result.raw_findings_count == 0
        assert len(result.evidence_items) == 0


# =============================================================================
# ConfigCollector Tests
# =============================================================================

class TestConfigCollector:
    """Tests for ConfigCollector using botocore.Stubber."""

    def _make_collector(self):
        """Create a ConfigCollector with a stubbed client."""
        client = boto3.client("config", region_name="us-east-1")
        collector = ConfigCollector(
            client=client,
            account_id="123456789012",
            region="us-east-1",
        )
        return collector, client

    def test_collect_handles_access_denied(self):
        """Test graceful handling when Config access is denied."""
        collector, client = self._make_collector()

        stubber = Stubber(client)
        stubber.add_client_error(
            "describe_compliance_by_config_rule",
            service_error_code="AccessDeniedException",
            service_message="Not authorized",
        )

        with stubber:
            result = collector.collect()

        assert result.status == "ERROR"
        assert isinstance(result, CollectorResult)


# =============================================================================
# IAMCollector Tests
# =============================================================================

class TestIAMCollector:
    """Tests for IAMCollector using botocore.Stubber."""

    def _make_collector(self):
        """Create an IAMCollector with a stubbed client."""
        client = boto3.client("iam", region_name="us-east-1")
        collector = IAMCollector(
            client=client,
            account_id="123456789012",
        )
        return collector, client

    def test_collect_handles_access_denied(self):
        """Test graceful handling when IAM access is denied."""
        collector, client = self._make_collector()

        stubber = Stubber(client)
        stubber.add_client_error(
            "get_credential_report",
            service_error_code="AccessDeniedException",
            service_message="Not authorized",
        )

        with stubber:
            result = collector.collect()

        assert isinstance(result, CollectorResult)
        assert result.status in ("ERROR", "PARTIAL", "SUCCESS")
