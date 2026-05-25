"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

const links = [
  { href: "/sales-tools", label: "Sales Tools" },
  { href: "/projects", label: "Projects" },
  { href: "/blog", label: "Blog" },
];

export default function SiteNav() {
  const pathname = usePathname();
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("theme") === "dark";
  });
  const homeActive = pathname === "/";

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  function toggleDark() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
      <nav className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link
          href="/"
          className={`px-3 py-1.5 rounded-md font-bold transition-colors ${
            homeActive
              ? "bg-blue-600 text-white dark:bg-blue-500 dark:text-white"
              : "text-zinc-900 dark:text-zinc-50 hover:bg-zinc-300 dark:hover:bg-zinc-800"
          }`}
        >
          Jonathan Lohr
        </Link>
        <div className="flex items-center gap-1">
          <ul className="flex gap-1 text-sm">
            {links.map((l) => {
              const active = pathname === l.href;
              return (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                      active
                        ? "bg-blue-600 text-white dark:bg-blue-500 dark:text-white"
                        : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-300 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-50"
                    }`}
                  >
                    {l.label}
                  </Link>
                </li>
              );
            })}
          </ul>
          <button
            onClick={toggleDark}
            className="ml-2 px-2 py-1.5 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors text-sm"
          >
            {dark ? "☀️" : "🌙"}
          </button>
        </div>
      </nav>
    </header>
  );
}
