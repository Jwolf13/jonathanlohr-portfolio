"""
ControlMappingEngine: Maps evidence to NIST controls and assesses compliance.

Takes a ScanResult (raw evidence from collectors) and:
  1. Groups evidence by NIST control ID
  2. Assesses each control's status (PASS, FAIL, PARTIAL, NOT_ASSESSED)
  3. Calculates remediation priority based on evidence severity
  4. Generates aggregate CompliancePosture

DDIA Connection (Ch. 10 — Batch Processing):
    We perform a batch aggregation operation: group evidence by control,
    then compute summary statistics per control. This is the same pattern
    as map-reduce.
"""

try:
    from src.models import (
        ScanResult,
        ControlAssessment,
        ControlStatus,
        CompliancePosture,
        EvidenceItem,
        SEVERITY_WEIGHTS,
        CONTROL_FAMILIES,
    )
except ImportError:
    from ..models import (
        ScanResult,
        ControlAssessment,
        ControlStatus,
        CompliancePosture,
        EvidenceItem,
        SEVERITY_WEIGHTS,
        CONTROL_FAMILIES,
    )

from .control_catalog import get_control, get_all_controls
from datetime import datetime, timezone
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ControlMappingEngine:
    """
    Maps raw evidence to NIST controls and performs compliance assessment.

    This is the second phase of the pipeline:
    ScanResult (from collectors) → List[ControlAssessment] → CompliancePosture
    """

    def assess_all_controls(self, scan_result: ScanResult) -> List[ControlAssessment]:
        """
        Assess all NIST controls based on evidence in the scan result.

        For each control in the catalog:
          - Retrieve evidence items tagged with that control
          - Determine overall status (PASS if all passed, FAIL if any failed, etc.)
          - Calculate highest severity and remediation priority
          - Create ControlAssessment

        Args:
            scan_result: ScanResult from the collector phase.

        Returns:
            List of ControlAssessment, one per control in the catalog.
        """
        assessments = []
        evidence_by_control = scan_result.evidence_by_control

        for control_id, control_meta in get_all_controls().items():
            evidence_list = evidence_by_control.get(control_id, [])

            assessment = self._assess_control(
                control_id,
                control_meta,
                evidence_list,
                scan_result.scan_id,
            )
            assessments.append(assessment)

        logger.info(
            f"Assessed {len(assessments)} controls from {len(scan_result.all_evidence)} evidence items."
        )

        return assessments

    def _assess_control(
        self,
        control_id: str,
        control_meta: Dict,
        evidence_list: List[EvidenceItem],
        scan_id: str,
    ) -> ControlAssessment:
        """
        Assess a single control.

        Args:
            control_id: e.g., 'AC-2'
            control_meta: Control metadata from catalog
            evidence_list: Evidence items tagged with this control
            scan_id: ID of the scan being assessed

        Returns:
            ControlAssessment for this control.
        """
        title = control_meta.get("title", "Unknown Control")
        family = control_meta.get("family", "XX")
        family_name = control_meta.get("family_name", "Unknown Family")
        description = control_meta.get("assessment_criteria", "")
        fedramp_baseline = control_meta.get("fedramp_baselines", ["MODERATE"])[0]

        # Determine control status based on evidence
        if not evidence_list:
            status = ControlStatus.NOT_ASSESSED
            highest_severity = "INFORMATIONAL"
            failed_count = 0
            passed_count = 0
        else:
            # Count passing vs failing evidence
            passed_count = sum(
                1 for e in evidence_list if e.status == "PASSED"
            )
            failed_count = sum(
                1 for e in evidence_list if e.status == "FAILED"
            )

            # Determine overall status
            if failed_count == 0:
                status = ControlStatus.PASS
            elif passed_count > 0:
                status = ControlStatus.PARTIAL
            else:
                status = ControlStatus.FAIL

            # Find highest severity
            highest_severity = self._max_severity(evidence_list)

        # Calculate remediation priority (1-10 scale)
        remediation_priority = self._calculate_priority(
            status,
            highest_severity,
            len(evidence_list),
        )

        assessment = ControlAssessment(
            control_id=control_id,
            control_title=title,
            control_family=family,
            family_name=family_name,
            status=status,
            evidence=evidence_list,
            total_findings=len(evidence_list),
            failed_findings=failed_count,
            passed_findings=passed_count,
            highest_severity=highest_severity,
            fedramp_baseline=fedramp_baseline,
            remediation_priority=remediation_priority,
            assessment_criteria=description,
            scan_id=scan_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return assessment

    @staticmethod
    def _max_severity(evidence_list: List[EvidenceItem]) -> str:
        """
        Find the highest severity level in evidence.

        Args:
            evidence_list: List of EvidenceItem.

        Returns:
            Highest severity level string.
        """
        if not evidence_list:
            return "INFORMATIONAL"

        max_weight = -1
        max_severity = "INFORMATIONAL"

        for evidence in evidence_list:
            weight = SEVERITY_WEIGHTS.get(evidence.severity, 0)
            if weight > max_weight:
                max_weight = weight
                max_severity = evidence.severity

        return max_severity

    @staticmethod
    def _calculate_priority(
        status: ControlStatus,
        severity: str,
        evidence_count: int,
    ) -> int:
        """
        Calculate remediation priority (1-10, where 10 is most urgent).

        Factors:
          - Control status: FAIL > PARTIAL > PASS > NOT_ASSESSED
          - Severity of highest finding: CRITICAL > HIGH > MEDIUM > LOW > INFO
          - Number of failing findings

        Args:
            status: ControlStatus
            severity: Highest severity in evidence
            evidence_count: Total evidence items

        Returns:
            Priority score 1-10.
        """
        # Base score by status
        status_scores = {
            ControlStatus.FAIL: 8,
            ControlStatus.PARTIAL: 5,
            ControlStatus.PASS: 2,
            ControlStatus.NOT_ASSESSED: 1,
            ControlStatus.NOT_APPLICABLE: 0,
        }
        score = status_scores.get(status, 1)

        # Bump up for high severity
        severity_bump = {
            "CRITICAL": 2,
            "HIGH": 1,
            "MEDIUM": 0,
            "LOW": 0,
            "INFORMATIONAL": 0,
        }
        score += severity_bump.get(severity, 0)

        # Bump up if many findings
        if evidence_count > 10:
            score += 1

        # Clamp to 1-10 range
        return max(1, min(10, score))

    def generate_posture(
        self, assessments: List[ControlAssessment]
    ) -> CompliancePosture:
        """
        Generate aggregate CompliancePosture from control assessments.

        Calculates:
          - Total controls and applicable controls
          - Pass/fail/partial/not_assessed counts
          - Compliance percentage
          - Breakdown by family
          - Top 10 failures

        Args:
            assessments: List of ControlAssessment from assess_all_controls.

        Returns:
            CompliancePosture with aggregate statistics.
        """
        if not assessments:
            # Empty scan
            posture = CompliancePosture(
                scan_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_controls=0,
                applicable_controls=0,
                passed=0,
                failed=0,
                partial=0,
                not_assessed=0,
                compliance_percentage=0.0,
                by_family={},
                top_failures=[],
            )
            return posture

        scan_id = assessments[0].scan_id
        timestamp = assessments[0].timestamp

        # Count statuses
        passed = sum(
            1 for a in assessments if a.status == ControlStatus.PASS
        )
        failed = sum(
            1 for a in assessments if a.status == ControlStatus.FAIL
        )
        partial = sum(
            1 for a in assessments if a.status == ControlStatus.PARTIAL
        )
        not_assessed = sum(
            1 for a in assessments if a.status == ControlStatus.NOT_ASSESSED
        )
        not_applicable = sum(
            1 for a in assessments if a.status == ControlStatus.NOT_APPLICABLE
        )

        total = len(assessments)
        applicable = total - not_applicable

        # Calculate compliance percentage
        if applicable > 0:
            compliance_percentage = (passed / applicable) * 100
        else:
            compliance_percentage = 0.0

        # Breakdown by family
        by_family = {}
        for assessment in assessments:
            family = assessment.control_family
            if family not in by_family:
                by_family[family] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "partial": 0,
                    "not_assessed": 0,
                }

            by_family[family]["total"] += 1
            if assessment.status == ControlStatus.PASS:
                by_family[family]["passed"] += 1
            elif assessment.status == ControlStatus.FAIL:
                by_family[family]["failed"] += 1
            elif assessment.status == ControlStatus.PARTIAL:
                by_family[family]["partial"] += 1
            elif assessment.status == ControlStatus.NOT_ASSESSED:
                by_family[family]["not_assessed"] += 1

        # Get top 10 failures (sorted by priority)
        failures = [
            a for a in assessments
            if a.status in (ControlStatus.FAIL, ControlStatus.PARTIAL)
        ]
        failures.sort(key=lambda a: a.remediation_priority, reverse=True)
        top_failures = [
            {
                "control_id": f.control_id,
                "control_title": f.control_title,
                "status": f.status.value,
                "highest_severity": f.highest_severity,
                "remediation_priority": f.remediation_priority,
                "failed_findings": f.failed_findings,
            }
            for f in failures[:10]
        ]

        posture = CompliancePosture(
            scan_id=scan_id,
            timestamp=timestamp,
            total_controls=total,
            applicable_controls=applicable,
            passed=passed,
            failed=failed,
            partial=partial,
            not_assessed=not_assessed,
            compliance_percentage=round(compliance_percentage, 2),
            by_family=by_family,
            top_failures=top_failures,
        )

        logger.info(
            f"Generated compliance posture: {compliance_percentage:.1f}% pass rate "
            f"({passed}/{applicable} applicable controls)"
        )

        return posture
