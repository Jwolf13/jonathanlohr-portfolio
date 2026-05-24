"use client";

import { useState } from "react";
import dashboardData from "@/data/processed/occupation_dashboard.json";

type Occupation = (typeof dashboardData.occupations)[number];

export default function NcLaborDashboard() {
  const [selected, setSelected] = useState<Occupation>(
    dashboardData.occupations[0]
  );
  const [search, setSearch] = useState("");

  const filtered = dashboardData.occupations.filter((occ) =>
    occ.title.toLowerCase().includes(search.toLowerCase())
  );

  const totalEmployment = dashboardData.occupations.reduce(
    (sum, occ) => sum + occ.employment_count,
    0
  );

  const counties = selected
    ? [...selected.counties].sort((a, b) => b.employment - a.employment)
    : [];

  return (
    <div className="not-prose">
      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <Stat label="Total employed" value={`${(totalEmployment / 1_000_000).toFixed(1)}M`} />
        <Stat label="Categories" value={String(dashboardData.occupations.length)} />
        <Stat
          label="Top category"
          value={`${dashboardData.occupations[0]?.employment_percentage}%`}
        />
        <Stat label="Data year" value={String(dashboardData.year)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Occupation list */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">
          <input
            type="text"
            placeholder="Search occupations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-3 py-2 mb-3 text-sm bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-300 dark:border-zinc-700"
          />
          <div className="space-y-1.5">
            {filtered.map((occ) => (
              <button
                key={occ.title}
                onClick={() => setSelected(occ)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                  selected.title === occ.title
                    ? "bg-blue-600 text-white"
                    : "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                }`}
              >
                <div className="font-medium">{occ.title}</div>
                <div
                  className={`text-xs ${
                    selected.title === occ.title
                      ? "text-blue-100"
                      : "text-zinc-500 dark:text-zinc-400"
                  }`}
                >
                  {occ.employment_percentage}% of workforce
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Detail */}
        <div className="lg:col-span-2 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-5">
          <h3 className="text-xl font-semibold mb-4 text-zinc-900 dark:text-zinc-50">
            {selected.title}
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-5">
            <Stat
              label="Workers"
              value={`${(selected.employment_count / 1_000_000).toFixed(2)}M`}
            />
            <Stat
              label="% of workforce"
              value={`${selected.employment_percentage}%`}
            />
          </div>

          <h4 className="text-sm font-semibold uppercase tracking-wide text-zinc-500 mb-2">
            Top counties
          </h4>
          <div className="space-y-1.5">
            {counties.slice(0, 8).map((c) => {
              const pct = (c.employment / selected.employment_count) * 100;
              return (
                <div key={c.County}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-zinc-700 dark:text-zinc-300">
                      {c.County}
                    </span>
                    <span className="text-zinc-500 dark:text-zinc-400 tabular-nums">
                      {c.employment.toLocaleString()}
                    </span>
                  </div>
                  <div className="h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded overflow-hidden">
                    <div
                      className="h-full bg-blue-600"
                      style={{ width: `${Math.min(pct * 3, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <p className="text-xs text-zinc-500 mt-4">
        Source: {dashboardData.data_source} · {dashboardData.state} ·{" "}
        {dashboardData.year}
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-lg p-3 border border-zinc-200 dark:border-zinc-800">
      <p className="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
        {value}
      </p>
    </div>
  );
}
