import Link from "next/link";
import ProjectCard from "@/components/ProjectCard";
import { getProjectsByCategory } from "@/content/projects";

export const metadata = {
  title: "Architecture & Infra — Jonathan Lohr",
  description:
    "Infrastructure, security, and architecture case studies — Channel Stream, AWS Compliance Collector, more.",
};

export default function ArchitectureCasesPage() {
  const infra = getProjectsByCategory("infra");
  const fullstack = getProjectsByCategory("fullstack");

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-3">
        Architecture cases
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-10 max-w-2xl">
        Each case walks through the problem, the decisions, and the trade-offs
        I made along the way.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-10">
        {[...infra, ...fullstack].map((project) => (
          <ProjectCard key={project.slug} project={project} />
        ))}
      </div>

      <Link
        href="/projects"
        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        All projects →
      </Link>
    </div>
  );
}
