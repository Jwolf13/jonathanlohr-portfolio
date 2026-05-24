import Link from "next/link";
import { Section } from "@/components/CaseStudyLayout";

export default function GtmCalculator() {
  return (
    <>
      <Section title="The problem">
        <p>
          Sales reps get assigned a quota and told to &quot;go execute.&quot;
          What they actually need is the math underneath the quota: how many
          calls per day, how many demos per week, at what conversion rates,
          will hit it. Most teams have this in a spreadsheet that two people
          understand and nobody trusts.
        </p>
      </Section>

      <Section title="What it does">
        <p>
          The calculator takes a quota, deal size, and conversion benchmarks,
          and reverse-engineers daily activity targets. It models sensitivity
          — what happens if your meeting-to-opp rate drops 10%? — and surfaces
          GTM health indicators (ramp, pipeline coverage, slippage) using
          published B2B SaaS benchmarks.
        </p>
        <p>
          Everything runs client-side. No data leaves the browser, no account,
          no cookies. The whole thing is a single React component compiled into
          the static export.
        </p>
        <p>
          <Link
            href="/gtm-calculator"
            className="text-blue-600 dark:text-blue-400 font-medium hover:underline"
          >
            Open the calculator →
          </Link>
        </p>
      </Section>

      <Section title="Hard decisions">
        <p>
          <strong>Client-side only.</strong> Tempting to store presets on the
          server, but a sales leader pasting in their pipeline numbers doesn&apos;t
          want them sitting in someone else&apos;s database. Trust costs
          nothing if you never ask for it.
        </p>
      </Section>
    </>
  );
}
