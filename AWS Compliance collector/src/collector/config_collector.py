"""
ConfigCollector: Gathers compliance evidence from AWS Config.

Maps AWS Config rules to NIST 800-53 control IDs. AWS Config evaluates your
infrastructure against predefined rules (e.g., "encrypted-volumes",
"ec2-security-group-auditing"), allowing continuous compliance monitoring.

DDIA Connection (Ch. 5 — Replication):
    Config provides the "source of truth" for infrastructure compliance state.
    It continuously re-evaluates as infrastructure changes (eventual consistency).
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


class ConfigCollector:
    """
    Collects compliance evidence from AWS Config rules.

    Maps 30+ common AWS Config rules to NIST 800-53 controls.

    Attributes:
        client: boto3 config client (or mock)
        account_id: AWS account ID
        region: AWS region
    """

    # Maps AWS Config rule names to NIST control IDs
    RULE_TO_NIST_MAP = {
        "s3-bucket-public-read-prohibited": ["AC-3"],
        "s3-bucket-public-write-prohibited": ["AC-3"],
        "s3-bucket-server-side-encryption-enabled": ["SC-7"],
        "s3-bucket-versioning-enabled": ["SI-12"],
        "s3-object-lock-enabled": ["SC-7"],
        "encrypted-volumes": ["SC-7"],
        "root-account-mfa-enabled": ["IA-2"],
        "mfa-enabled-for-iam-console-access": ["IA-2"],
        "iam-password-policy": ["IA-5"],
        "iam-user-mfa-enabled": ["IA-2"],
        "access-keys-rotated": ["IA-4"],
        "iam-user-unused-credentials-check": ["AC-2"],
        "ec2-security-group-auditing": ["AU-12"],
        "ec2-security-groups-in-use": ["AC-3"],
        "restricted-incoming-traffic": ["AC-3"],
        "restricted-ssh": ["AC-3"],
        "restricted-rdp": ["AC-3"],
        "elb-logging-enabled": ["AU-12"],
        "alb-http-to-https-redirection-check": ["SC-7"],
        "api-gw-execution-logs-enabled": ["AU-12"],
        "apigateway-logging-enabled": ["AU-12"],
        "cloudtrail-enabled": ["AU-2"],
        "cloudtrail-logs-encrypted": ["SC-7"],
        "cloudwatch-log-group-encrypted": ["SC-7"],
        "config-enabled": ["CM-3"],
        "config-all-supported": ["CM-3"],
        "dynamodb-encryption-enabled": ["SC-7"],
        "rds-encryption-enabled": ["SC-7"],
        "rds-multi-az-support": ["CP-13"],
        "approved-amis-by-tag": ["CM-2"],
        "ec2-ebs-encryption-by-default": ["SC-7"],
        "guardduty-enabled-centralized": ["SI-4"],
        "rds-automatic-minor-version-upgrade-enabled": ["CP-9"],
        "rds-backup-enabled": ["CP-9"],
        "dynamodb-pitr-enabled": ["CP-9"],
        "elasticache-redis-cluster-automatic-backup-check": ["CP-9"],
    }

    def __init__(
        self,
        client=None,
        account_id: str = "",
        region: str = "us-east-1",
    ):
        """
        Initialize ConfigCollector.

        Args:
            client: boto3 config client. If None, creates one with retry config.
            account_id: AWS account ID. If empty, retrieved from STS.
            region: AWS region.
        """
        self.region = region
        self.account_id = account_id

        if client is None:
            retry_config = Config(
                retries={"max_attempts": 5, "mode": "adaptive"}
            )
            self.client = boto3.client("config", region_name=region, config=retry_config)
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
        Collect all Config rule evaluations and map to NIST controls.

        Iterates through all enabled rules and retrieves their evaluation results.
        Maps each rule to NIST control IDs using RULE_TO_NIST_MAP.

        Returns:
            CollectorResult with evidence_items, status, and metadata.
        """
        result = CollectorResult(
            source="config",
            status="SUCCESS",
            evidence_items=[],
            raw_findings_count=0,
        )

        try:
            evidence_items = []
            raw_count = 0

            # Get all Config rules
            paginator = self.client.get_paginator("describe_config_rules")
            page_iterator = paginator.paginate(
                PaginationConfig={"PageSize": 25}
            )

            for page in page_iterator:
                for rule in page.get("ConfigRules", []):
                    rule_name = rule.get("ConfigRuleName", "unknown")

                    # Get evaluation results for this rule
                    try:
                        eval_paginator = self.client.get_paginator(
                            "describe_compliance_by_config_rule"
                        )
                        eval_iterator = eval_paginator.paginate(
                            ConfigRuleNames=[rule_name],
                            PaginationConfig={"PageSize": 100},
                        )

                        for eval_page in eval_iterator:
                            for compliance in eval_page.get("ComplianceByConfigRules", []):
                                raw_count += 1

                                # Get detailed evaluation details
                                evaluation_details = self._get_evaluation_details(
                                    rule_name
                                )

                                # Map rule to NIST controls
                                control_ids = self.RULE_TO_NIST_MAP.get(
                                    rule_name, []
                                )

                                evidence_item = self._parse_compliance(
                                    rule,
                                    compliance,
                                    evaluation_details,
                                    control_ids,
                                )

                                if evidence_item:
                                    evidence_items.append(evidence_item)

                    except ClientError as e:
                        logger.warning(
                            f"Error getting compliance details for rule {rule_name}: {e}"
                        )
                        continue

            result.evidence_items = evidence_items
            result.raw_findings_count = raw_count
            result.status = "SUCCESS"

            logger.info(
                f"Collected {len(evidence_items)} evidence items "
                f"from {raw_count} Config rule evaluations."
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "AccessDeniedException":
                result.status = "ERROR"
                result.error_message = f"Access denied to Config: {str(e)}"
                result.metadata["error_type"] = "AccessDeniedException"
                logger.error(result.error_message)

            elif error_code == "ThrottlingException":
                result.status = "PARTIAL"
                result.error_message = f"Config throttled request: {str(e)}"
                result.metadata["error_type"] = "ThrottlingException"
                logger.warning(result.error_message)

            else:
                result.status = "ERROR"
                result.error_message = f"Error collecting from Config: {str(e)}"
                result.metadata["error_type"] = error_code
                logger.error(result.error_message)

        except BotoCoreError as e:
            result.status = "ERROR"
            result.error_message = f"Botocore error: {str(e)}"
            result.metadata["error_type"] = "BotoCoreError"
            logger.error(result.error_message)

        except Exception as e:
            result.status = "ERROR"
            result.error_message = f"Unexpected error in ConfigCollector: {str(e)}"
            result.metadata["error_type"] = type(e).__name__
            logger.error(result.error_message)

        return result

    def _get_evaluation_details(self, rule_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed evaluation results for a Config rule.

        Args:
            rule_name: Name of the Config rule.

        Returns:
            List of evaluation detail dicts.
        """
        try:
            response = self.client.get_compliance_details_by_config_rule(
                ConfigRuleName=rule_name,
                ComplianceTypes=["COMPLIANT", "NON_COMPLIANT"],
            )
            return response.get("EvaluationResults", [])
        except ClientError as e:
            logger.debug(f"Could not retrieve evaluation details for {rule_name}: {e}")
            return []

    def _parse_compliance(
        self,
        rule: Dict[str, Any],
        compliance: Dict[str, Any],
        evaluation_details: List[Dict[str, Any]],
        control_ids: List[str],
    ) -> Optional[EvidenceItem]:
        """
        Parse Config rule compliance result into an EvidenceItem.

        Args:
            rule: ConfigRule dict from describe_config_rules.
            compliance: Compliance dict from describe_compliance_by_config_rule.
            evaluation_details: Evaluation results from get_compliance_details_by_config_rule.
            control_ids: NIST control IDs this rule maps to

        Returns:
            EvidenceItem or None if parsing fails.
        """
        try:
            rule_name = rule.get("ConfigRuleName", "unknown")
            rule_description = rule.get("Description", "")

            compliance_type = compliance.get("Compliance", {}).get(
                "ComplianceType", "UNKNOWN"
            )
            status = (
                "PASSED"
                if compliance_type == "COMPLIANT"
                else "FAILED" if compliance_type == "NON_COMPLIANT"
                else "NOT_EVALUATED"
            )

            # Count compliant vs non-compliant resources
            compliant_resources = 0
            non_compliant_resources = 0
            non_compliant_example = ""

            for eval_result in evaluation_details:
                if eval_result.get("ComplianceType") == "COMPLIANT":
                    compliant_resources += 1
                elif eval_result.get("ComplianceType") == "NON_COMPLIANT":
                    non_compliant_resources += 1
                    if not non_compliant_example:
                        non_compliant_example = eval_result.get(
                            "EvaluationResultIdentifier", {}
                        ).get("EvaluationResultQualifier", {}).get("ResourceId", "")

            # Determine severity based on number of non-compliant resources
            if non_compliant_resources > 10:
                severity = "HIGH"
            elif non_compliant_resources > 5:
                severity = "MEDIUM"
            elif non_compliant_resources > 0:
                severity = "LOW"
            else:
                severity = "INFORMATIONAL"

            resource_id = non_compliant_example or rule_name
            title = f"Config Rule: {rule_name}"

            finding_id = f"config-{rule_name}-{self.account_id}-{self.region}"

            evidence_item = EvidenceItem(
                source="config",
                finding_id=finding_id,
                title=title,
                status=status,
                severity=severity,
                resource_type="AWS::Config::Rule",
                resource_id=resource_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Review Config rule documentation for remediation steps.",
                control_ids=control_ids,
                raw_data={
                    "rule": rule,
                    "compliance": compliance,
                    "compliant_resources": compliant_resources,
                    "non_compliant_resources": non_compliant_resources,
                },
            )

            return evidence_item

        except Exception as e:
            logger.warning(f"Failed to parse Config compliance result: {e}")
            return None
