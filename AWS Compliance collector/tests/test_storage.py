"""
Tests for DynamoDB single-table storage using moto.

Validates all 8 access patterns described in src/storage/dynamodb.py:
  1. Get one assessment (GetItem)
  2. Get control history (Query PK)
  3. Get all assessments for a scan (Query GSI1)
  4. Get failed controls for a scan (Query GSI1 + filter)
  5. Get posture for a scan (GetItem)
  6. Get posture history (Query PK, reverse)
  7. Get drift events for a scan (Query PK)
  8. Get drift history for a control (Query GSI1)

Uses moto to spin up a local DynamoDB — no AWS credentials required.
"""

import pytest
import boto3
from moto import mock_aws

from src.storage.dynamodb import DynamoDBStore
from src.models import (
    ControlAssessment,
    CompliancePosture,
    ControlStatus,
    DriftEvent,
)


TABLE_NAME = "test-compliance"


@pytest.fixture
def store():
    """Create a DynamoDBStore backed by moto."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        s = DynamoDBStore(table_name=TABLE_NAME, resource=resource)
        s.create_table()
        yield s


@pytest.fixture
def sample_assessments():
    """Two scans worth of assessments."""
    scan1 = []
    scan2 = []

    for ctrl_id, title, family, fname, status1, status2 in [
        ("AC-2", "Account Management", "AC", "Access Control", ControlStatus.PASS, ControlStatus.FAIL),
        ("AC-3", "Access Enforcement", "AC", "Access Control", ControlStatus.PASS, ControlStatus.PASS),
        ("AU-2", "Event Logging", "AU", "Audit and Accountability", ControlStatus.FAIL, ControlStatus.PASS),
        ("SC-7", "Boundary Protection", "SC", "System and Communications Protection", ControlStatus.FAIL, ControlStatus.FAIL),
    ]:
        scan1.append(ControlAssessment(
            control_id=ctrl_id,
            control_title=title,
            control_family=family,
            family_name=fname,
            status=status1,
            scan_id="2026-05-01T10-00-00Z_aaa111",
            timestamp="2026-05-01T10:00:00Z",
        ))
        scan2.append(ControlAssessment(
            control_id=ctrl_id,
            control_title=title,
            control_family=family,
            family_name=fname,
            status=status2,
            scan_id="2026-05-02T10-00-00Z_bbb222",
            timestamp="2026-05-02T10:00:00Z",
        ))

    return scan1, scan2


@pytest.fixture
def sample_postures():
    """Two posture snapshots."""
    return (
        CompliancePosture(
            scan_id="2026-05-01T10-00-00Z_aaa111",
            timestamp="2026-05-01T10:00:00Z",
            total_controls=4,
            applicable_controls=4,
            passed=2,
            failed=2,
            compliance_percentage=50.0,
        ),
        CompliancePosture(
            scan_id="2026-05-02T10-00-00Z_bbb222",
            timestamp="2026-05-02T10:00:00Z",
            total_controls=4,
            applicable_controls=4,
            passed=2,
            failed=2,
            compliance_percentage=50.0,
        ),
    )


@pytest.fixture
def sample_drifts():
    """Drift events between scan 1 and scan 2."""
    return [
        DriftEvent(
            drift_id="drift-001",
            control_id="AC-2",
            control_title="Account Management",
            previous_status="PASS",
            current_status="FAIL",
            drift_type="REGRESSION",
            severity="HIGH",
            previous_scan_id="2026-05-01T10-00-00Z_aaa111",
            current_scan_id="2026-05-02T10-00-00Z_bbb222",
            timestamp="2026-05-02T10:00:00Z",
            details="AC-2 regressed from PASS to FAIL",
        ),
        DriftEvent(
            drift_id="drift-002",
            control_id="AU-2",
            control_title="Event Logging",
            previous_status="FAIL",
            current_status="PASS",
            drift_type="IMPROVEMENT",
            severity="MEDIUM",
            previous_scan_id="2026-05-01T10-00-00Z_aaa111",
            current_scan_id="2026-05-02T10-00-00Z_bbb222",
            timestamp="2026-05-02T10:00:00Z",
            details="AU-2 improved from FAIL to PASS",
        ),
    ]


# =============================================================================
# Table creation
# =============================================================================

class TestTableCreation:
    def test_create_table(self, store):
        """Table should exist after create_table."""
        tables = store._resource.meta.client.list_tables()["TableNames"]
        assert TABLE_NAME in tables

    def test_create_table_idempotent(self, store):
        """Calling create_table twice should not raise."""
        store.create_table()  # second call
        tables = store._resource.meta.client.list_tables()["TableNames"]
        assert tables.count(TABLE_NAME) == 1


# =============================================================================
# Write + read single items
# =============================================================================

class TestSingleItemOperations:
    """Access patterns #1 and #5: GetItem for assessment and posture."""

    def test_put_get_assessment(self, store, sample_assessments):
        """Pattern #1: write and read a single assessment."""
        scan1, _ = sample_assessments
        ac2 = scan1[0]  # AC-2, PASS

        store.put_assessment(ac2)
        result = store.get_assessment("AC-2", ac2.scan_id)

        assert result is not None
        assert result.control_id == "AC-2"
        assert result.status == ControlStatus.PASS
        assert result.scan_id == ac2.scan_id

    def test_get_assessment_not_found(self, store):
        """GetItem for nonexistent key returns None."""
        result = store.get_assessment("ZZ-99", "nonexistent-scan")
        assert result is None

    def test_put_get_posture(self, store, sample_postures):
        """Pattern #5: write and read a posture snapshot."""
        p1, _ = sample_postures

        store.put_posture(p1)
        result = store.get_posture(p1.scan_id)

        assert result is not None
        assert result.scan_id == p1.scan_id
        assert result.compliance_percentage == 50.0
        assert result.passed == 2
        assert result.failed == 2

    def test_put_assessment_idempotent(self, store, sample_assessments):
        """Writing the same assessment twice should overwrite, not duplicate."""
        scan1, _ = sample_assessments
        ac2 = scan1[0]

        store.put_assessment(ac2)
        store.put_assessment(ac2)

        result = store.get_assessment("AC-2", ac2.scan_id)
        assert result.control_id == "AC-2"


