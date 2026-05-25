"""
DynamoDB single-table storage for compliance data.

Implements the access patterns described in Phase 4 and Phase 5 notebooks:

    Entity              PK                          SK                                  GSI1PK                      GSI1SK
    ─────────────────   ─────────────────────────   ─────────────────────────────────   ─────────────────────────   ────────────────────────
    ControlAssessment   CTRL#{control_id}           SCAN#{scan_id}                      SCAN#{scan_id}              CTRL#{control_id}#{status}
    CompliancePosture   POSTURE                     SCAN#{scan_id}                      (none)                      (none)
    DriftEvent          DRIFT#SCAN#{scan_id}        CTRL#{control_id}#{drift_id}        DRIFT#CTRL#{control_id}     {timestamp}

Access patterns supported:
    1. Get assessment for one control in one scan     → GetItem(PK=CTRL#AC-2, SK=SCAN#{id})
    2. Get control history across scans               → Query(PK=CTRL#AC-2, SK begins_with SCAN#)
    3. Get all assessments for a scan                 → Query(GSI1PK=SCAN#{id})
    4. Get all FAIL controls for a scan               → Query(GSI1PK=SCAN#{id}) + FilterExpression
    5. Get posture for a scan                         → GetItem(PK=POSTURE, SK=SCAN#{id})
    6. Get posture history (all scans, sorted)        → Query(PK=POSTURE, SK begins_with SCAN#, ScanIndexForward=False)
    7. Get drift events for a scan                    → Query(PK=DRIFT#SCAN#{id})
    8. Get drift history for a control                → Query(GSI1PK=DRIFT#CTRL#{id})

DDIA Connection (Ch. 3 — Storage and Retrieval):
    DynamoDB uses LSM-tree storage (SSTables). Our PK/SK composite key is
    analogous to a clustered index — items with the same PK are co-located
    on the same partition, making range queries on SK efficient.

DVA-C02 Connection:
    Single-table design, GSI overloading, batch_write_item (25-item limit),
    conditional writes for idempotency, query vs scan vs get_item.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from src.models import (
    ControlAssessment,
    CompliancePosture,
    DriftEvent,
)

logger = logging.getLogger(__name__)

# DynamoDB batch_write_item limit
BATCH_SIZE = 25



def _floats_to_decimals(obj: Any) -> Any:
    """Convert float values to Decimal for DynamoDB compatibility.

    DVA-C02: DynamoDB uses Decimal, not float. This is a common gotcha
    on the exam and in real projects.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _floats_to_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floats_to_decimals(v) for v in obj]
    return obj


