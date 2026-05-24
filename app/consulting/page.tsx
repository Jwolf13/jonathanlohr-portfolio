import Link from "next/link";
import ProjectCard from "@/components/ProjectCard";
import { getProjectsByCategory } from "@/content/projects";

export const metadata = {
  title: "Consulting — Jonathan Lohr",
  description: "GTM and pipeline tooling I've built and shipped.",
};

export default function ConsultingPage() {
  const gtm = getProjectsByCategory("gtm");

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-3">
        GTM & Pipeline
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-10 max-w-2xl">
        I&apos;ve spent most of my career inside revenue orgs at early-stage
        cybersecurity and SaaS companies. These are the tools I built along the
        way.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-10">
        {gtm.map((project) => (
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
