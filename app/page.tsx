import Link from "next/link";

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-3xl mx-auto px-4 py-24">
          <p className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-4 tracking-wide uppercase">
            Jonathan Lohr
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold text-zinc-900 dark:text-zinc-50 mb-6 leading-tight">
            Sales tools and GTM systems
            <span className="text-zinc-400 dark:text-zinc-500"> for early-stage B2B SaaS.</span>
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-10 leading-relaxed">
            I&apos;ve spent my career inside revenue orgs at cybersecurity and SaaS
            companies — close enough to know what breaks, and close enough to
            engineering to ship the fix.
          </p>
          <div className="flex gap-4 flex-wrap">
            <Link
              href="/sales-tools"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              See sales tools →
            </Link>
            <Link
              href="/projects"
              className="inline-block border border-zinc-300 dark:border-zinc-700 px-6 py-3 rounded-lg font-medium hover:border-zinc-500 dark:hover:border-zinc-500 transition-colors"
            >
              See projects
            </Link>
          </div>
        </div>
      </section>

      {/* Two-up cards */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Sales Tools */}
          <Link
            href="/sales-tools"
            className="group block rounded-xl border border-zinc-200 dark:border-zinc-800 p-8 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
          >
            <div className="text-2xl mb-4">⚡</div>
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              Sales Tools
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed text-sm">
              Live tools you can use right now — quota calculators, pipeline
              diagnostic frameworks, and conversion modeling.
            </p>
            <p className="text-blue-600 dark:text-blue-400 text-sm font-medium mt-4">
              Open the tools →
            </p>
          </Link>

          {/* Projects */}
          <Link
            href="/projects"
            className="group block rounded-xl border border-zinc-200 dark:border-zinc-800 p-8 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
          >
            <div className="text-2xl mb-4">🛠</div>
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              Projects
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed text-sm">
              Engineering work across infra security, data pipelines, and
              full-stack apps — with write-ups on how each one was built.
            </p>
            <p className="text-blue-600 dark:text-blue-400 text-sm font-medium mt-4">
              Browse projects →
            </p>
          </Link>
        </div>
      </section>

      {/* Thin contact strip */}
      <section className="border-t border-zinc-200 dark:border-zinc-800">
        <div className="max-w-3xl mx-auto px-4 py-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-zinc-600 dark:text-zinc-400">
            Want to work together or just want to talk shop?
          </p>
          <a
            href="mailto:jkl914@gmail.com"
            className="text-blue-600 dark:text-blue-400 font-medium hover:underline whitespace-nowrap"
          >
            Get in touch →
          </a>
        </div>
      </section>
    </div>
  );
}
