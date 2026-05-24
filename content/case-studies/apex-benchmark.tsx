import { Section } from "@/components/CaseStudyLayout";

export default function ApexBenchmark() {
  return (
    <>
      <Section title="The problem">
        <p>
          LLM evaluation runs are easy to start and hard to compare over time.
          Notebooks get lost, eval datasets drift, and &quot;is the new model
          better&quot; turns into a vibes check. Apex Benchmark is a service
          for persisting eval runs with enough structure that you can answer
          that question quantitatively.
        </p>
      </Section>

      <Section title="Architecture">
        <p>
          A FastAPI app with SQLAlchemy + Alembic-managed Postgres. Eval runs
          are immutable records keyed by{" "}
          <code>(model, dataset, run_id)</code>. Endpoints accept new runs,
          query historical performance, and emit comparative diffs between any
          two runs. Dockerized so the same image runs in CI and in deployed
          environments.
        </p>
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>Alembic over auto-migration.</strong> Schema diffs in version
          control instead of behind-the-scenes magic. Slower at the start,
          fewer 2am rollbacks later.
        </p>
        <p>
          <strong>FastAPI over Flask.</strong> Pydantic-validated request and
          response models are the cheapest documentation you can write — they
          generate an OpenAPI spec for free.
        </p>
      </Section>

      <Section title="What I&apos;d do next">
        <p>
          Add a small UI for browsing run history (the API is the source of
          truth, but a UI accelerates the comparison loop). Add support for
          streaming uploads of large eval datasets so the API doesn&apos;t
          time-out on big runs.
        </p>
      </Section>
    </>
  );
}
