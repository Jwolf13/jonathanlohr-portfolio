# AWS Compliance Evidence Collector

An automated NIST 800-53 compliance evidence collection and assessment pipeline for AWS environments. Collects findings from Security Hub, AWS Config, and IAM, maps them to NIST controls, generates PDF compliance reports, and detects drift between scans.

Built as a learning project that connects three domains: **AWS certification prep (DVA-C02)**, **distributed systems theory (Designing Data-Intensive Applications)**, and **hands-on Python engineering**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Account                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Security Hub  │  │  AWS Config  │  │     IAM      │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────────────────────────────────────────┐
   │           Collector Layer (Phase 1)              │
   │  SecurityHubCollector │ ConfigCollector │ IAM    │
   │         → EvidenceItem[]                         │
   └──────────────────────┬──────────────────────────┘
                          │
                          ▼
   ┌─────────────────────────────────────────────────┐
   │        Control Mapping Engine (Phase 2)          │
   │  24 NIST 800-53 controls × 8 families            │
   │  EvidenceItem[] → ControlAssessment[]             │
   │              → CompliancePosture                  │
   └──────────────────────┬──────────────────────────┘
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
   ┌──────────────┐ ┌──────────┐ ┌──────────────────┐
   │ PDF Report   │ │ DynamoDB │ │  Drift Detector   │
   │ (Phase 3)    │ │ Storage  │ │  (Phase 4)        │
   │              │ │ (Phase 4)│ │                    │
   │ reportlab →  │ │ Single-  │ │ ControlAssessment │
   │ compliance-  │ │ table    │ │  (prev vs curr)   │
   │ report.pdf   │ │ design   │ │  → DriftEvent[]   │
   └──────────────┘ └──────────┘ └──────────────────┘
```

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd aws-compliance-collector
pip install -r requirements.txt

# Run tests (no AWS credentials needed)
make test

# Run with coverage
make coverage

# Lint
make lint
```

## Project Structure

```
├── src/
│   ├── models.py                  # Canonical data models (single source of truth)
│   ├── collector/
│   │   ├── security_hub.py        # Security Hub → EvidenceItem[]
│   │   ├── config_collector.py    # AWS Config → EvidenceItem[]
│   │   ├── iam_collector.py       # IAM credential report → EvidenceItem[]
│   │   └── orchestrator.py        # Runs all collectors, builds ScanResult
│   ├── mapper/
│   │   ├── engine.py              # Maps evidence → NIST control assessments
│   │   └── control_catalog.py     # 24 NIST 800-53 controls across 8 families
│   ├── evidence/
│   │   └── pdf_generator.py       # Generates compliance PDF reports
│   ├── drift/
│   │   └── detector.py            # Detects compliance drift between scans
│   ├── storage/
│   │   └── dynamodb.py            # DynamoDB single-table read/write layer
│   └── common/
│       └── retry.py               # Exponential backoff decorator
├── tests/
│   ├── conftest.py                # Shared pytest fixtures
│   ├── test_collectors.py         # botocore.Stubber tests with real ASFF JSON
│   ├── test_storage.py            # moto-backed DynamoDB integration tests
│   ├── test_mapper.py             # Control mapping engine tests
│   ├── test_drift.py              # Drift detection tests
│   ├── test_models.py             # Data model serialization tests
│   ├── test_pdf.py                # PDF generation tests
│   └── test_end_to_end.py         # Full pipeline integration tests
├── terraform/
│   ├── environments/dev/          # Dev environment configuration
│   └── modules/                   # Reusable Terraform modules
│       ├── lambda/                #   Lambda function + IAM role
│       ├── dynamodb/              #   Single-table with GSI
│       ├── api_gateway/           #   REST API
│       ├── cognito/               #   User pool + app client
│       ├── eventbridge/           #   Scheduled scan rule
│       ├── monitoring/            #   CloudWatch alarms + dashboard
│       └── storage/               #   S3 bucket for reports
├── notebooks/                     # 8-phase learning curriculum
│   ├── 00-MASTER-INDEX.ipynb
│   ├── phase-0-foundations/       # Architecture & NIST overview
│   ├── phase-1-data-collection/   # AWS API collection pipeline
│   ├── phase-2-control-mapping/   # Evidence → NIST control mapping
│   ├── phase-3-evidence-pdf/      # PDF report generation
│   ├── phase-4-storage-drift/     # DynamoDB design & drift detection
│   ├── phase-5-dashboard/         # Dashboard API patterns
│   ├── phase-6-iac-deployment/    # Terraform & CI/CD
│   └── phase-7-demo-gtm/         # Demo environment & go-to-market
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── Makefile                       # Build automation
└── requirements.txt               # Python dependencies
```

