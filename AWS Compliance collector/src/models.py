"""
Canonical data models for the Compliance Evidence Collector.

EVERY module imports from here. This is the single source of truth for
data structures flowing through the pipeline:

    Collector (Phase 1) → produces ScanResult
    Mapper (Phase 2)    → consumes ScanResult, produces ControlAssessment[]
    PDF Generator (Phase 3) → consumes ControlAssessment[], produces PDF
    Drift Detector (Phase 4) → consumes ControlAssessment[], produces DriftEvent[]
    Dashboard API (Phase 5)  → reads ControlAssessment[] and DriftEvent[]

DDIA Connection (Ch. 4 — Encoding and Evolution):
    These dataclasses define our schema. As the tool evolves, we add fields
    with defaults (forward compatible) and ignore unknown fields when reading
    old data (backward compatible). This is the same principle behind Avro
    and Protobuf schema evolution.

DVA-C02 Connection:
    These models map directly to DynamoDB items. Understanding how Python
    dataclasses serialize to DynamoDB's attribute types is testable knowledge.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Optional
import json
import uuid


# =============================================================================
# Enums
# =============================================================================

class ControlStatus(Enum):
    """Possible assessment statuses for a NIST 800-53 control."""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    NOT_ASSESSED = "NOT_ASSESSED"
    NOT_APPLICABLE = "N/A"


class FindingStatus(Enum):
    """Status of an individual finding from any AWS service."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_EVALUATED = "NOT_EVALUATED"
    SUPPRESSED = "SUPPRESSED"


