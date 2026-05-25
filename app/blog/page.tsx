
export const metadata = {
  title: "Blog — Jonathan Lohr",
  description: "Writing on sales, GTM systems, and building.",
};

export default function BlogPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-24 text-center">
      <p className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-4 uppercase tracking-wide">
        Blog
      </p>
      <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-5">
        Coming soon
      </h1>
      <p className="text-zinc-600 dark:text-zinc-400 text-lg leading-relaxed max-w-md mx-auto">
        Writing on sales systems, GTM infrastructure, and what it actually looks
        like to build at the intersection of revenue and engineering.
      </p>
    </div>
  );
}
