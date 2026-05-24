import ProjectCard from "@/components/ProjectCard";
import {
  projects,
  categoryLabels,
  type Category,
} from "@/content/projects";

export const metadata = {
  title: "Projects — Jonathan Lohr",
  description: "Case studies across full-stack, data, infra security, and GTM.",
};

const order: Category[] = ["fullstack", "infra", "data", "gtm"];

export default function ProjectsIndex() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <header className="mb-12">
        <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-3">
          Projects
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl">
          Each card opens a case study — the problem, the architecture
          decisions, and what I&apos;d do differently next time.
        </p>
      </header>

      <div className="space-y-12">
        {order.map((category) => {
          const inCategory = projects.filter((p) => p.category === category);
          if (inCategory.length === 0) return null;
          return (
            <section key={category}>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 mb-4">
                {categoryLabels[category]}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {inCategory.map((project) => (
                  <ProjectCard key={project.slug} project={project} />
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
