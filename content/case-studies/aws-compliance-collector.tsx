import { Section } from "@/components/CaseStudyLayout";

export default function AwsComplianceCollector() {
  return (
    <>
      <Section title="The problem">
        <p>
          NIST 800-53 audits require evidence — screenshots, exports, control
          mappings — that&apos;s tedious to gather by hand and stale the moment
          you collect it. Most teams either rent a GRC SaaS or run a quarterly
          fire drill. Both are expensive.
        </p>
        <p>
          This collector automates the evidence pass for an AWS account: it
          pulls findings from Security Hub, Config, and IAM, maps them to NIST
          controls, and emits an audit-ready PDF plus a drift report against
          the last scan.
        </p>
      </Section>

      <Section title="Architecture">
        <p>
          A Python service built around Boto3 with one collector module per
          source (Security Hub, Config, IAM). A central orchestrator runs them
          in parallel, deduplicates findings, and writes to DynamoDB using a
          single-table design — partition key is{" "}
          <code>account#{"{accountId}"}</code>, sort key is{" "}
          <code>scan#{"{timestamp}"}#{"{finding}"}</code>. Drift detection diffs
          the latest scan against the prior one for the same account.
        </p>
        <p>
          Control mappings live in versioned JSON under{" "}
          <code>mappings/nist-800-53-r5.json</code>. ReportLab renders the PDF
          from a templated layout. Terraform provisions the IAM role, DynamoDB
          table, and an EventBridge schedule.
        </p>
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>DynamoDB single-table over RDS.</strong> Findings are append-
          only and queried by account + time range — exactly what Dynamo&apos;s
          composite key is good at. RDS would&apos;ve been overkill and added a
          subnet group / VPC dance to the Terraform.
        </p>
        <p>
          <strong>botocore.Stubber for tests, not moto.</strong> Stubber gives
          you exact-API-call assertions. Moto&apos;s state simulation drifts
          from real AWS behavior more than you&apos;d expect for edge cases
          like Security Hub finding pagination.
        </p>
        <p>
          <strong>PDF instead of HTML report.</strong> Auditors want a frozen
          artifact they can sign off on. PDF removes ambiguity about whether
          they reviewed today&apos;s data or yesterday&apos;s.
        </p>
      </Section>

      <Section title="What I&apos;d do next">
        <p>
          Add CIS Benchmark mapping alongside NIST. Wire Lambda invocation so
          scans run on Security Hub event changes, not just on a schedule.
          Build a thin dashboard layer (the current notebooks are good for
          learning, not for ops).
        </p>
      </Section>
    </>
  );
}