class SeverityLevel(Enum):
    """Severity levels with numeric weights for priority calculation."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    INFORMATIONAL = 0


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class EvidenceItem:
    """A single piece of compliance evidence from any AWS source.

    This is the atomic unit of evidence. One Security Hub finding, one Config
    rule evaluation, one IAM credential check — each becomes one EvidenceItem.

    Every field is typed and documented because auditors need to trace evidence
    back to its source. The finding_id + source combination is globally unique.
    """
    source: str                # 'security_hub', 'config', 'iam', 'cloudtrail', 'guardduty'
    finding_id: str            # Unique within source (ARN, rule name, etc.)
    title: str                 # Human-readable description
    status: str                # 'PASSED', 'FAILED', 'NOT_EVALUATED'
    severity: str              # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'
    resource_type: str         # AWS resource type (e.g., 'AWS::S3::Bucket')
    resource_id: str           # AWS resource ARN or ID
    timestamp: str             # ISO 8601 when this evidence was collected
    remediation: str = ""      # Recommended fix (from AWS or custom)
    control_ids: List[str] = field(default_factory=list)  # NIST control IDs this maps to
    raw_data: Dict = field(default_factory=dict)  # Original finding JSON (for auditors)

    def to_dict(self) -> Dict:
        """Serialize for JSON/DynamoDB storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvidenceItem':
        """Deserialize from JSON/DynamoDB."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CollectorResult:
    """Output from a single AWS service collector (e.g., SecurityHubCollector).

    Each collector produces one of these. The master orchestrator aggregates
    them into a ScanResult.
    """
    source: str                # Which collector produced this
    status: str                # 'SUCCESS', 'ERROR', 'PARTIAL'
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    raw_findings_count: int = 0
    error_message: str = ""
    duration_ms: int = 0       # How long collection took
    metadata: Dict = field(default_factory=dict)  # Source-specific extras

    def to_dict(self) -> Dict:
        return {
            **{k: v for k, v in asdict(self).items() if k != 'evidence_items'},
            'evidence_items': [e.to_dict() for e in self.evidence_items],
        }


@dataclass
class ScanResult:
    """Complete output from one compliance scan run.

    This is what the Collector Lambda produces. It contains all evidence
    gathered from all AWS services in one scan cycle.

    DDIA Connection (Ch. 11 — Event Sourcing):
        Each ScanResult is an immutable event. We never modify past scans.
        The current compliance state is derived by reading the latest scan.
    """
    scan_id: str               # Unique, sortable: {timestamp}_{uuid}
    scan_start: str            # ISO 8601
    scan_end: str = ""         # ISO 8601 (filled when complete)
    status: str = "IN_PROGRESS"  # 'IN_PROGRESS', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED'
    collector_results: Dict[str, CollectorResult] = field(default_factory=dict)
    all_evidence: List[EvidenceItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    account_id: str = ""
    region: str = ""

    def finalize(self):
        """Mark scan complete and aggregate all evidence."""
        self.scan_end = datetime.now(timezone.utc).isoformat()
        self.all_evidence = []
        for result in self.collector_results.values():
            self.all_evidence.extend(result.evidence_items)
        self.status = "COMPLETED" if not self.errors else "COMPLETED_WITH_ERRORS"

    def to_dict(self) -> Dict:
        return {
            'scan_id': self.scan_id,
            'scan_start': self.scan_start,
            'scan_end': self.scan_end,
            'status': self.status,
            'account_id': self.account_id,
            'region': self.region,
            'errors': self.errors,
            'evidence_count': len(self.all_evidence),
            'collector_results': {
                k: v.to_dict() for k, v in self.collector_results.items()
            },
            'all_evidence': [e.to_dict() for e in self.all_evidence],
        }

    @property
    def evidence_by_control(self) -> Dict[str, List[EvidenceItem]]:
        """Group all evidence by NIST control ID."""
        by_control: Dict[str, List[EvidenceItem]] = {}
        for item in self.all_evidence:
            for cid in item.control_ids:
                by_control.setdefault(cid, []).append(item)
        return by_control


@dataclass
class ControlAssessment:
    """Assessment result for a single NIST 800-53 control.

    This is what the Mapping Engine produces. One per control per scan.
    The Dashboard reads these. The PDF generator formats these.
    """
    control_id: str            # e.g., 'AC-2'
    control_title: str         # e.g., 'Account Management'
    control_family: str        # e.g., 'AC'
    family_name: str           # e.g., 'Access Control'
    status: ControlStatus = ControlStatus.NOT_ASSESSED
    evidence: List[EvidenceItem] = field(default_factory=list)
    total_findings: int = 0
    failed_findings: int = 0
    passed_findings: int = 0
    highest_severity: str = "INFORMATIONAL"
    fedramp_baseline: str = "MODERATE"
    remediation_priority: int = 0   # 1-10 scale, 10 = most urgent
    assessment_criteria: str = ""   # What "passing" means for this control
    scan_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        d['evidence'] = [e.to_dict() for e in self.evidence]
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'ControlAssessment':
        data = dict(data)
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ControlStatus(data['status'])
        if 'evidence' in data:
            data['evidence'] = [EvidenceItem.from_dict(e) for e in data['evidence']]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CompliancePosture:
    """Aggregate compliance posture for a single scan.

    The executive summary. Dashboard shows this as the headline number.
    """
    scan_id: str
    timestamp: str
    total_controls: int = 0
    applicable_controls: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_assessed: int = 0
    compliance_percentage: float = 0.0
    by_family: Dict[str, Dict[str, int]] = field(default_factory=dict)
    top_failures: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DriftEvent:
    """A single compliance drift event — a control changed status between scans.

    DDIA Connection (Ch. 11 — Change Data Capture):
        Drift events are derived from comparing two ScanResults. They form
        a changelog of compliance posture over time.
    """
    drift_id: str              # Unique ID for this event
    control_id: str
    control_title: str
    previous_status: str       # ControlStatus.value
    current_status: str        # ControlStatus.value
    drift_type: str            # 'REGRESSION', 'IMPROVEMENT', 'NEW_FINDING', 'RESOLVED'
    severity: str              # Severity of the drift (based on control priority)
    previous_scan_id: str
    current_scan_id: str
    timestamp: str
    affected_resources: List[str] = field(default_factory=list)
    details: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def is_regression(self) -> bool:
        return self.drift_type == "REGRESSION"


# =============================================================================
# Utility Functions
# =============================================================================

def generate_scan_id() -> str:
    """Generate a unique, sortable scan ID.

    Format: {ISO-timestamp}_{short-uuid}
    Example: 2024-01-15T10-30-00Z_a1b2c3d4

    System Design Interview (Ch. 7 — Unique ID Generator):
        Timestamp prefix = sortable. UUID suffix = unique.
        Same approach as Twitter Snowflake but simpler.
    """
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    short_uuid = str(uuid.uuid4())[:8]
    return f"{timestamp}_{short_uuid}"


def generate_drift_id() -> str:
    """Generate a unique drift event ID."""
    return f"drift-{uuid.uuid4().hex[:12]}"


# =============================================================================
# Constants
# =============================================================================

SEVERITY_WEIGHTS = {
    'CRITICAL': 4,
    'HIGH': 3,
    'MEDIUM': 2,
    'LOW': 1,
    'INFORMATIONAL': 0,
}

CONTROL_FAMILIES = {
    'AC': 'Access Control',
    'AT': 'Awareness and Training',
    'AU': 'Audit and Accountability',
    'CA': 'Assessment, Authorization, and Monitoring',
    'CM': 'Configuration Management',
    'CP': 'Contingency Planning',
    'IA': 'Identification and Authentication',
    'IR': 'Incident Response',
    'MA': 'Maintenance',
    'MP': 'Media Protection',
    'PE': 'Physical and Environmental Protection',
    'PL': 'Planning',
    'PM': 'Program Management',
    'PS': 'Personnel Security',
    'PT': 'PII Processing and Transparency',
    'RA': 'Risk Assessment',
    'SA': 'System and Services Acquisition',
    'SC': 'System and Communications Protection',
    'SI': 'System and Information Integrity',
    'SR': 'Supply Chain Risk Management',
}
