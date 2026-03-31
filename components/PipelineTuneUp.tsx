// components/PipelineTuneUp.tsx
import Link from "next/link";

export default function PipelineTuneUp() {
  return (
    <section className="py-16 border-t border-gray-200">
      <div className="max-w-4xl mx-auto px-4">
        {/* Product heading */}
        <h2 className="text-3xl font-semibold mb-2">
          Pipeline &amp; GTM Tune-Up
        </h2>
        <p className="text-gray-600 mb-6">
          For founders and sales leaders at early-stage cybersecurity and B2B SaaS vendors.
        </p>

        {/* Short description */}
        <p className="mb-6">
          You know the product works. Customers love it once they buy. The problem is
          inconsistent pipeline and a sales motion that feels different with every rep.
        </p>

        {/* 3-step process */}
        <div className="grid gap-6 md:grid-cols-3 mb-10">
          <div>
            <h3 className="font-semibold mb-2">1. Audit your motion</h3>
            <p className="text-sm text-gray-700">
              Review ICP, territories, sequences, discovery, and current pipeline by stage and source.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">2. Build quota math</h3>
            <p className="text-sm text-gray-700">
              Turn quota, ASP, and win rates into clear weekly targets: meetings, opps, and coverage.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">3. Tighten positioning</h3>
            <p className="text-sm text-gray-700">
              Clarify who you are for, which problems you solve, and arm reps with repeatable stories.
            </p>
          </div>
        </div>

        {/* Is this you? */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
          <h3 className="font-semibold mb-3">Is this you?</h3>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-800">
            <li>Pipeline is lumpy and unpredictable even though customers like the product.</li>
            <li>You’re not sure how many meetings or opps your team actually needs each week to hit quota.</li>
            <li>Every AE has a different story and discovery flow, so deals feel random.</li>
            <li>You spend more time fixing pipeline gaps than coaching to a clear plan.</li>
            <li>You know you should tie your product to risk, compliance, or revenue, but calls sound like feature tours.</li>
          </ul>
          <p className="mt-4 text-sm">
            If 2–3 of these sound familiar, the Pipeline &amp; GTM Tune-Up will give you a simple,
            numbers-driven plan your team can execute in the next 90 days.
          </p>
        </div>

        {/* CTA */}
        <Link
          href="/consulting-contact"
          className="inline-block px-5 py-3 bg-black text-white rounded-md text-sm font-medium"
        >
          Let&apos;s see if this fits
        </Link>
      </div>
    </section>
  );
}