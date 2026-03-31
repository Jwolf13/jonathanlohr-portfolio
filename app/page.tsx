// app/page.tsx
import Link from "next/link";
import PipelineTuneUp from "@/components/PipelineTuneUp";

export default function Home() {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-10">
      <main className="w-full max-w-5xl bg-white dark:bg-zinc-950 shadow-sm rounded-xl px-6 sm:px-10 py-10 sm:py-14">
        {/* Header / hero */}
        <header className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Jonathan Lohr – Pipeline &amp; GTM for Cybersecurity and SaaS Teams
          </h1>

          <p className="mt-3 text-sm sm:text-base text-zinc-700 dark:text-zinc-300 max-w-2xl">
            I help early-stage cybersecurity and B2B SaaS companies turn complex
            products into a simple, numbers-driven sales motion their team can execute.
          </p>

          <nav className="mt-5 flex flex-wrap gap-4 text-sm text-blue-600">
            <Link href="/projects">Projects</Link>
            <Link href="/architecture-cases">Architecture Cases</Link>
            <Link href="/consulting">Consulting</Link>
            <a
              href="https://www.linkedin.com/in/jonathan-lohr-20550248/"
              target="_blank"
              rel="noreferrer"
            >
              LinkedIn
            </a>
          </nav>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/consulting-contact"
              className="inline-flex items-center justify-center px-5 py-2.5 rounded-md bg-zinc-900 text-white text-sm font-medium"
            >
              Book a working session
            </Link>
            <a
              href="#pipeline-tune-up"
              className="inline-flex items-center justify-center px-5 py-2.5 rounded-md border border-zinc-300 text-sm font-medium text-zinc-900 dark:text-zinc-100"
            >
              See Pipeline &amp; GTM Tune-Up
            </a>
          </div>
        </header>

        {/* Section */}
        <section id="pipeline-tune-up">
          <PipelineTuneUp />
        </section>
      </main>
    </div>
  );
}