import { notFound } from "next/navigation";
import CaseStudyLayout from "@/components/CaseStudyLayout";
import { projects, getProject } from "@/content/projects";
import { caseStudies } from "@/content/case-studies";

export function generateStaticParams() {
  return projects.map((p) => ({ slug: p.slug }));
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) return {};
  return {
    title: `${project.title} — Jonathan Lohr`,
    description: project.hook,
  };
}

export default async function CaseStudyPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = getProject(slug);
  const CaseStudy = caseStudies[slug as keyof typeof caseStudies];

  if (!project || !CaseStudy) {
    notFound();
  }

  return (
    <CaseStudyLayout project={project}>
      <CaseStudy />
    </CaseStudyLayout>
  );
}
