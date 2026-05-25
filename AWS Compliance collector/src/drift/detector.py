"""
DriftDetector: Detects and classifies compliance posture changes between scans.

Compares two ControlAssessment lists (previous scan vs current scan) and
identifies:
  - REGRESSION: Control moved from PASS to FAIL
  - IMPROVEMENT: Control moved from FAIL to PASS
  - NEW_FINDING: Control had no evidence before, now has evidence
  - RESOLVED: Control had failures, now passes

These drift events form a changelog of compliance changes over time.

DDIA Connection (Ch. 11 — Change Data Capture):
    Drift events are derived from comparing two snapshots of control assessments.
    This is the same pattern as CDC (Change Data Capture) in databases:
    compare old vs new state, emit events for changes.
"""

try:
    from src.models import (
        ControlAssessment,
        DriftEvent,
        ControlStatus,
        SEVERITY_WEIGHTS,
        generate_drift_id,
    )
except ImportError:
    from ..models import (
        ControlAssessment,
        DriftEvent,
        ControlStatus,
        SEVERITY_WEIGHTS,
        generate_drift_id,
    )

from datetime import datetime, timezone
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects and classifies compliance drift between two scans.

    Drift is a change in control status from one scan to the next.
    """

    def detect(
        self,
        previous: List[ControlAssessment],
        current: List[ControlAssessment],
    ) -> List[DriftEvent]:
        """
        Detect drift events by comparing previous and current assessments.

        Args:
            previous: List of ControlAssessment from previous scan.
            current: List of ControlAssessment from current scan.

        Returns:
            List of DriftEvent representing all changes.
        """
        # Build lookup dicts for easy comparison
        previous_by_control = {a.control_id: a for a in previous}
        current_by_control = {a.control_id: a for a in current}

        drift_events = []

        # Check all current controls for changes
        for control_id, current_assessment in current_by_control.items():
            previous_assessment = previous_by_control.get(control_id)

            if previous_assessment is None:
                # New control (not in previous scan)
                if current_assessment.status in (
                    ControlStatus.FAIL,
                    ControlStatus.PARTIAL,
                ):
                    # It's a new failure/partial
                    event = self._create_drift_event(
                        control_id=control_id,
                        previous_status=ControlStatus.NOT_ASSESSED,
                        current_status=current_assessment.status,
                        drift_type="NEW_FINDING",
                        current_assessment=current_assessment,
                        previous_assessment=None,
                    )
                    drift_events.append(event)
            else:
                # Control exists in both scans
                if previous_assessment.status != current_assessment.status:
                    # Status changed
                    drift_type = self._classify_drift(
                        previous_assessment.status,
                        current_assessment.status,
                    )
                    event = self._create_drift_event(
                        control_id=control_id,
                        previous_status=previous_assessment.status,
                        current_status=current_assessment.status,
                        drift_type=drift_type,
                        current_assessment=current_assessment,
                        previous_assessment=previous_assessment,
                    )
                    drift_events.append(event)

        # Check for controls that were in previous but not in current
        # (This should rarely happen, but handle it anyway)
        for control_id, previous_assessment in previous_by_control.items():
            if control_id not in current_by_control:
                logger.warning(
                    f"Control {control_id} was in previous scan but not in current scan. "
                    "This may indicate a catalog change."
                )

        logger.info(f"Detected {len(drift_events)} drift events.")
        return drift_events

    @staticmethod
    def _classify_drift(
        previous_status: ControlStatus,
        current_status: ControlStatus,
    ) -> str:
        """
        Classify the type of drift based on status transition.

        Args:
            previous_status: ControlStatus from previous scan.
            current_status: ControlStatus from current scan.

        Returns:
            Drift type string: REGRESSION, IMPROVEMENT, or other change.
        """
        # REGRESSION: moved to worse status
        if (
            previous_status == ControlStatus.PASS and
            current_status in (ControlStatus.FAIL, ControlStatus.PARTIAL)
        ):
            return "REGRESSION"

        # IMPROVEMENT: moved to better status
        if (
            previous_status in (ControlStatus.FAIL, ControlStatus.PARTIAL) and
            current_status == ControlStatus.PASS
        ):
            return "IMPROVEMENT"

        # RESOLVED: partial became pass or fail became pass
        if (
            previous_status in (ControlStatus.FAIL, ControlStatus.PARTIAL) and
            current_status == ControlStatus.PASS
        ):
            return "RESOLVED"

        # Other changes
        if previous_status != current_status:
            return "STATUS_CHANGE"

        return "NO_CHANGE"

    @staticmethod
    def _create_drift_event(
        control_id: str,
        previous_status: ControlStatus,
        current_status: ControlStatus,
        drift_type: str,
        current_assessment: ControlAssessment,
        previous_assessment: ControlAssessment = None,
    ) -> DriftEvent:
        """
        Create a DriftEvent from assessment comparison.

        Args:
            control_id: NIST control ID.
            previous_status: ControlStatus from previous scan.
            current_status: ControlStatus from current scan.
            drift_type: Classification of drift.
            current_assessment: Current ControlAssessment.
            previous_assessment: Previous ControlAssessment or None.

        Returns:
            DriftEvent.
        """
        # Determine severity based on drift type and severity of findings
        if drift_type == "REGRESSION":
            # Regression is always serious
            severity = "CRITICAL" if current_assessment.highest_severity in ("CRITICAL", "HIGH") else "HIGH"
        elif drift_type == "IMPROVEMENT":
            # Improvement is positive
            severity = "LOW"
        elif drift_type == "RESOLVED":
            # Resolved is positive
            severity = "LOW"
        elif drift_type == "NEW_FINDING":
            # New finding severity depends on finding severity
            severity = current_assessment.highest_severity
        else:
            # Generic change
            severity = current_assessment.highest_severity

        # Affected resources: collect from evidence
        affected_resources = []
        if current_assessment.evidence:
            for item in current_assessment.evidence:
                if item.status == "FAILED":
                    affected_resources.append(item.resource_id)

        affected_resources = list(set(affected_resources))[:10]  # Limit to 10

        # Construct detail string
        details = f"Control moved from {previous_status.value} to {current_status.value}."
        if previous_assessment and current_assessment:
            prev_failed = previous_assessment.failed_findings
            curr_failed = current_assessment.failed_findings
            if curr_failed != prev_failed:
                details += f" Failed findings: {prev_failed} → {curr_failed}."

        event = DriftEvent(
            drift_id=generate_drift_id(),
            control_id=control_id,
            control_title=current_assessment.control_title,
            previous_status=previous_status.value,
            current_status=current_status.value,
            drift_type=drift_type,
            severity=severity,
            previous_scan_id=previous_assessment.scan_id if previous_assessment else "unknown",
            current_scan_id=current_assessment.scan_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            affected_resources=affected_resources,
            details=details,
        )

        return event