# =============================================================================
# Batch writes
# =============================================================================

class TestBatchOperations:
    def test_batch_put_assessments(self, store, sample_assessments):
        """batch_put_assessments writes all items and returns count."""
        scan1, _ = sample_assessments

        count = store.batch_put_assessments(scan1)
        assert count == 4

        # Verify all 4 are readable
        for a in scan1:
            result = store.get_assessment(a.control_id, a.scan_id)
            assert result is not None
            assert result.control_id == a.control_id

    def test_batch_put_drift_events(self, store, sample_drifts):
        """batch_put_drift_events writes all events and returns count."""
        count = store.batch_put_drift_events(sample_drifts)
        assert count == 2

    def test_save_scan_results(self, store, sample_assessments, sample_postures, sample_drifts):
        """save_scan_results is the full pipeline entry point."""
        _, scan2 = sample_assessments
        _, p2 = sample_postures

        counts = store.save_scan_results(scan2, p2, sample_drifts)

        assert counts["assessments"] == 4
        assert counts["posture"] == 1
        assert counts["drift_events"] == 2

        # Verify posture readable
        posture = store.get_posture(p2.scan_id)
        assert posture is not None

    def test_save_scan_results_no_drift(self, store, sample_assessments, sample_postures):
        """save_scan_results works with no drift events (first scan)."""
        scan1, _ = sample_assessments
        p1, _ = sample_postures

        counts = store.save_scan_results(scan1, p1)
        assert counts["drift_events"] == 0


# =============================================================================
# Query operations
# =============================================================================

