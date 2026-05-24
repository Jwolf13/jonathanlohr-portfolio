import Link from "next/link";
import ProjectCard from "@/components/ProjectCard";
import { getFeaturedProjects } from "@/content/projects";

export default function Home() {
  const featured = getFeaturedProjects();

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-4xl mx-auto px-4 py-20">
          <p className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-3">
            Jonathan Lohr
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold text-zinc-900 dark:text-zinc-50 mb-5 leading-tight">
            Engineering, infra security, and GTM systems —
            <span className="text-zinc-500"> shipped end-to-end.</span>
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-8 leading-relaxed max-w-2xl">
            I build the boring parts of go-to-market well — pipelines, data
            plumbing, compliance tooling — and the polished parts that make
            people stop and try them.
          </p>
          <div className="flex gap-4 flex-wrap">
            <Link
              href="/projects"
              className="inline-block bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-blue-700"
            >
              See projects →
            </Link>
            <Link
              href="/about"
              className="inline-block border border-zinc-300 dark:border-zinc-700 px-5 py-2.5 rounded-lg font-medium hover:border-zinc-400"
            >
              About
            </Link>
          </div>
        </div>
      </section>

      {/* Featured projects */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="flex items-baseline justify-between mb-8">
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
            Featured projects
          </h2>
          <Link
            href="/projects"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            All projects →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {featured.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </section>
    </div>
  );
}
