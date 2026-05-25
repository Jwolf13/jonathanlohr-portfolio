"""
ComplianceCollector: Orchestrator that runs all sub-collectors in parallel.

Coordinates:
  - SecurityHubCollector
  - ConfigCollector
  - IAMCollector

Handles partial failures (one collector error doesn't stop the entire scan),
tracks timing per collector, and finalizes the ScanResult.

DDIA Connection (Ch. 12 — The Future of Data Systems):
    This orchestrator implements fault tolerance: if one collector fails,
    others continue. It's a real-world system design pattern.
"""

try:
    from src.models import (
        ScanResult,
        generate_scan_id,
    )
except ImportError:
    from ..models import (
        ScanResult,
        generate_scan_id,
    )

from .security_hub import SecurityHubCollector
from .config_collector import ConfigCollector
from .iam_collector import IAMCollector

from datetime import datetime, timezone
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ComplianceCollector:
    """
    Orchestrator that runs all compliance collectors and aggregates results.

    Attributes:
        security_hub_client: boto3 client for Security Hub (or mock)
        config_client: boto3 client for Config (or mock)
        iam_client: boto3 client for IAM (or mock)
        account_id: AWS account ID
        region: AWS region
    """

    def __init__(
        self,
        security_hub_client=None,
        config_client=None,
        iam_client=None,
        account_id: str = "",
        region: str = "us-east-1",
    ):
        """
        Initialize ComplianceCollector.

        Args:
            security_hub_client: boto3 securityhub client or mock.
            config_client: boto3 config client or mock.
            iam_client: boto3 iam client or mock.
            account_id: AWS account ID. If empty, retrieved from STS.
            region: AWS region.
        """
        self.account_id = account_id
        self.region = region

        # Lazy-load account ID if not provided
        if not self.account_id:
            try:
                import boto3
                sts = boto3.client("sts")
                self.account_id = sts.get_caller_identity()["Account"]
            except Exception as e:
                logger.warning(f"Could not retrieve account ID from STS: {e}")
                self.account_id = "unknown"

        # Initialize sub-collectors with provided or default clients
        self.security_hub_collector = SecurityHubCollector(
            client=security_hub_client,
            account_id=self.account_id,
            region=self.region,
        )
        self.config_collector = ConfigCollector(
            client=config_client,
            account_id=self.account_id,
            region=self.region,
        )
        self.iam_collector = IAMCollector(
            client=iam_client,
            account_id=self.account_id,
        )

    def run_scan(self) -> ScanResult:
        """
        Run all collectors in sequence and aggregate results.

        Each collector runs to completion; if one fails, others continue.
        Tracks duration per collector. Calls finalize() on the ScanResult.

        Returns:
            Completed ScanResult with all evidence aggregated.
        """
        scan_id = generate_scan_id()
        scan_result = ScanResult(
            scan_id=scan_id,
            scan_start=datetime.now(timezone.utc).isoformat(),
            account_id=self.account_id,
            region=self.region,
        )

        logger.info(f"Starting compliance scan {scan_id}")

        # Run Security Hub collector
        logger.info("Running SecurityHubCollector...")
        start_time = time.time()
        try:
            security_hub_result = self.security_hub_collector.collect()
            duration_ms = int((time.time() - start_time) * 1000)
            security_hub_result.duration_ms = duration_ms
            scan_result.collector_results["security_hub"] = security_hub_result

            if security_hub_result.status == "ERROR":
                scan_result.errors.append(
                    f"SecurityHub error: {security_hub_result.error_message}"
                )
            logger.info(
                f"SecurityHubCollector completed in {duration_ms}ms: "
                f"{len(security_hub_result.evidence_items)} evidence items"
            )
        except Exception as e:
            error_msg = f"SecurityHubCollector exception: {str(e)}"
            scan_result.errors.append(error_msg)
            logger.error(error_msg)

        # Run Config collector
        logger.info("Running ConfigCollector...")
        start_time = time.time()
        try:
            config_result = self.config_collector.collect()
            duration_ms = int((time.time() - start_time) * 1000)
            config_result.duration_ms = duration_ms
            scan_result.collector_results["config"] = config_result

            if config_result.status == "ERROR":
                scan_result.errors.append(
                    f"Config error: {config_result.error_message}"
                )
            logger.info(
                f"ConfigCollector completed in {duration_ms}ms: "
                f"{len(config_result.evidence_items)} evidence items"
            )
        except Exception as e:
            error_msg = f"ConfigCollector exception: {str(e)}"
            scan_result.errors.append(error_msg)
            logger.error(error_msg)

        # Run IAM collector
        logger.info("Running IAMCollector...")
        start_time = time.time()
        try:
            iam_result = self.iam_collector.collect()
            duration_ms = int((time.time() - start_time) * 1000)
            iam_result.duration_ms = duration_ms
            scan_result.collector_results["iam"] = iam_result

            if iam_result.status == "ERROR":
                scan_result.errors.append(
                    f"IAM error: {iam_result.error_message}"
                )
            logger.info(
                f"IAMCollector completed in {duration_ms}ms: "
                f"{len(iam_result.evidence_items)} evidence items"
            )
        except Exception as e:
            error_msg = f"IAMCollector exception: {str(e)}"
            scan_result.errors.append(error_msg)
            logger.error(error_msg)

        # Finalize scan result
        scan_result.finalize()

        total_evidence = len(scan_result.all_evidence)
        logger.info(
            f"Scan {scan_id} completed with status {scan_result.status}: "
            f"{total_evidence} total evidence items, {len(scan_result.errors)} errors"
        )

        return scan_result
