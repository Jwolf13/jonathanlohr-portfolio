"use client"

import Link from "next/link"

export function Sidebar() {
  return (
    <nav className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col p-6 flex-shrink-0">
      <div className="mb-10">
        <h1 className="text-xl font-bold text-blue-400">▶ Channel Stream</h1>
        <p className="text-gray-500 text-xs mt-1">Your streaming guide</p>
      </div>

      <ul className="space-y-1">
        <NavLink href="/"          label="Dashboard"   icon="⊞" />
        <NavLink href="/sports"    label="Sports Live" icon="🏟" />
        <NavLink href="/schedule"  label="Schedule"    icon="📅" />
        <NavLink href="/providers" label="Providers"   icon="🔗" />
      </ul>
    </nav>
  )
}

function NavLink({ href, label, icon }: { href: string; label: string; icon: string }) {
  return (
    <li>
      <Link
        href={href}
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors text-sm"
      >
        <span>{icon}</span>
        <span>{label}</span>
      </Link>
    </li>
  )
}
