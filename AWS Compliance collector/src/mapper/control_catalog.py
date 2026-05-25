"""
NIST 800-53 Control Catalog for AWS compliance mapping.

Contains canonical definitions of 25 controls across 8 families:
  - AC: Access Control
  - AU: Audit and Accountability
  - CM: Configuration Management
  - CP: Contingency Planning
  - IA: Identification and Authentication
  - RA: Risk Assessment
  - SC: System and Communications Protection
  - SI: System and Information Integrity

Each control includes:
  - Title and description
  - Family and family name
  - FedRAMP baseline(s) it applies to (LOW, MODERATE, HIGH)
  - Assessment criteria (what "passing" means)

DDIA Connection (Ch. 4 — Encoding and Evolution):
    This catalog defines our schema for control metadata. As new controls
    are added, we maintain backward compatibility with optional fields.
"""

try:
    from src.models import CONTROL_FAMILIES
except ImportError:
    from ..models import CONTROL_FAMILIES


NIST_CONTROL_CATALOG = {
    # =================================================================
    # ACCESS CONTROL (AC) FAMILY
    # =================================================================
    "AC-2": {
        "title": "Account Management",
        "family": "AC",
        "family_name": CONTROL_FAMILIES.get("AC", "Access Control"),
        "description": (
            "Define and document the types of accounts allowed. Assign account "
            "managers. Establish conditions for group and role membership."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All IAM users are documented, have MFA enabled, and access "
            "keys are rotated within 90 days. "
            "FAIL: Accounts exist without authorization or stale accounts are active."
        ),
    },
    "AC-3": {
        "title": "Access Enforcement",
        "family": "AC",
        "family_name": CONTROL_FAMILIES.get("AC", "Access Control"),
        "description": (
            "Enforce approved authorizations for logical access to information "
            "and system resources."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: No public S3 buckets. IAM policies enforce least privilege. "
            "Security groups are restrictive. "
            "FAIL: Overly permissive rules allow unauthorized access."
        ),
    },
    "AC-6": {
        "title": "Least Privilege",
        "family": "AC",
        "family_name": CONTROL_FAMILIES.get("AC", "Access Control"),
        "description": (
            "Employ the principle of least privilege, allowing only authorized "
            "accesses necessary to accomplish assigned tasks."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: No inline policies on users. No wildcard admin policies. "
            "Roles used instead of direct user policies. "
            "FAIL: Overly broad IAM policies or admin access granted unnecessarily."
        ),
    },

    # =================================================================
    # AUDIT AND ACCOUNTABILITY (AU) FAMILY
    # =================================================================
    "AU-2": {
        "title": "Event Logging",
        "family": "AU",
        "family_name": CONTROL_FAMILIES.get("AU", "Audit and Accountability"),
        "description": (
            "Identify the types of events that the system is capable of logging "
            "in support of the audit function."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: CloudTrail enabled in all regions. VPC Flow Logs enabled. "
            "S3 access logging enabled. "
            "FAIL: CloudTrail is disabled or logs are not being stored."
        ),
    },
    "AU-3": {
        "title": "Content of Audit Records",
        "family": "AU",
        "family_name": CONTROL_FAMILIES.get("AU", "Audit and Accountability"),
        "description": (
            "Ensure audit records contain what type of event occurred, when, "
            "where, source, outcome, and identity."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: CloudTrail log file validation enabled. Data events captured "
            "for S3 and Lambda. "
            "FAIL: Audit records lack required detail or validation is disabled."
        ),
    },
    "AU-9": {
        "title": "Protection of Audit Information",
        "family": "AU",
        "family_name": CONTROL_FAMILIES.get("AU", "Audit and Accountability"),
        "description": (
            "Protect audit information and audit logging tools from unauthorized "
            "access, modification, and deletion."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: CloudTrail logs encrypted. Log file validation enabled. "
            "S3 bucket for logs has versioning and MFA delete. "
            "FAIL: Logs are unprotected or integrity validation is missing."
        ),
    },
    "AU-12": {
        "title": "Audit Record Generation",
        "family": "AU",
        "family_name": CONTROL_FAMILIES.get("AU", "Audit and Accountability"),
        "description": (
            "Provide audit record generation capability for the events "
            "defined in AU-2."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: CloudTrail actively recording. Multi-region trail configured. "
            "FAIL: Logging is not configured for critical resources."
        ),
    },

    # =================================================================
    # CONFIGURATION MANAGEMENT (CM) FAMILY
    # =================================================================
    "CM-2": {
        "title": "Baseline Configuration",
        "family": "CM",
        "family_name": CONTROL_FAMILIES.get("CM", "Configuration Management"),
        "description": (
            "Develop, document, and maintain a current baseline configuration "
            "of the system."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All instances managed by Systems Manager. Configuration "
            "baselines documented. "
            "FAIL: No baseline configuration process or AMIs not tagged/tracked."
        ),
    },
    "CM-3": {
        "title": "Change Control",
        "family": "CM",
        "family_name": CONTROL_FAMILIES.get("CM", "Configuration Management"),
        "description": (
            "Implement procedures to manage changes to information systems."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: AWS Config rules enforce immutable infrastructure patterns "
            "and changes are tracked. "
            "FAIL: Configuration drift is not detected or monitored."
        ),
    },
    "CM-6": {
        "title": "Configuration Settings",
        "family": "CM",
        "family_name": CONTROL_FAMILIES.get("CM", "Configuration Management"),
        "description": (
            "Establish and document mandatory configuration settings using "
            "the most restrictive mode consistent with operational requirements."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: Security groups restrict SSH to known IPs. Common ports "
            "not exposed to 0.0.0.0/0. "
            "FAIL: Default or overly permissive configuration settings in use."
        ),
    },
    "CM-8": {
        "title": "System Component Inventory",
        "family": "CM",
        "family_name": CONTROL_FAMILIES.get("CM", "Configuration Management"),
        "description": (
            "Develop and document an inventory of system components that "
            "accurately reflects the system."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All EC2 instances tracked in Systems Manager. All security "
            "groups attached to resources. "
            "FAIL: Untracked resources or incomplete inventory."
        ),
    },

    # =================================================================
    # IDENTIFICATION AND AUTHENTICATION (IA) FAMILY
    # =================================================================
    "IA-2": {
        "title": "Identification and Authentication (Organizational Users)",
        "family": "IA",
        "family_name": CONTROL_FAMILIES.get("IA", "Identification and Authentication"),
        "description": (
            "Uniquely identify and authenticate organizational users."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All users uniquely identified. No shared accounts. MFA "
            "enabled for all users. "
            "FAIL: MFA is not enforced or users have long-lived credentials."
        ),
    },
    "IA-2(1)": {
        "title": "Multi-Factor Authentication to Privileged Accounts",
        "family": "IA",
        "family_name": CONTROL_FAMILIES.get("IA", "Identification and Authentication"),
        "description": (
            "Implement multi-factor authentication for access to privileged "
            "accounts."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: Root account has MFA. All IAM users with console access "
            "have MFA. "
            "FAIL: Privileged accounts lack MFA enforcement."
        ),
    },
    "IA-4": {
        "title": "Identifier Management",
        "family": "IA",
        "family_name": CONTROL_FAMILIES.get("IA", "Identification and Authentication"),
        "description": (
            "Manage information system identifiers for users."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: Users are assigned unique identifiers, access keys are rotated "
            "within 90 days, and unused accounts are removed. "
            "FAIL: Shared accounts or stale credentials exist."
        ),
    },
    "IA-5(1)": {
        "title": "Password-Based Authentication",
        "family": "IA",
        "family_name": CONTROL_FAMILIES.get("IA", "Identification and Authentication"),
        "description": (
            "For password-based authentication: maintain a list of commonly-used "
            "passwords. Enforce minimum complexity."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: Minimum 12 characters. Requires uppercase, lowercase, numbers, "
            "symbols. 90-day rotation. 12-password history. "
            "FAIL: Weak password policy or no expiration requirements."
        ),
    },

    # =================================================================
    # SYSTEM AND COMMUNICATIONS PROTECTION (SC) FAMILY
    # =================================================================
    "SC-7": {
        "title": "Boundary Protection",
        "family": "SC",
        "family_name": CONTROL_FAMILIES.get("SC", "System and Communications Protection"),
        "description": (
            "Monitor and control communications at the external managed "
            "interfaces to the system."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: No unrestricted SSH. No public S3 buckets. Security groups "
            "follow least privilege. "
            "FAIL: Public buckets, unencrypted storage, or unencrypted data transit."
        ),
    },
    "SC-8": {
        "title": "Transmission Confidentiality and Integrity",
        "family": "SC",
        "family_name": CONTROL_FAMILIES.get("SC", "System and Communications Protection"),
        "description": (
            "Protect the confidentiality and integrity of transmitted information."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All S3 buckets require SSL. Load balancers use HTTPS. "
            "HTTP-to-HTTPS redirection enabled. "
            "FAIL: Unencrypted data in transit or missing TLS enforcement."
        ),
    },
    "SC-13": {
        "title": "Cryptographic Protection",
        "family": "SC",
        "family_name": CONTROL_FAMILIES.get("SC", "System and Communications Protection"),
        "description": (
            "Determine the cryptographic uses; and implement cryptographic "
            "mechanisms in accordance with applicable laws."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: S3 buckets encrypted. EBS volumes encrypted. RDS instances "
            "encrypted. KMS keys managed. "
            "FAIL: Data stores lack encryption at rest."
        ),
    },
    "SC-28": {
        "title": "Protection of Information at Rest",
        "family": "SC",
        "family_name": CONTROL_FAMILIES.get("SC", "System and Communications Protection"),
        "description": (
            "Protect the confidentiality and integrity of information at rest."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All data stores encrypted at rest. KMS CMK used where required. "
            "FAIL: Unencrypted data stores or missing KMS key management."
        ),
    },

    # =================================================================
    # SYSTEM AND INFORMATION INTEGRITY (SI) FAMILY
    # =================================================================
    "SI-2": {
        "title": "Flaw Remediation",
        "family": "SI",
        "family_name": CONTROL_FAMILIES.get("SI", "System and Information Integrity"),
        "description": (
            "Identify, report, and correct system flaws. Install security-relevant "
            "updates within defined timeframes."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: All EC2 instances managed by Systems Manager. Patches applied "
            "within 30 days (critical) or 90 days (other). "
            "FAIL: Unpatched systems or no vulnerability management process."
        ),
    },
    "SI-4": {
        "title": "System Monitoring",
        "family": "SI",
        "family_name": CONTROL_FAMILIES.get("SI", "System and Information Integrity"),
        "description": (
            "Monitor the system to detect attacks, indicators of potential "
            "attacks, and unauthorized connections."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: GuardDuty enabled in all regions. Security Hub enabled. "
            "CloudWatch alarms for security events. "
            "FAIL: GuardDuty is not enabled or threat findings are not addressed."
        ),
    },
    "SI-12": {
        "title": "Information Handling and Retention",
        "family": "SI",
        "family_name": CONTROL_FAMILIES.get("SI", "System and Information Integrity"),
        "description": (
            "Handle and retain information within the system in accordance "
            "with applicable retention requirements."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: S3 bucket versioning is enabled and lifecycle policies manage retention. "
            "FAIL: Versioning is not enabled or retention policy is missing."
        ),
    },

    # =================================================================
    # CONTINGENCY PLANNING (CP) FAMILY
    # =================================================================
    "CP-9": {
        "title": "System Backup",
        "family": "CP",
        "family_name": CONTROL_FAMILIES.get("CP", "Contingency Planning"),
        "description": (
            "Conduct backups of user-level information, system-level information, "
            "and system documentation. Protect backup information at storage locations."
        ),
        "fedramp_baselines": ["LOW", "MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: AWS Backup plans exist with daily or more frequent backups. "
            "RDS automated backups enabled with retention >= 7 days. "
            "FAIL: No backup plans configured or retention period is insufficient."
        ),
    },
    "CP-13": {
        "title": "Alternate Processing Site",
        "family": "CP",
        "family_name": CONTROL_FAMILIES.get("CP", "Contingency Planning"),
        "description": (
            "Plan for and support backup and recovery of the system."
        ),
        "fedramp_baselines": ["HIGH"],
        "assessment_criteria": (
            "PASS: RDS has Multi-AZ enabled for high availability and backup "
            "retention configured. "
            "FAIL: Single-AZ deployment or no backups configured."
        ),
    },

    # =================================================================
    # RISK ASSESSMENT (RA) FAMILY
    # =================================================================
    "RA-5": {
        "title": "Vulnerability Scanning",
        "family": "RA",
        "family_name": CONTROL_FAMILIES.get("RA", "Risk Assessment"),
        "description": (
            "Scan information systems and hosted applications for vulnerabilities."
        ),
        "fedramp_baselines": ["MODERATE", "HIGH"],
        "assessment_criteria": (
            "PASS: Security Hub is enabled and findings are reviewed regularly. "
            "FAIL: No vulnerability management tool enabled."
        ),
    },
}


def get_control(control_id: str) -> dict:
    """
    Retrieve a control's metadata from the catalog.

    Args:
        control_id: e.g., 'AC-2', 'IA-5(1)'

    Returns:
        Control dict with title, description, etc. or empty dict if not found.
    """
    return NIST_CONTROL_CATALOG.get(control_id, {})


def get_controls_by_family(family: str) -> dict:
    """
    Retrieve all controls for a given family.

    Args:
        family: e.g., 'AC', 'IA'

    Returns:
        Dict of {control_id: control_dict} for matching family.
    """
    return {
        control_id: control
        for control_id, control in NIST_CONTROL_CATALOG.items()
        if control.get("family") == family
    }


def get_all_controls() -> dict:
    """
    Get the entire NIST control catalog.

    Returns:
        Complete NIST_CONTROL_CATALOG.
    """
    return NIST_CONTROL_CATALOG