def _decimals_to_floats(obj: Any) -> Any:
    """Convert Decimal values back to float when reading from DynamoDB."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimals_to_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimals_to_floats(v) for v in obj]
    return obj


class DynamoDBStore:
    """Single-table DynamoDB store for compliance data.

    Args:
        table_name: DynamoDB table name.
        resource: Optional boto3 DynamoDB resource (for testing with moto).
                  If not provided, creates a default resource.
    """

    TABLE_NAME_DEFAULT = "compliance-evidence"

    def __init__(
        self,
        table_name: str = TABLE_NAME_DEFAULT,
        resource=None,
    ):
        self.table_name = table_name
        self._resource = resource or boto3.resource("dynamodb")
        self._table = self._resource.Table(table_name)

    # =========================================================================
    # Table creation (for local dev / moto tests)
    # =========================================================================

    def create_table(self) -> None:
        """Create the DynamoDB table with GSI.

        Idempotent — skips if the table already exists.
        Used for local development and moto-based tests.
        In production, Terraform manages the table (modules/dynamodb).
        """
        try:
            self._resource.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "PK", "KeyType": "HASH"},
                    {"AttributeName": "SK", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "PK", "AttributeType": "S"},
                    {"AttributeName": "SK", "AttributeType": "S"},
                    {"AttributeName": "GSI1PK", "AttributeType": "S"},
                    {"AttributeName": "GSI1SK", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "GSI1",
                        "KeySchema": [
                            {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                            {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    }
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            logger.info("Created table %s", self.table_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                logger.info("Table %s already exists", self.table_name)
            else:
                raise

    # =========================================================================
    # Key builders — single source of truth for PK/SK patterns
    # =========================================================================

    @staticmethod
    def _assessment_keys(control_id: str, scan_id: str) -> Dict[str, str]:
        """Build PK/SK/GSI keys for a ControlAssessment item."""
        return {
            "PK": f"CTRL#{control_id}",
            "SK": f"SCAN#{scan_id}",
        }

    @staticmethod
    def _assessment_gsi_keys(
        control_id: str, scan_id: str, status: str
    ) -> Dict[str, str]:
        """Build GSI1 keys for a ControlAssessment item."""
        return {
            "GSI1PK": f"SCAN#{scan_id}",
            "GSI1SK": f"CTRL#{control_id}#{status}",
        }

    @staticmethod
    def _posture_keys(scan_id: str) -> Dict[str, str]:
        """Build PK/SK for a CompliancePosture item."""
        return {
            "PK": "POSTURE",
            "SK": f"SCAN#{scan_id}",
        }

    @staticmethod
    def _drift_keys(scan_id: str, control_id: str, drift_id: str) -> Dict[str, str]:
        """Build PK/SK for a DriftEvent item."""
        return {
            "PK": f"DRIFT#SCAN#{scan_id}",
            "SK": f"CTRL#{control_id}#{drift_id}",
        }

    @staticmethod
    def _drift_gsi_keys(control_id: str, timestamp: str) -> Dict[str, str]:
        """Build GSI1 keys for a DriftEvent item."""
        return {
            "GSI1PK": f"DRIFT#CTRL#{control_id}",
            "GSI1SK": timestamp,
        }

    # =========================================================================
    # Write operations
    # =========================================================================

    def put_assessment(self, assessment: ControlAssessment) -> None:
        """Store a single ControlAssessment.

        Overwrites if the same control+scan combination exists (idempotent).
        """
        item = assessment.to_dict()

        # Add single-table keys
        keys = self._assessment_keys(assessment.control_id, assessment.scan_id)
        gsi = self._assessment_gsi_keys(
            assessment.control_id, assessment.scan_id, assessment.status.value
        )
        item.update(keys)
        item.update(gsi)
        item["item_type"] = "ControlAssessment"

        self._table.put_item(Item=item)

    def put_posture(self, posture: CompliancePosture) -> None:
        """Store a CompliancePosture snapshot."""
        item = _floats_to_decimals(posture.to_dict())

        keys = self._posture_keys(posture.scan_id)
        item.update(keys)
        item["item_type"] = "CompliancePosture"

        self._table.put_item(Item=item)

    def put_drift_event(self, event: DriftEvent) -> None:
        """Store a single DriftEvent."""
        item = event.to_dict()

        keys = self._drift_keys(
            event.current_scan_id, event.control_id, event.drift_id
        )
        gsi = self._drift_gsi_keys(event.control_id, event.timestamp)
        item.update(keys)
        item.update(gsi)
        item["item_type"] = "DriftEvent"

        self._table.put_item(Item=item)

    def batch_put_assessments(self, assessments: List[ControlAssessment]) -> int:
        """Batch write assessments in chunks of 25.

        DVA-C02: batch_write_item accepts max 25 items per call.
        Returns the number of items written.
        """
        written = 0
        with self._table.batch_writer() as batch:
            for assessment in assessments:
                item = assessment.to_dict()
                keys = self._assessment_keys(
                    assessment.control_id, assessment.scan_id
                )
                gsi = self._assessment_gsi_keys(
                    assessment.control_id,
                    assessment.scan_id,
                    assessment.status.value,
                )
                item.update(keys)
                item.update(gsi)
                item["item_type"] = "ControlAssessment"
                batch.put_item(Item=item)
                written += 1

        logger.info("Batch wrote %d assessments", written)
        return written

    def batch_put_drift_events(self, events: List[DriftEvent]) -> int:
        """Batch write drift events in chunks of 25."""
        written = 0
        with self._table.batch_writer() as batch:
            for event in events:
                item = event.to_dict()
                keys = self._drift_keys(
                    event.current_scan_id, event.control_id, event.drift_id
                )
                gsi = self._drift_gsi_keys(event.control_id, event.timestamp)
                item.update(keys)
                item.update(gsi)
                item["item_type"] = "DriftEvent"
                batch.put_item(Item=item)
                written += 1

        logger.info("Batch wrote %d drift events", written)
        return written

    def save_scan_results(
        self,
        assessments: List[ControlAssessment],
        posture: CompliancePosture,
        drift_events: Optional[List[DriftEvent]] = None,
    ) -> Dict[str, int]:
        """Save a complete scan's results in one call.

        This is the main entry point after a pipeline run:
            scan → map → assess → save_scan_results(assessments, posture, drifts)

        Returns counts of items written by type.
        """
        counts = {}
        counts["assessments"] = self.batch_put_assessments(assessments)
        self.put_posture(posture)
        counts["posture"] = 1

        if drift_events:
            counts["drift_events"] = self.batch_put_drift_events(drift_events)
        else:
            counts["drift_events"] = 0

        logger.info("Saved scan %s: %s", posture.scan_id, counts)
        return counts

    # =========================================================================
    # Read operations — single item
    # =========================================================================

    def get_assessment(
        self, control_id: str, scan_id: str
    ) -> Optional[ControlAssessment]:
        """Get a single control assessment by control ID and scan ID.

        Access pattern #1: GetItem(PK=CTRL#AC-2, SK=SCAN#{id})
        """
        keys = self._assessment_keys(control_id, scan_id)
        response = self._table.get_item(Key=keys)
        item = response.get("Item")

        if not item:
            return None
        return self._item_to_assessment(item)

    def get_posture(self, scan_id: str) -> Optional[CompliancePosture]:
        """Get compliance posture for a specific scan.

        Access pattern #5: GetItem(PK=POSTURE, SK=SCAN#{id})
        """
        keys = self._posture_keys(scan_id)
        response = self._table.get_item(Key=keys)
        item = response.get("Item")

        if not item:
            return None
        return self._item_to_posture(item)

    # =========================================================================
    # Read operations — queries
    # =========================================================================

    def get_control_history(
        self, control_id: str, limit: int = 50
    ) -> List[ControlAssessment]:
        """Get assessment history for a control across scans.

        Access pattern #2: Query(PK=CTRL#AC-2, SK begins_with SCAN#)
        Returns most recent scans first.
        """
        response = self._table.query(
            KeyConditionExpression=(
                Key("PK").eq(f"CTRL#{control_id}")
                & Key("SK").begins_with("SCAN#")
            ),
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )
        return [self._item_to_assessment(item) for item in response.get("Items", [])]

    def get_scan_assessments(self, scan_id: str) -> List[ControlAssessment]:
        """Get all control assessments for a scan.

        Access pattern #3: Query(GSI1PK=SCAN#{id})
        Uses the GSI1 index.
        """
        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"SCAN#{scan_id}"),
        )
        return [self._item_to_assessment(item) for item in response.get("Items", [])]

    def get_failed_controls(self, scan_id: str) -> List[ControlAssessment]:
        """Get all FAILED controls for a scan.

        Access pattern #4: Query(GSI1PK=SCAN#{id}) + FilterExpression status=FAIL
        """
        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"SCAN#{scan_id}"),
            FilterExpression=Attr("status").eq("FAIL"),
        )
        return [self._item_to_assessment(item) for item in response.get("Items", [])]

    def get_posture_history(self, limit: int = 30) -> List[CompliancePosture]:
        """Get posture snapshots across scans, newest first.

        Access pattern #6: Query(PK=POSTURE, SK begins_with SCAN#, reverse)
        """
        response = self._table.query(
            KeyConditionExpression=(
                Key("PK").eq("POSTURE") & Key("SK").begins_with("SCAN#")
            ),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [self._item_to_posture(item) for item in response.get("Items", [])]

    def get_scan_drift_events(self, scan_id: str) -> List[DriftEvent]:
        """Get all drift events for a scan.

        Access pattern #7: Query(PK=DRIFT#SCAN#{id})
        """
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(f"DRIFT#SCAN#{scan_id}"),
        )
        return [self._item_to_drift_event(item) for item in response.get("Items", [])]

    def get_control_drift_history(
        self, control_id: str, limit: int = 50
    ) -> List[DriftEvent]:
        """Get drift history for a specific control.

        Access pattern #8: Query(GSI1PK=DRIFT#CTRL#{id})
        Returns most recent drift events first.
        """
        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"DRIFT#CTRL#{control_id}"),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [self._item_to_drift_event(item) for item in response.get("Items", [])]

    # =========================================================================
    # Item conversion helpers
    # =========================================================================

    @staticmethod
    def _item_to_assessment(item: Dict[str, Any]) -> ControlAssessment:
        """Convert a DynamoDB item to a ControlAssessment.

        Strips single-table keys (PK, SK, GSI1PK, GSI1SK, item_type)
        before passing to from_dict.
        """
        clean = {
            k: v
            for k, v in item.items()
            if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "item_type")
        }
        return ControlAssessment.from_dict(clean)

    @staticmethod
    def _item_to_posture(item: Dict[str, Any]) -> CompliancePosture:
        """Convert a DynamoDB item to a CompliancePosture."""
        clean = _decimals_to_floats({
            k: v
            for k, v in item.items()
            if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "item_type")
        })
        return CompliancePosture(**{
            k: v for k, v in clean.items()
            if k in CompliancePosture.__dataclass_fields__
        })

    @staticmethod
    def _item_to_drift_event(item: Dict[str, Any]) -> DriftEvent:
        """Convert a DynamoDB item to a DriftEvent."""
        clean = {
            k: v
            for k, v in item.items()
            if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "item_type")
        }
        return DriftEvent(**{
            k: v for k, v in clean.items()
            if k in DriftEvent.__dataclass_fields__
        })
