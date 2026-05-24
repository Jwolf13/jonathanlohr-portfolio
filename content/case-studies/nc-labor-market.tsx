"use client";

import NcLaborDashboard from "@/components/NcLaborDashboard";
import { Section } from "@/components/CaseStudyLayout";

export default function NcLaborMarket() {
  return (
    <>
      <Section title="The problem">
        <p>
          Public labor data lives in two places that don&apos;t talk to each
          other — BLS (employment and wages by occupation) and Census ACS
          (geography). To answer &quot;which counties in NC are dense in X
          occupation&quot; you have to stitch them yourself.
        </p>
      </Section>

      <Section title="Pipeline">
        <p>
          Python ETL scripts in <code>scripts/</code> pull from the BLS and
          Census APIs, write raw JSON into <code>data/raw/</code>, then
          transform and join into{" "}
          <code>data/processed/occupation_dashboard.json</code>. The static
          site imports the processed file at build time — no server needed,
          no API key on the client.
        </p>
        <p>
          To refresh: <code>python scripts/build_occupation_dashboard.py</code>{" "}
          then push. GitHub Actions rebuilds the static site and CloudFront
          invalidates the cache.
        </p>
      </Section>

      <Section title="Live dashboard">
        <NcLaborDashboard />
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>Bake the data into the build, don&apos;t fetch at runtime.</strong>{" "}
          The dataset is small (~50KB) and updates monthly at most. A build-
          time import means no CORS, no API key in the bundle, and no loading
          spinner. The cost: a deploy is required to see new data, which is
          fine for monthly data.
        </p>
        <p>
          <strong>Categorize at ETL time, not in the UI.</strong> The five
          occupation buckets are derived in Python and stored in the JSON.
          Keeps the React code dumb — it just renders what it&apos;s given.
        </p>
      </Section>
    </>
  );
}
