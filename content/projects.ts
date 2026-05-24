// Typed registry of every project shown on the portfolio.
// Add a new project here + create a content/case-studies/<slug>.tsx file,
// then it appears on the homepage, /projects index, and /projects/<slug>.

export type Category = "fullstack" | "data" | "infra" | "gtm";

export type Project = {
  slug: string;
  title: string;
  hook: string;
  category: Category;
  stack: string[];
  github?: string;
  demo?: string;
  status: "live" | "wip" | "archived";
  featured: boolean;
};

export const categoryLabels: Record<Category, string> = {
  fullstack: "Full-stack",
  data: "Data & ETL",
  infra: "Infra & Security",
  gtm: "Tools & GTM",
};

export const projects: Project[] = [
  {
    slug: "channel-stream",
    title: "Channel Stream",
    hook: "Discovery layer that tells sports fans where to watch any live game.",
    category: "fullstack",
    stack: ["Go", "Next.js", "Supabase", "Redis", "AWS ECS", "Playwright"],
    github: "https://github.com/jwolf13/channel-stream",
    status: "wip",
    featured: true,
  },
  {
    slug: "aws-compliance-collector",
    title: "AWS Compliance Collector",
    hook: "Maps Security Hub, Config, and IAM findings to NIST 800-53 controls and ships audit-ready PDFs.",
    category: "infra",
    stack: ["Python", "Boto3", "ReportLab", "DynamoDB", "Terraform", "pytest"],
    github: "https://github.com/jwolf13/aws-compliance-collector",
    status: "wip",
    featured: true,
  },
  {
    slug: "apex-benchmark",
    title: "Apex Benchmark",
    hook: "FastAPI service for benchmarking LLM evaluation runs with Alembic-managed Postgres.",
    category: "fullstack",
    stack: ["Python", "FastAPI", "SQLAlchemy", "Alembic", "Docker"],
    github: "https://github.com/jwolf13/apex-benchmark",
    status: "wip",
    featured: false,
  },
  {
    slug: "nc-labor-market",
    title: "NC Labor Market Dashboard",
    hook: "Python ETL pulls BLS + Census ACS data, ships as a static, filterable React dashboard.",
    category: "data",
    stack: ["Python", "BLS API", "Census ACS", "Next.js", "TypeScript"],
    github: "https://github.com/jwolf13/jonathanlohr-portfolio",
    demo: "/projects/nc-labor-market",
    status: "live",
    featured: true,
  },
  {
    slug: "gtm-calculator",
    title: "GTM Pipeline Calculator",
    hook: "Reverse-engineers a quota into daily activity targets and models conversion sensitivity.",
    category: "gtm",
    stack: ["Next.js", "TypeScript", "Tailwind"],
    demo: "/gtm-calculator",
    status: "live",
    featured: true,
  },
  {
    slug: "data-science-notebooks",
    title: "Statistical Modeling Notebooks",
    hook: "Jupyter notebooks on golf-shot probabilities and applied probability problems.",
    category: "data",
    stack: ["Python", "NumPy", "Pandas", "Jupyter"],
    github: "https://github.com/jwolf13/jonathanlohr-portfolio",
    status: "live",
    featured: false,
  },
];

export function getProject(slug: string): Project | undefined {
  return projects.find((p) => p.slug === slug);
}

export function getFeaturedProjects(): Project[] {
  return projects.filter((p) => p.featured);
}

export function getProjectsByCategory(category: Category): Project[] {
  return projects.filter((p) => p.category === category);
}
