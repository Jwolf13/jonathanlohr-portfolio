"""
PDFReportGenerator: Creates compliance reports in PDF format.

Generates a professional compliance report with:
  - Cover page (scan date, compliance score)
  - Executive summary table (pass/fail counts by family)
  - Control family sections (individual control assessments)
  - Finding details (evidence items for each control)

Falls back to plain-text report if reportlab is not installed (for testing).

DDIA Connection (Ch. 6 — Partitioning):
    Each control family is rendered as a separate section (partition).
    This matches the idea of dividing large datasets into manageable chunks.
"""

try:
    from src.models import (
        ControlAssessment,
        CompliancePosture,
        ControlStatus,
    )
except ImportError:
    from ..models import (
        ControlAssessment,
        CompliancePosture,
        ControlStatus,
    )

from datetime import datetime, timezone
from typing import List
import logging
import os

logger = logging.getLogger(__name__)

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        PageBreak,
        KeepTogether,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed; PDF generation will use text fallback.")


class PDFReportGenerator:
    """
    Generates compliance reports in PDF or text format.

    Attributes:
        use_reportlab: Whether to use reportlab (if available).
    """

    def __init__(self, use_reportlab: bool = True):
        """
        Initialize PDFReportGenerator.

        Args:
            use_reportlab: If True and reportlab is available, generate PDF.
                          Otherwise, generate plain-text report.
        """
        self.use_reportlab = use_reportlab and REPORTLAB_AVAILABLE

    def generate(
        self,
        assessments: List[ControlAssessment],
        posture: CompliancePosture,
        output_path: str,
    ) -> str:
        """
        Generate compliance report and write to file.

        Args:
            assessments: List of ControlAssessment from mapping engine.
            posture: CompliancePosture aggregate from mapping engine.
            output_path: Path to write report to (*.pdf or *.txt).

        Returns:
            Path to generated report file.
        """
        if self.use_reportlab:
            return self._generate_pdf(assessments, posture, output_path)
        else:
            return self._generate_text(assessments, posture, output_path)

    def _generate_pdf(
        self,
        assessments: List[ControlAssessment],
        posture: CompliancePosture,
        output_path: str,
    ) -> str:
        """
        Generate PDF report using reportlab.

        Args:
            assessments: List of ControlAssessment.
            posture: CompliancePosture aggregate.
            output_path: Path to write PDF to.

        Returns:
            Path to generated PDF file.
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f4788"),
            spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#1f4788"),
            spaceAfter=12,
        )

        # ==== COVER PAGE ====
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("AWS Compliance Report", title_style))
        story.append(Spacer(1, 0.3 * inch))
        story.append(
            Paragraph(
                f"Scan ID: <b>{posture.scan_id}</b>",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"Report Date: <b>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</b>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.5 * inch))

        # Compliance score banner
        compliance_pct = posture.compliance_percentage
        if compliance_pct >= 90:
            score_color = colors.HexColor("#2ecc71")  # Green
        elif compliance_pct >= 70:
            score_color = colors.HexColor("#f39c12")  # Orange
        else:
            score_color = colors.HexColor("#e74c3c")  # Red

        score_para = Paragraph(
            f"<font size=48 color={score_color.hexval()}><b>{compliance_pct:.1f}%</b></font>",
            styles["Normal"],
        )
        story.append(score_para)
        story.append(
            Paragraph("Overall Compliance Score", styles["Normal"])
        )
        story.append(PageBreak())

        # ==== EXECUTIVE SUMMARY ====
        story.append(Paragraph("Executive Summary", heading_style))

        summary_data = [
            ["Metric", "Count"],
            ["Total Controls", str(posture.total_controls)],
            ["Applicable Controls", str(posture.applicable_controls)],
            ["Passed", str(posture.passed)],
            ["Failed", str(posture.failed)],
            ["Partial", str(posture.partial)],
            ["Not Assessed", str(posture.not_assessed)],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Family breakdown
        story.append(Paragraph("Compliance by Family", heading_style))
        family_data = [["Family", "Total", "Passed", "Failed", "Partial"]]
        for family, counts in sorted(posture.by_family.items()):
            family_data.append([
                family,
                str(counts["total"]),
                str(counts["passed"]),
                str(counts["failed"]),
                str(counts["partial"]),
            ])

        family_table = Table(family_data)
        family_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(family_table)
        story.append(PageBreak())

        # ==== CONTROL DETAILS BY FAMILY ====
        assessments_by_family = {}
        for assessment in assessments:
            family = assessment.control_family
            if family not in assessments_by_family:
                assessments_by_family[family] = []
            assessments_by_family[family].append(assessment)

        for family in sorted(assessments_by_family.keys()):
            story.append(
                Paragraph(f"Family: {family}", heading_style)
            )

            for assessment in assessments_by_family[family]:
                # Control header
                status_color = self._status_color(assessment.status)
                control_header = Paragraph(
                    f"<b>{assessment.control_id}: {assessment.control_title}</b> "
                    f"<font color={status_color}>[{assessment.status.value}]</font>",
                    styles["Normal"],
                )
                story.append(control_header)

                # Control details
                details = [
                    f"Severity: {assessment.highest_severity}",
                    f"Priority: {assessment.remediation_priority}/10",
                    f"Evidence: {assessment.total_findings} finding(s)",
                ]
                story.append(
                    Paragraph(" | ".join(details), styles["Normal"])
                )

                # Evidence table
                if assessment.evidence:
                    evidence_data = [
                        ["Source", "Status", "Severity", "Title"]
                    ]
                    for item in assessment.evidence[:5]:  # Limit to 5 per control
                        evidence_data.append([
                            item.source,
                            item.status,
                            item.severity,
                            item.title[:40] + ("..." if len(item.title) > 40 else ""),
                        ])

                    evidence_table = Table(evidence_data)
                    evidence_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ]
                        )
                    )
                    story.append(evidence_table)

                story.append(Spacer(1, 0.2 * inch))

            story.append(PageBreak())

        # Build PDF
        doc.build(story)
        logger.info(f"Generated PDF report: {output_path}")
        return output_path

    def _generate_text(
        self,
        assessments: List[ControlAssessment],
        posture: CompliancePosture,
        output_path: str,
    ) -> str:
        """
        Generate plain-text report (fallback when reportlab not available).

        Args:
            assessments: List of ControlAssessment.
            posture: CompliancePosture aggregate.
            output_path: Path to write text report to.

        Returns:
            Path to generated text file.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        lines = []
        lines.append("=" * 80)
        lines.append("AWS COMPLIANCE REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Scan ID: {posture.scan_id}")
        lines.append(f"Report Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Overall Compliance Score: {posture.compliance_percentage:.1f}%")
        lines.append(f"Total Controls: {posture.total_controls}")
        lines.append(f"Applicable Controls: {posture.applicable_controls}")
        lines.append(f"Passed: {posture.passed}")
        lines.append(f"Failed: {posture.failed}")
        lines.append(f"Partial: {posture.partial}")
        lines.append(f"Not Assessed: {posture.not_assessed}")
        lines.append("")

        lines.append("-" * 80)
        lines.append("COMPLIANCE BY FAMILY")
        lines.append("-" * 80)
        for family, counts in sorted(posture.by_family.items()):
            pct = (counts["passed"] / counts["total"] * 100) if counts["total"] > 0 else 0
            lines.append(
                f"{family}: {counts['passed']}/{counts['total']} passed ({pct:.1f}%)"
            )
        lines.append("")

        lines.append("-" * 80)
        lines.append("TOP FAILURES (HIGH PRIORITY)")
        lines.append("-" * 80)
        for failure in posture.top_failures:
            lines.append(
                f"[Priority {failure['remediation_priority']}/10] "
                f"{failure['control_id']}: {failure['control_title']}"
            )
            lines.append(f"  Status: {failure['status']}, Severity: {failure['highest_severity']}")
            lines.append(f"  Failed Findings: {failure['failed_findings']}")
            lines.append("")

        lines.append("-" * 80)
        lines.append("CONTROL DETAILS")
        lines.append("-" * 80)

        assessments_by_family = {}
        for assessment in assessments:
            family = assessment.control_family
            if family not in assessments_by_family:
                assessments_by_family[family] = []
            assessments_by_family[family].append(assessment)

        for family in sorted(assessments_by_family.keys()):
            lines.append(f"\nFAMILY: {family}")
            lines.append("-" * 40)

            for assessment in assessments_by_family[family]:
                lines.append(
                    f"\n{assessment.control_id}: {assessment.control_title}"
                )
                lines.append(f"Status: {assessment.status.value}")
                lines.append(f"Severity: {assessment.highest_severity}")
                lines.append(f"Priority: {assessment.remediation_priority}/10")
                lines.append(f"Findings: {assessment.total_findings} "
                           f"(Passed: {assessment.passed_findings}, "
                           f"Failed: {assessment.failed_findings})")

                if assessment.evidence:
                    lines.append("Evidence:")
                    for item in assessment.evidence[:3]:
                        lines.append(
                            f"  - [{item.source}] {item.status}: {item.title}"
                        )

        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        report_text = "\n".join(lines)

        with open(output_path, "w") as f:
            f.write(report_text)

        logger.info(f"Generated text report: {output_path}")
        return output_path

    @staticmethod
    def _status_color(status: ControlStatus) -> str:
        """
        Map control status to hex color for PDF.

        Args:
            status: ControlStatus enum.

        Returns:
            Hex color string.
        """
        color_map = {
            ControlStatus.PASS: "#2ecc71",  # Green
            ControlStatus.FAIL: "#e74c3c",  # Red
            ControlStatus.PARTIAL: "#f39c12",  # Orange
            ControlStatus.NOT_ASSESSED: "#95a5a6",  # Gray
            ControlStatus.NOT_APPLICABLE: "#bdc3c7",  # Light gray
        }
        return color_map.get(status, "#000000")
