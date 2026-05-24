import Link from "next/link";

export const metadata = {
  title: "About — Jonathan Lohr",
  description: "Background, current focus, and how to reach me.",
};

export default function AboutPage() {
  return (
    <article className="max-w-2xl mx-auto px-4 py-16 space-y-6 text-zinc-700 dark:text-zinc-300 leading-relaxed">
      <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
        About
      </h1>

      <p>
        I&apos;m Jonathan Lohr. I&apos;ve spent most of my career inside revenue
        orgs at early-stage cybersecurity and SaaS companies — close enough to
        sales to know what actually breaks, and close enough to engineering to
        ship the fix instead of writing a slide about it.
      </p>

      <p>
        Lately I build at the intersection of go-to-market and infrastructure:
        compliance tooling on AWS, pipelines that pull from BLS / Census / ESPN,
        full-stack apps that turn the boring back-office parts of revenue into
        something a team can actually use.
      </p>

      <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 pt-6">
        Stack I reach for
      </h2>
      <p>
        Python and Go on the backend, FastAPI / SQLAlchemy / Alembic when
        Postgres is involved. Next.js + Tailwind on the frontend. AWS for
        anything that has to run. Terraform when the infra outlives the demo.
      </p>

      <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 pt-6">
        Contact
      </h2>
      <p>
        Email is the best channel. You can also find me on{" "}
        <a
          href="https://www.linkedin.com/in/jonathan-lohr-20550248/"
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          LinkedIn
        </a>{" "}
        or{" "}
        <a
          href="https://github.com/jwolf13"
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          GitHub
        </a>
        .
      </p>

      <p className="pt-6">
        <Link
          href="/projects"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          See the projects →
        </Link>
      </p>
    </article>
  );
}
