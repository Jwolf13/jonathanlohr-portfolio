import { Section } from "@/components/CaseStudyLayout";

export default function ApexBenchmark() {
  return (
    <>
      <Section title="The problem">
        <p>
          Gym progress is hard to contextualize without external reference
          points. You can track PRs in a notebook, but &ldquo;I squatted
          225&rdquo; is meaningless without a frame of reference. Apex Benchmark
          maps your personal athletic scores — 40-yard dash, vertical jump, back
          squat, VO2 max — against tiered elite standards (NFL Combine, Olympic
          lifting norms) and immediately prescribes a scaled training protocol
          matched to your gap.
        </p>
      </Section>

      <Section title="Architecture">
        <p>
          A FastAPI monolith with a Jinja2 + Alpine.js frontend — no separate
          SPA build step. The backend owns four concerns: a metric registry
          (what tests exist), a benchmark table (elite / average / below-average
          thresholds by gender), a protocol table (scaled workouts keyed to each
          metric), and an evaluation service that scores a submission and
          determines tier.
        </p>
        <p>
          Postgres is the store; SQLAlchemy ORM with Alembic-managed migrations
          keeps schema history in version control. The whole stack runs in a
          two-stage Docker image — builder installs deps into a venv, runtime
          copies only the venv and source, keeping the final image lean.
        </p>
      </Section>

      <Section title="Evaluation engine">
        <p>
          Two scoring functions handle the directional asymmetry of athletic
          tests: timed metrics (lower is better — 40-yard dash) use{" "}
          <code>elite_time / user_time</code>, output metrics (higher is better
          — vertical jump, squat, VO2 max) use <code>user_value / elite_value</code>.
          Both return a ratio where 1.0 means you matched the elite baseline.
          Tier assignment (<em>elite / average / below average</em>) then selects
          which protocol to prescribe.
        </p>
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>Alembic over auto-migration.</strong> Each schema change
          produces a versioned migration file that can be reviewed, rolled back,
          and applied identically across environments. Slower to set up, far
          safer in production.
        </p>
        <p>
          <strong>Alpine.js over a full SPA.</strong> The evaluation form is
          the only interactive surface. Pulling in a React build pipeline for
          one form is overhead that doesn&apos;t pay off — Alpine handles the
          fetch, state binding, and conditional rendering in the same Jinja
          template.
        </p>
        <p>
          <strong>Bodyweight multiplier for squat benchmarks.</strong> Storing
          absolute lb values would make cross-user comparison meaningless.
          The relative multiplier (e.g., 2.0× bodyweight = elite male) is the
          standard used by strength coaches and transfers across weight classes.
        </p>
      </Section>

      <Section title="What I&apos;d do next">
        <p>
          Add a user submission log so each evaluation is persisted and trends
          are visible over time — the data model supports it, the UI doesn&apos;t
          yet. Expand the benchmark table with age-group rows (VO2 max norms
          differ significantly by decade). Add Cognito or Supabase auth so the
          history belongs to a specific user rather than floating in an anonymous
          session.
        </p>
      </Section>
    </>
  );
}
