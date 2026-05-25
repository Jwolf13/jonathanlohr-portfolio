"""
IAMCollector: Gathers compliance evidence from AWS IAM.

Collects:
  - IAM credential report: password age, MFA status
  - IAM password policy: complexity requirements
  - IAM account summary: user counts, policy counts

Maps findings to NIST 800-53 controls for access control and authentication.

DVA-C02 Connection:
    IAM is the primary identity and access management service in AWS.
    Understanding IAM credential report structure is testable knowledge.
"""

try:
    from src.models import (
        EvidenceItem,
        CollectorResult,
    )
except ImportError:
    from ..models import (
        EvidenceItem,
        CollectorResult,
    )

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import csv
import io
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class IAMCollector:
    """
    Collects compliance evidence from AWS IAM.

    Evaluates:
      - Root account usage and MFA
      - User credential age and rotation
      - Password policy requirements
      - MFA enablement
      - Access key rotation

    Attributes:
        client: boto3 iam client (or mock)
        account_id: AWS account ID
    """

    def __init__(
        self,
        client=None,
        account_id: str = "",
    ):
        """
        Initialize IAMCollector.

        Args:
            client: boto3 iam client. If None, creates one with retry config.
            account_id: AWS account ID. If empty, retrieved from STS.
        """
        self.account_id = account_id

        if client is None:
            retry_config = Config(
                retries={"max_attempts": 5, "mode": "adaptive"}
            )
            self.client = boto3.client("iam", config=retry_config)
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
        Collect IAM compliance evidence.

        Retrieves credential report, password policy, and account summary,
        then generates EvidenceItems for access control and authentication controls.

        Returns:
            CollectorResult with evidence_items, status, and metadata.
        """
        result = CollectorResult(
            source="iam",
            status="SUCCESS",
            evidence_items=[],
            raw_findings_count=0,
        )

        try:
            evidence_items = []

            # Collect credential report
            credential_report = self._get_credential_report()
            if credential_report:
                evidence_items.extend(
                    self._assess_credentials(credential_report)
                )
                result.raw_findings_count += len(credential_report)

            # Collect password policy
            password_policy = self._get_password_policy()
            if password_policy:
                evidence_items.extend(
                    self._assess_password_policy(password_policy)
                )
                result.raw_findings_count += 1

            # Collect account summary
            account_summary = self._get_account_summary()
            if account_summary:
                evidence_items.extend(
                    self._assess_account_summary(account_summary)
                )
                result.raw_findings_count += 1

            result.evidence_items = evidence_items
            result.status = "SUCCESS"

            logger.info(
                f"Collected {len(evidence_items)} evidence items from IAM."
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "AccessDeniedException":
                result.status = "ERROR"
                result.error_message = f"Access denied to IAM: {str(e)}"
                result.metadata["error_type"] = "AccessDeniedException"
                logger.error(result.error_message)

            elif error_code == "ThrottlingException":
                result.status = "PARTIAL"
                result.error_message = f"IAM throttled request: {str(e)}"
                result.metadata["error_type"] = "ThrottlingException"
                logger.warning(result.error_message)

            else:
                result.status = "ERROR"
                result.error_message = f"Error collecting from IAM: {str(e)}"
                result.metadata["error_type"] = error_code
                logger.error(result.error_message)

        except BotoCoreError as e:
            result.status = "ERROR"
            result.error_message = f"Botocore error: {str(e)}"
            result.metadata["error_type"] = "BotoCoreError"
            logger.error(result.error_message)

        except Exception as e:
            result.status = "ERROR"
            result.error_message = f"Unexpected error in IAMCollector: {str(e)}"
            result.metadata["error_type"] = type(e).__name__
            logger.error(result.error_message)

        return result

    def _get_credential_report(self) -> Optional[List[Dict[str, str]]]:
        """
        Retrieve the IAM credential report.

        The credential report is a CSV that lists all users, their credential
        status (access keys, passwords, MFA), and last used dates.

        Returns:
            List of dicts, one per IAM user, or None if failed.
        """
        try:
            # Generate credential report (async operation)
            self.client.generate_credential_report()

            # Poll until ready
            for _ in range(10):
                response = self.client.get_credential_report()
                if response.get("Content"):
                    # Content is base64-encoded CSV
                    import base64
                    csv_data = base64.b64decode(response["Content"]).decode("utf-8")

                    # Parse CSV
                    reader = csv.DictReader(io.StringIO(csv_data))
                    return list(reader)

            logger.warning("Credential report generation timed out.")
            return None

        except ClientError as e:
            logger.warning(f"Could not retrieve credential report: {e}")
            return None

    def _get_password_policy(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the account password policy.

        Returns:
            PasswordPolicy dict or None if not set.
        """
        try:
            response = self.client.get_account_password_policy()
            return response.get("PasswordPolicy", {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                logger.info("No custom password policy set (using default).")
                return None
            logger.warning(f"Could not retrieve password policy: {e}")
            return None

    def _get_account_summary(self) -> Optional[Dict[str, int]]:
        """
        Retrieve account summary statistics.

        Returns:
            Summary dict with user counts, policy counts, etc.
        """
        try:
            response = self.client.get_account_summary()
            return response.get("SummaryMap", {})
        except ClientError as e:
            logger.warning(f"Could not retrieve account summary: {e}")
            return None

    def _assess_credentials(
        self, credential_report: List[Dict[str, str]]
    ) -> List[EvidenceItem]:
        """
        Assess individual user credentials against NIST controls.

        Checks for:
          - AC-2: Account and Access Control
          - IA-2: Authentication
          - IA-4: Identifier Management
          - IA-5(1): Password-based Authentication

        Args:
            credential_report: List of credential report rows.

        Returns:
            List of EvidenceItems.
        """
        evidence_items = []

        # Check root account status (AC-2, IA-2)
        for row in credential_report:
            if row.get("user") == "<root_account>":
                root_mfa = row.get("mfa_active", "false") == "true"
                root_access_key = row.get("access_key_1_active") == "true" or \
                                 row.get("access_key_2_active") == "true"

                root_status = "PASSED" if root_mfa and not root_access_key else "FAILED"

                evidence_items.append(
                    EvidenceItem(
                        source="iam",
                        finding_id=f"iam-root-account-{self.account_id}",
                        title="Root Account Security",
                        status=root_status,
                        severity="CRITICAL" if not root_mfa else "LOW",
                        resource_type="AWS::IAM::Root",
                        resource_id="<root_account>",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        remediation=(
                            "Enable MFA on root account and disable root access keys. "
                            "Use IAM users with minimal permissions instead."
                        ),
                        control_ids=["AC-2", "IA-2"],
                        raw_data={"root_mfa_enabled": root_mfa, "root_access_keys": root_access_key},
                    )
                )
                continue

            # Check user credentials (IA-2, IA-4, IA-5(1))
            user = row.get("user", "unknown")
            password_enabled = row.get("password_enabled", "false") == "true"
            password_last_changed = row.get("password_last_changed", "N/A")
            mfa_active = row.get("mfa_active", "false") == "true"

            # Calculate password age
            password_age_days = 0
            if password_last_changed != "N/A":
                try:
                    last_changed = datetime.fromisoformat(
                        password_last_changed.replace("Z", "+00:00")
                    )
                    password_age_days = (
                        datetime.now(timezone.utc) - last_changed
                    ).days
                except ValueError:
                    pass

            # Password status (IA-5(1))
            if password_enabled:
                if password_age_days > 90:
                    password_status = "FAILED"
                    severity = "MEDIUM"
                elif password_age_days > 60:
                    password_status = "FAILED"
                    severity = "LOW"
                else:
                    password_status = "PASSED"
                    severity = "INFORMATIONAL"

                evidence_items.append(
                    EvidenceItem(
                        source="iam",
                        finding_id=f"iam-password-{user}-{self.account_id}",
                        title=f"User {user}: Password Age",
                        status=password_status,
                        severity=severity,
                        resource_type="AWS::IAM::User",
                        resource_id=user,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        remediation="Rotate password to meet organizational policy.",
                        control_ids=["IA-5(1)", "IA-4"],
                        raw_data={"password_age_days": password_age_days},
                    )
                )

            # MFA status (IA-2)
            mfa_status = "PASSED" if mfa_active else "FAILED"
            evidence_items.append(
                EvidenceItem(
                    source="iam",
                    finding_id=f"iam-mfa-{user}-{self.account_id}",
                    title=f"User {user}: MFA Enablement",
                    status=mfa_status,
                    severity="HIGH" if not mfa_active else "INFORMATIONAL",
                    resource_type="AWS::IAM::User",
                    resource_id=user,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    remediation="Enable virtual MFA device for this user.",
                    control_ids=["IA-2"],
                    raw_data={"mfa_active": mfa_active},
                )
            )

        return evidence_items

    def _assess_password_policy(
        self, policy: Dict[str, Any]
    ) -> List[EvidenceItem]:
        """
        Assess password policy against NIST controls.

        Checks for:
          - IA-5(1): Password-based Authentication

        Args:
            policy: PasswordPolicy dict.

        Returns:
            List of EvidenceItems.
        """
        evidence_items = []

        # Check minimum password length
        min_length = policy.get("MinimumPasswordLength", 0)
        length_status = "PASSED" if min_length >= 14 else "FAILED"

        evidence_items.append(
            EvidenceItem(
                source="iam",
                finding_id=f"iam-password-length-{self.account_id}",
                title="IAM Password Policy: Minimum Length",
                status=length_status,
                severity="MEDIUM" if min_length < 14 else "INFORMATIONAL",
                resource_type="AWS::IAM::PasswordPolicy",
                resource_id="PasswordPolicy",
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Set minimum password length to 14 characters.",
                control_ids=["IA-5(1)"],
                raw_data={"minimum_length": min_length},
            )
        )

        # Check complexity requirements
        requires_symbols = policy.get("RequireSymbols", False)
        requires_numbers = policy.get("RequireNumbers", False)
        requires_uppercase = policy.get("RequireUppercaseCharacters", False)
        requires_lowercase = policy.get("RequireLowercaseCharacters", False)

        complexity_met = (
            requires_symbols and requires_numbers and
            requires_uppercase and requires_lowercase
        )
        complexity_status = "PASSED" if complexity_met else "FAILED"

        evidence_items.append(
            EvidenceItem(
                source="iam",
                finding_id=f"iam-password-complexity-{self.account_id}",
                title="IAM Password Policy: Complexity Requirements",
                status=complexity_status,
                severity="MEDIUM" if not complexity_met else "INFORMATIONAL",
                resource_type="AWS::IAM::PasswordPolicy",
                resource_id="PasswordPolicy",
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Enable all complexity requirements (symbols, numbers, case).",
                control_ids=["IA-5(1)"],
                raw_data={
                    "requires_symbols": requires_symbols,
                    "requires_numbers": requires_numbers,
                    "requires_uppercase": requires_uppercase,
                    "requires_lowercase": requires_lowercase,
                },
            )
        )

        # Check password expiration
        expire_days = policy.get("ExpirePasswords", False)
        expire_status = "PASSED" if expire_days else "FAILED"

        evidence_items.append(
            EvidenceItem(
                source="iam",
                finding_id=f"iam-password-expiration-{self.account_id}",
                title="IAM Password Policy: Password Expiration",
                status=expire_status,
                severity="LOW" if not expire_days else "INFORMATIONAL",
                resource_type="AWS::IAM::PasswordPolicy",
                resource_id="PasswordPolicy",
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Enable password expiration with 90-day rotation requirement.",
                control_ids=["IA-5(1)", "IA-4"],
                raw_data={"password_expiration_enabled": expire_days},
            )
        )

        return evidence_items

    def _assess_account_summary(
        self, summary: Dict[str, int]
    ) -> List[EvidenceItem]:
        """
        Assess account-wide IAM configuration.

        Checks for:
          - AC-2: Account Management (user count, policy count)

        Args:
            summary: Account summary dict.

        Returns:
            List of EvidenceItems.
        """
        evidence_items = []

        user_count = summary.get("UserCount", 0)
        role_count = summary.get("RoleCount", 0)
        policy_count = summary.get("PolicyCount", 0)

        # Assess principal count (AC-2)
        principal_status = "PASSED" if user_count > 0 and role_count > 0 else "FAILED"

        evidence_items.append(
            EvidenceItem(
                source="iam",
                finding_id=f"iam-principals-configured-{self.account_id}",
                title="IAM: Principals and Roles Configured",
                status=principal_status,
                severity="HIGH" if not principal_status == "PASSED" else "INFORMATIONAL",
                resource_type="AWS::IAM::AccountSummary",
                resource_id="AccountSummary",
                timestamp=datetime.now(timezone.utc).isoformat(),
                remediation="Ensure IAM users and roles are properly configured for your workload.",
                control_ids=["AC-2"],
                raw_data={
                    "user_count": user_count,
                    "role_count": role_count,
                    "policy_count": policy_count,
                },
            )
        )

        return evidence_items
