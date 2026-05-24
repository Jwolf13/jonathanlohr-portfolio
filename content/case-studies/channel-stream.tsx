import { Section } from "@/components/CaseStudyLayout";

export default function ChannelStream() {
  return (
    <>
      <Section title="The problem">
        <p>
          Watching live sports has become a scavenger hunt across a dozen
          paid streamers. Schedule pages tell you when a game is on, but rarely
          which service is broadcasting it. By the time a fan figures it out,
          the first quarter is over.
        </p>
        <p>
          Channel Stream is a discovery layer that ingests live game data and
          tells you exactly where to watch — in one screen, in real time.
        </p>
      </Section>

      <Section title="Architecture">
        <p>
          A Go API + ingestion worker polls ESPN&apos;s public endpoints,
          normalizes the broadcast metadata, and writes to PostgreSQL via
          Supabase. Redis caches feed responses with 90s–10m TTLs depending on
          game state. A Next.js frontend reads the API and renders the watch-now
          / up-next / schedule views. Auth and per-user preferences are stored
          in Supabase.
        </p>
        <p>
          Deployed as Docker images to AWS ECS Fargate, with the frontend on
          CloudFront. Playwright runs E2E tests against a local Supabase stack
          before each deploy.
        </p>
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>Polling vs. webhooks.</strong> ESPN doesn&apos;t offer
          webhooks for live state. I went with adaptive polling — fast during
          active games, slow during off-hours — instead of a fixed cadence. Cut
          API egress by ~70% without losing freshness.
        </p>
        <p>
          <strong>Supabase over self-hosted Postgres.</strong> Auth + DB + RLS
          in one. Trade-off: vendor lock-in on RLS policies, but the velocity
          gain on the auth flow alone was worth it for a solo project.
        </p>
        <p>
          <strong>Go for the API, not Node.</strong> Concurrent polling with
          goroutines is cleaner than Promise.all spaghetti, and the binary
          deploys to ECS without a runtime image bloat.
        </p>
      </Section>

      <Section title="What I&apos;d do next">
        <p>
          Move ingestion to a serverless cron (EventBridge → Lambda) so the ECS
          task only serves the API. Add a Slack / Discord notify on user&apos;s
          favorite team going live. Open-source the broadcast normalization
          mapping since the rest of the ecosystem has the same problem.
        </p>
      </Section>
    </>
  );
}