## Pipeline

The compliance pipeline runs in four stages:

**1. Collect** — Pull findings from Security Hub (ASFF format), AWS Config rules, and IAM credential reports. Each collector produces `EvidenceItem` objects with normalized fields.

**2. Map** — The `ControlMappingEngine` maps evidence to 24 NIST 800-53 Rev 5 controls across 8 families (AC, AU, CM, CP, IA, RA, SC, SI). Each control gets a `ControlAssessment` with status (PASS/FAIL/PARTIAL), severity, and remediation priority. The aggregate `CompliancePosture` tracks the overall compliance percentage.

**3. Report** — Generate a PDF compliance report with executive summary, per-control findings, and remediation recommendations.

**4. Detect Drift** — Compare the current scan's assessments against the previous scan to identify regressions (PASS→FAIL), improvements (FAIL→PASS), and new findings.

## DynamoDB Single-Table Design

The storage layer uses a single DynamoDB table with composite keys and a GSI:

| Entity | PK | SK | GSI1PK | GSI1SK |
|---|---|---|---|---|
| ControlAssessment | `CTRL#{id}` | `SCAN#{scan_id}` | `SCAN#{scan_id}` | `CTRL#{id}#{status}` |
| CompliancePosture | `POSTURE` | `SCAN#{scan_id}` | — | — |
| DriftEvent | `DRIFT#SCAN#{scan_id}` | `CTRL#{id}#{drift_id}` | `DRIFT#CTRL#{id}` | `{timestamp}` |

This supports 8 access patterns: single-item lookups, control history, scan-wide queries, posture timeline, drift tracking, and filtered queries for failed controls.

## Testing

The test suite uses `botocore.Stubber` (for precise API response control) and `moto` (for DynamoDB integration tests). No AWS credentials are needed to run tests.

```bash
make test          # Run all 98 tests
make test-fast     # Skip slow integration tests
make coverage      # Tests with coverage report
make lint          # Ruff linter
```

## NIST 800-53 Controls Covered

8 families, 24 controls, mapped to FedRAMP baselines (Low/Moderate/High):

| Family | Controls |
|---|---|
| AC — Access Control | AC-2, AC-3, AC-6 |
| AU — Audit and Accountability | AU-2, AU-3, AU-9, AU-12 |
| CM — Configuration Management | CM-2, CM-3, CM-6, CM-8 |
| CP — Contingency Planning | CP-13 |
| IA — Identification and Authentication | IA-2, IA-2(1), IA-4, IA-5(1) |
| RA — Risk Assessment | RA-5 |
| SC — System and Communications Protection | SC-7, SC-8, SC-13, SC-28 |
| SI — System and Information Integrity | SI-2, SI-4, SI-12 |

## Learning Connections

Each module connects to exam and book topics:

| Component | DVA-C02 Topics | DDIA Chapters |
|---|---|---|
| Collectors | Security Hub, Config, IAM APIs | Ch. 1 (Reliability) |
| Mapping Engine | Lambda event processing | Ch. 2 (Data Models), Ch. 10 (Batch) |
| PDF Generator | S3 storage patterns | Ch. 3 (Storage and Retrieval) |
| DynamoDB Storage | Single-table design, GSIs, batch writes | Ch. 3 (LSM-trees), Ch. 6 (Partitioning) |
| Drift Detection | DynamoDB Streams, EventBridge | Ch. 11 (Change Data Capture) |
| Dashboard API | API Gateway, Cognito auth | Ch. 5 (Replication) |
| Terraform/CI | CloudFormation, CodePipeline | Ch. 4 (Schema Evolution) |

## License

MIT
