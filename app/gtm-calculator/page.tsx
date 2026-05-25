"use client";

import Link from "next/link";
import SalesMotionPlaybook from "@/components/SalesMotionPlaybook";

export default function GTMCalculatorPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900">
      <div className="px-4 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <Link href="/" className="text-blue-600 dark:text-blue-400 font-medium hover:text-blue-700">
              ← Back
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
              GTM Pipeline Calculator
            </h1>
            <p className="text-lg text-zinc-600 dark:text-zinc-400">
              Reverse-engineer your quota into daily activity targets, model conversion sensitivity, and track GTM health indicators.
            </p>
          </div>

          <SalesMotionPlaybook />

          <div className="mt-8 text-center">
            <p className="text-xs text-zinc-400 dark:text-zinc-500">
              Benchmarks derived from published B2B SaaS research. All calculations run client-side — no data is sent anywhere.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
