// Typed registry of sales tools listed on /sales-tools.
// Add a tool here and it appears on the page — no other code changes needed.

export type SalesToolStatus = "live" | "framework" | "wip";

export type SalesTool = {
  slug: string;
  title: string;
  description: string;
  href: string;          // where the "Open" button links to
  status: SalesToolStatus;
  featured?: boolean;
};

export const statusLabels: Record<SalesToolStatus, string> = {
  live: "Live tool",
  framework: "Framework",
  wip: "In progress",
};

export const statusStyles: Record<SalesToolStatus, string> = {
  live: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  framework: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  wip: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
};

export const salesTools: SalesTool[] = [
  {
    slug: "gtm-pipeline-calculator",
    title: "GTM Pipeline Calculator",
    description:
      "Reverse-engineer a quota into daily activity targets. Input your ACV, quota, and conversion rates — get a model of exactly what your reps need to do each day to hit the number.",
    href: "/gtm-calculator",
    status: "live",
    featured: true,
  },
  {
    slug: "pipeline-gtm-tuneup",
    title: "Pipeline & GTM Tune-Up",
    description:
      "Diagnostic framework for founders and sales leaders at early-stage cybersecurity and B2B SaaS vendors. Covers ICP, territories, sequences, discovery, and stage-by-stage pipeline health.",
    href: "/gtm-calculator",
    status: "framework",
    featured: true,
  },
];

export function getSalesTool(slug: string): SalesTool | undefined {
  return salesTools.find((t) => t.slug === slug);
}
