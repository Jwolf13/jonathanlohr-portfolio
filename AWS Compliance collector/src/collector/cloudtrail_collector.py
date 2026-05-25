"""
CloudTrailCollector: Gathers whether CloudTrail is enabled and configured correctly.

Calls describe_trails and get_trail_status to check if logging is active,
multi-region, and has log file validation enabled. Returns EvidenceItems
mapped to AU-2, AU-3, AU-9, AU-12.

DDIA Connection (Ch. 1 — Data Systems):
    Unlike Security Hub which needs pagination (thousands of findings),
    CloudTrail uses direct API calls — most accounts have 1-5 trails.
    Design your data access pattern to match the actual data shape.
"""

try:
    from src.models import (
        EvidenceItem,
        CollectorResult,
        SEVERITY_WEIGHTS,
    )
except ImportError:
    from ..models import (
        EvidenceItem,
        CollectorResult,
        SEVERITY_WEIGHTS,
    )

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class CloudTrailCollector:
    """
    Collects compliance evidence from AWS CloudTrail.

    Checks whether trails exist, are actively logging, span all regions,
    and have log file validation enabled.

    Attributes:
        client: boto3 cloudtrail client (or mock for testing)
        account_id: AWS account ID
        region: AWS region
    """

    def __init__(self, client=None, account_id: str = "", region: str = "us-east-1"):
        self.region = region
        self.account_id = account_id

        if client is None:
            retry_config = Config(retries={"max_attempts": 5, "mode": "adaptive"})
            self.client = boto3.client("cloudtrail", region_name=region, config=retry_config)
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
        Collect CloudTrail configuration and map to NIST AU controls.

        Returns:
            CollectorResult with evidence_items, status, and metadata.
        """
        result = CollectorResult(
            source="cloudtrail",
            status="SUCCESS",
            evidence_items=[],
            raw_findings_count=0,
        )

        try:
            response = self.client.describe_trails(includeShadowTrails=False)
            trails = response.get("trailList", [])

            if not trails:
                result.evidence_items = [self._no_trail_evidence()]
                result.raw_findings_count = 1
                return result

            for trail in trails:
                trail_status = self.client.get_trail_status(Name=trail["TrailARN"])
                evidence = self._parse_trail(trail, trail_status)
                if evidence:
                    result.evidence_items.append(evidence)
                result.raw_findings_count += 1

            result.status = "SUCCESS"
            logger.info(
                f"Collected {len(result.evidence_items)} CloudTrail evidence items "
                f"from {result.raw_findings_count} trails."
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "AccessDeniedException":
                result.status = "ERROR"
                result.error_message = f"Access denied to CloudTrail: {str(e)}"
                result.metadata["error_type"] = "AccessDeniedException"
                logger.error(result.error_message)

            elif error_code == "ThrottlingException":
                result.status = "PARTIAL"
                result.error_message = f"CloudTrail throttled request: {str(e)}"
                result.metadata["error_type"] = "ThrottlingException"
                logger.warning(result.error_message)

            else:
                result.status = "ERROR"
                result.error_message = f"Error collecting from CloudTrail: {str(e)}"
                result.metadata["error_type"] = error_code
                logger.error(result.error_message)

        except BotoCoreError as e:
            result.status = "ERROR"
            result.error_message = f"Botocore error: {str(e)}"
            result.metadata["error_type"] = "BotoCoreError"
            logger.error(result.error_message)

        except Exception as e:
            result.status = "ERROR"
            result.error_message = f"Unexpected error in CloudTrailCollector: {str(e)}"
            result.metadata["error_type"] = type(e).__name__
            logger.error(result.error_message)

        return result

    def _parse_trail(
        self,
        trail: Dict[str, Any],
        trail_status: Dict[str, Any],
    ) -> Optional[EvidenceItem]:
        """
        Parse a CloudTrail trail + status into an EvidenceItem.

        Args:
            trail: Trail config dict from describe_trails.
            trail_status: Status dict from get_trail_status.

        Returns:
            EvidenceItem or None if parsing fails.
        """
        try:
            is_logging = trail_status.get("IsLogging", False)
            is_multi_region = trail.get("IsMultiRegionTrail", False)
            log_validation = trail.get("LogFileValidationEnabled", False)

            if is_logging and is_multi_region and log_validation:
                status = "PASSED"
                severity = "INFORMATIONAL"
            elif is_logging:
                status = "PARTIAL"
                severity = "MEDIUM"
            else:
                status = "FAILED"
                severity = "HIGH"

            return EvidenceItem(
                source="cloudtrail",
                finding_id=f"cloudtrail-{trail['TrailARN']}",
                title=f"CloudTrail: {trail['Name']}",
                status=status,
                severity=severity,
                resource_type="AWS::CloudTrail::Trail",
                resource_id=trail["TrailARN"],
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Enable multi-region trail with log file validation.",
                control_ids=["AU-2", "AU-3", "AU-9", "AU-12"],
                raw_data={"trail": trail, "status": trail_status},
            )

        except Exception as e:
            logger.warning(f"Failed to parse CloudTrail trail {trail.get('Name')}: {e}")
            return None

    def _no_trail_evidence(self) -> EvidenceItem:
        """Return a FAILED EvidenceItem when no trails exist in the account."""
        return EvidenceItem(
            source="cloudtrail",
            finding_id=f"cloudtrail-none-{self.account_id}",
            title="No CloudTrail trails exist in this account",
            status="FAILED",
            severity="HIGH",
            resource_type="AWS::CloudTrail::Trail",
            resource_id=self.account_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            remediation="Create a multi-region trail with log file validation enabled.",
            control_ids=["AU-2", "AU-3", "AU-9", "AU-12"],
        )
