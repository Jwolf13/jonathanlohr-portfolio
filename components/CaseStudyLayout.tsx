import Link from "next/link";
import type { ReactNode } from "react";
import type { Project } from "@/content/projects";
import { categoryLabels } from "@/content/projects";

export default function CaseStudyLayout({
  project,
  children,
}: {
  project: Project;
  children: ReactNode;
}) {
  return (
    <article className="max-w-3xl mx-auto px-4 py-12">
      <Link
        href="/projects"
        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        ← All projects
      </Link>

      <header className="mt-6 mb-10 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-2">
          {categoryLabels[project.category]}
        </div>
        <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-3">
          {project.title}
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400 leading-relaxed mb-6">
          {project.hook}
        </p>

        <div className="flex flex-wrap gap-1.5 mb-6">
          {project.stack.map((tech) => (
            <span
              key={tech}
              className="text-xs px-2 py-1 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300"
            >
              {tech}
            </span>
          ))}
        </div>

        <div className="flex gap-4 text-sm">
          {project.github && (
            <a
              href={project.github}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 font-medium hover:underline"
            >
              GitHub →
            </a>
          )}
          {project.demo && (
            <Link
              href={project.demo}
              className="text-blue-600 dark:text-blue-400 font-medium hover:underline"
            >
              Live demo →
            </Link>
          )}
        </div>
      </header>

      <div className="prose prose-zinc dark:prose-invert max-w-none space-y-6 text-zinc-700 dark:text-zinc-300 leading-relaxed">
        {children}
      </div>
    </article>
  );
}

export function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-8">
      <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 mb-3">
        {title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}