class TestQueryOperations:
    """Access patterns #2, #3, #4, #6, #7, #8."""

    def test_get_control_history(self, store, sample_assessments):
        """Pattern #2: Query control across multiple scans."""
        scan1, scan2 = sample_assessments

        store.batch_put_assessments(scan1)
        store.batch_put_assessments(scan2)

        history = store.get_control_history("AC-2")

        assert len(history) == 2
        # Newest first (ScanIndexForward=False)
        assert history[0].scan_id == "2026-05-02T10-00-00Z_bbb222"
        assert history[1].scan_id == "2026-05-01T10-00-00Z_aaa111"
        # Status changed
        assert history[0].status == ControlStatus.FAIL
        assert history[1].status == ControlStatus.PASS

    def test_get_scan_assessments(self, store, sample_assessments):
        """Pattern #3: Query all assessments for a scan via GSI1."""
        scan1, _ = sample_assessments
        store.batch_put_assessments(scan1)

        results = store.get_scan_assessments(scan1[0].scan_id)
        assert len(results) == 4

        control_ids = {r.control_id for r in results}
        assert control_ids == {"AC-2", "AC-3", "AU-2", "SC-7"}

    def test_get_failed_controls(self, store, sample_assessments):
        """Pattern #4: Query failed controls for a scan via GSI1 + filter."""
        scan1, _ = sample_assessments
        store.batch_put_assessments(scan1)

        failed = store.get_failed_controls(scan1[0].scan_id)

        failed_ids = {f.control_id for f in failed}
        assert failed_ids == {"AU-2", "SC-7"}

    def test_get_posture_history(self, store, sample_postures):
        """Pattern #6: Query posture history, newest first."""
        p1, p2 = sample_postures
        store.put_posture(p1)
        store.put_posture(p2)

        history = store.get_posture_history()

        assert len(history) == 2
        # Newest first
        assert history[0].scan_id == "2026-05-02T10-00-00Z_bbb222"
        assert history[1].scan_id == "2026-05-01T10-00-00Z_aaa111"

    def test_get_scan_drift_events(self, store, sample_drifts):
        """Pattern #7: Query drift events for a scan."""
        store.batch_put_drift_events(sample_drifts)

        events = store.get_scan_drift_events("2026-05-02T10-00-00Z_bbb222")

        assert len(events) == 2
        event_controls = {e.control_id for e in events}
        assert event_controls == {"AC-2", "AU-2"}

    def test_get_control_drift_history(self, store, sample_drifts):
        """Pattern #8: Query drift history for a specific control via GSI1."""
        store.batch_put_drift_events(sample_drifts)

        history = store.get_control_drift_history("AC-2")

        assert len(history) == 1
        assert history[0].control_id == "AC-2"
        assert history[0].drift_type == "REGRESSION"

    def test_get_scan_drift_events_empty(self, store):
        """No drift events for a scan returns empty list."""
        events = store.get_scan_drift_events("nonexistent-scan")
        assert events == []

    def test_get_control_history_with_limit(self, store, sample_assessments):
        """Pattern #2 with limit=1 returns only the most recent."""
        scan1, scan2 = sample_assessments
        store.batch_put_assessments(scan1)
        store.batch_put_assessments(scan2)

        history = store.get_control_history("AC-2", limit=1)
        assert len(history) == 1
        assert history[0].scan_id == "2026-05-02T10-00-00Z_bbb222"


# =============================================================================
# Key builder unit tests
# =============================================================================

class TestKeyBuilders:
    """Verify PK/SK patterns match the documented schema."""

    def test_assessment_keys(self):
        keys = DynamoDBStore._assessment_keys("AC-2", "scan-123")
        assert keys == {"PK": "CTRL#AC-2", "SK": "SCAN#scan-123"}

    def test_assessment_gsi_keys(self):
        keys = DynamoDBStore._assessment_gsi_keys("AC-2", "scan-123", "PASS")
        assert keys == {"GSI1PK": "SCAN#scan-123", "GSI1SK": "CTRL#AC-2#PASS"}

    def test_posture_keys(self):
        keys = DynamoDBStore._posture_keys("scan-123")
        assert keys == {"PK": "POSTURE", "SK": "SCAN#scan-123"}

    def test_drift_keys(self):
        keys = DynamoDBStore._drift_keys("scan-123", "AC-2", "drift-001")
        assert keys == {
            "PK": "DRIFT#SCAN#scan-123",
            "SK": "CTRL#AC-2#drift-001",
        }

    def test_drift_gsi_keys(self):
        keys = DynamoDBStore._drift_gsi_keys("AC-2", "2026-05-01T10:00:00Z")
        assert keys == {
            "GSI1PK": "DRIFT#CTRL#AC-2",
            "GSI1SK": "2026-05-01T10:00:00Z",
        }
