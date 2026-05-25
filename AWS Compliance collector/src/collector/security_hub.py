"""
SecurityHubCollector: Gathers compliance findings from AWS Security Hub.

Maps ASFF (AWS Security Findings Format) RelatedRequirements to NIST 800-53
control IDs. Uses server-side filters and pagination for efficient, large-scale
finding retrieval.

DDIA Connection (Ch. 1 — Data Systems):
    We use paginated scanning (not pulling all findings into memory at once)
    because real AWS accounts may have thousands of findings. Pagination is
    critical for scalability.
"""

try:
    from src.models import (
        EvidenceItem,
        CollectorResult,
        SeverityLevel,
        FindingStatus,
        SEVERITY_WEIGHTS,
    )
except ImportError:
    from ..models import (
        EvidenceItem,
        CollectorResult,
        SeverityLevel,
        FindingStatus,
        SEVERITY_WEIGHTS,
    )

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class SecurityHubCollector:
    """
    Collects compliance findings from AWS Security Hub.

    Attributes:
        client: boto3 SecurityHub client (or mock)
        account_id: AWS account ID
        region: AWS region
    """

    def __init__(
        self,
        client=None,
        account_id: str = "",
        region: str = "us-east-1",
    ):
        """
        Initialize SecurityHubCollector.

        Args:
            client: boto3 securityhub client. If None, creates one with retry config.
            account_id: AWS account ID. If empty, retrieved from STS.
            region: AWS region.
        """
        self.region = region
        self.account_id = account_id

        if client is None:
            retry_config = Config(
                retries={"max_attempts": 5, "mode": "adaptive"}
            )
            self.client = boto3.client("securityhub", region_name=region, config=retry_config)
        else:
            self.client = client

        if not self.account_id:
            try:
                sts = boto3.client("sts")
                self.account_id = sts.get_caller_identity()["Account"]
            except ClientError as e:
                logger.warning(f"Could not retrieve account ID from STS: {e}")
                self.account_id = "unknown"

    def collect(self) -> CollectorResult:
        """
        Collect all findings from Security Hub and map to NIST controls.

        Uses server-side filters to retrieve only active findings, then paginates
        through all results using the GetFindings API.

        Returns:
            CollectorResult with evidence_items, status, and metadata.
        """
        result = CollectorResult(
            source="security_hub",
            status="SUCCESS",
            evidence_items=[],
            raw_findings_count=0,
        )

        try:
            evidence_items = []
            raw_count = 0

            # Server-side filter: get only active findings
            filters = {
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            }

            # Paginate through all findings
            paginator = self.client.get_paginator("get_findings")
            page_iterator = paginator.paginate(
                Filters=filters,
                PaginationConfig={"PageSize": 100},
            )

            for page in page_iterator:
                for finding in page.get("Findings", []):
                    raw_count += 1
                    evidence_item = self._parse_finding(finding)
                    if evidence_item:
                        evidence_items.append(evidence_item)

            result.evidence_items = evidence_items
            result.raw_findings_count = raw_count
            result.status = "SUCCESS"

            if raw_count == 0:
                logger.info("No active findings in Security Hub.")
            else:
                logger.info(
                    f"Collected {len(evidence_items)} evidence items "
                    f"from {raw_count} Security Hub findings."
                )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "AccessDeniedException":
                result.status = "ERROR"
                result.error_message = f"Access denied to Security Hub: {str(e)}"
                result.metadata["error_type"] = "AccessDeniedException"
                logger.error(result.error_message)

            elif error_code == "InvalidAccessException":
                result.status = "ERROR"
                result.error_message = f"Invalid access to Security Hub: {str(e)}"
                result.metadata["error_type"] = "InvalidAccessException"
                logger.error(result.error_message)

            elif error_code == "ThrottlingException":
                result.status = "PARTIAL"
                result.error_message = f"Security Hub throttled request: {str(e)}"
                result.metadata["error_type"] = "ThrottlingException"
                logger.warning(result.error_message)

            else:
                result.status = "ERROR"
                result.error_message = f"Error collecting from Security Hub: {str(e)}"
                result.metadata["error_type"] = error_code
                logger.error(result.error_message)

        except BotoCoreError as e:
            result.status = "ERROR"
            result.error_message = f"Botocore error: {str(e)}"
            result.metadata["error_type"] = "BotoCoreError"
            logger.error(result.error_message)

        except Exception as e:
            result.status = "ERROR"
            result.error_message = f"Unexpected error in SecurityHubCollector: {str(e)}"
            result.metadata["error_type"] = type(e).__name__
            logger.error(result.error_message)

        return result

    def _parse_finding(self, finding: Dict[str, Any]) -> Optional[EvidenceItem]:
        """
        Parse an ASFF finding into an EvidenceItem.

        Maps RelatedRequirements to NIST control IDs.

        Args:
            finding: ASFF finding dict from Security Hub.

        Returns:
            EvidenceItem or None if parsing fails.
        """
        try:
            finding_id = finding.get("Id", "unknown")
            title = finding.get("Title", "Unknown Finding")
            status_str = finding.get("RecordState", "UNKNOWN")

            # Map ASFF RecordState to our FindingStatus
            if status_str == "ACTIVE":
                status = "FAILED"  # ACTIVE = needs remediation
            elif status_str == "ARCHIVED":
                status = "PASSED"
            else:
                status = "NOT_EVALUATED"

            severity_label = finding.get("Severity", {}).get("Label", "INFORMATIONAL")
            resource_type = finding.get("Resources", [{}])[0].get("Type", "AWS::Unknown")
            resource_id = finding.get("Resources", [{}])[0].get("Id", "unknown")

            # Extract NIST control IDs from RelatedRequirements
            # Real ASFF stores these in two places:
            #   1. Compliance.RelatedRequirements — flat list of strings (botocore schema)
            #   2. Top-level RelatedRequirements — list of dicts (some integrations)
            # We check both to be resilient.
            control_ids = []

            # Primary: Compliance.RelatedRequirements (real AWS API location)
            compliance_reqs = finding.get("Compliance", {}).get("RelatedRequirements", [])
            for req_text in compliance_reqs:
                controls = self._extract_nist_controls(req_text)
                control_ids.extend(controls)

            # Fallback: top-level RelatedRequirements (legacy / third-party)
            for req in finding.get("RelatedRequirements", []):
                if isinstance(req, dict):
                    req_text = req.get("RelatedRequirement", "")
                else:
                    req_text = str(req)
                controls = self._extract_nist_controls(req_text)
                control_ids.extend(controls)

            control_ids = list(set(control_ids))  # Deduplicate

            # Remediation recommendation
            remediation = ""
            if "Remediation" in finding and "Recommendation" in finding["Remediation"]:
                remediation = finding["Remediation"]["Recommendation"].get("Text", "")

            timestamp = finding.get("FirstObservedAt", datetime.now(timezone.utc).isoformat())

            evidence_item = EvidenceItem(
                source="security_hub",
                finding_id=finding_id,
                title=title,
                status=status,
                severity=severity_label,
                resource_type=resource_type,
                resource_id=resource_id,
                timestamp=timestamp,
                remediation=remediation,
                control_ids=control_ids,
                raw_data=finding,
            )

            return evidence_item

        except Exception as e:
            logger.warning(f"Failed to parse Security Hub finding {finding.get('Id')}: {e}")
            return None

    @staticmethod
    def _extract_nist_controls(requirement_text: str) -> List[str]:
        """
        Extract NIST control IDs from requirement text.

        Looks for patterns like AC-2, AU-12, CM-3(2), etc.

        Args:
            requirement_text: Text from RelatedRequirement field.

        Returns:
            List of NIST control IDs found.
        """
        import re

        controls = []
        # Pattern matches AC-2, AC-2(1), AU-12, SI-4(5), etc.
        pattern = r'\b([A-Z]{2})-(\d+)(?:\((\d+)\))?'
        matches = re.findall(pattern, requirement_text)

        for match in matches:
            family = match[0]
            control_num = match[1]
            enhancement = match[2] if match[2] else ""

            if enhancement:
                control_id = f"{family}-{control_num}({enhancement})"
            else:
                control_id = f"{family}-{control_num}"

            controls.append(control_id)

        return controls
