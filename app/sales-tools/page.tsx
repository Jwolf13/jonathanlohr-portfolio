import Link from "next/link";

export const metadata = {
  title: "Sales Tools — Jonathan Lohr",
  description: "Live GTM and sales tools built for early-stage B2B SaaS teams.",
};

const tools = [
  {
    href: "/gtm-calculator",
    title: "GTM Pipeline Calculator",
    description:
      "Reverse-engineer a quota into daily activity targets. Input your ACV, quota, and conversion rates — get a model of exactly what your reps need to do each day to hit the number.",
    tag: "Live tool",
    tagColor: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  },
  {
    href: "/gtm-calculator",
    title: "Pipeline & GTM Tune-Up",
    description:
      "Diagnostic framework for founders and sales leaders at early-stage cybersecurity and B2B SaaS vendors. Covers ICP, territories, sequences, discovery, and stage-by-stage pipeline health.",
    tag: "Framework",
    tagColor: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  },
];

export default function SalesToolsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
          Sales Tools
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400 leading-relaxed">
          Tools and frameworks I&apos;ve built for early-stage B2B SaaS sales
          teams. All calculations run client-side — nothing is sent anywhere.
        </p>
      </div>

      <div className="space-y-6">
        {tools.map((tool) => (
          <Link
            key={tool.title}
            href={tool.href}
            className="group block rounded-xl border border-zinc-200 dark:border-zinc-800 p-7 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {tool.title}
              </h2>
              <span className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${tool.tagColor}`}>
                {tool.tag}
              </span>
            </div>
            <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed text-sm">
              {tool.description}
            </p>
            <p className="text-blue-600 dark:text-blue-400 text-sm font-medium mt-4">
              Open →
            </p>
          </Link>
        ))}
      </div>

      <div className="mt-16 border-t border-zinc-200 dark:border-zinc-800 pt-10">
        <p className="text-zinc-500 dark:text-zinc-400 text-sm">
          More tools in progress.{" "}
          <a
            href="mailto:jkl914@gmail.com"
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Reach out
          </a>{" "}
          if there&apos;s something specific you&apos;d find useful.
        </p>
      </div>
    </div>
  );
}
