"use client";

import { useMemo, useState } from "react";

type Inputs = {
  annualQuota: number;
  avgDealSize: number;
  winRate: number;
  convRate: number;
  meetingRate: number;
  sellDays: number;
  workWeeks: number;
  dailyTouches: number;
  oppConvRate: number;
};

type HealthInputs = {
  showRate: number;
  meetingToOpp: number;
  multiThread: number;
  stageVelocity: number;
};

type Status = "green" | "yellow" | "red" | "none";

const defaultInputs: Inputs = {
  annualQuota: 900000,
  avgDealSize: 40000,
  winRate: 22,
  convRate: 5,
  meetingRate: 25,
  sellDays: 5,
  workWeeks: 48,
  dailyTouches: 90,
  oppConvRate: 40,
};

const defaultHealth: HealthInputs = {
  showRate: 0,
  meetingToOpp: 0,
  multiThread: 0,
  stageVelocity: 0,
};

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));
const pct = (v: number) => v / 100 || 0;

function calcMetrics(inputs: Inputs) {
  const q = Math.max(1, inputs.annualQuota);
  const d = Math.max(1, inputs.avgDealSize);
  const w = clamp(inputs.winRate, 0.1, 100);
  const rc = clamp(inputs.convRate, 0.1, 100);
  const rm = clamp(inputs.meetingRate, 0.1, 100);
  const oc = clamp(inputs.oppConvRate, 0.1, 100);
  const sd = Math.max(1, inputs.sellDays);
  const ww = Math.max(1, inputs.workWeeks);
  const daily = Math.max(0, inputs.dailyTouches);

  const winsYear = q / d;
  const oppsNeeds = winsYear / pct(w);
  const meetingsNeeds = oppsNeeds / pct(oc);   // fixed: was pct(rm)
  const convsNeeds = meetingsNeeds / pct(rm);  // fixed: was pct(rm) on wrong base
  const touchesNeeds = convsNeeds / pct(rc);

  const weeklyMeetingsNeed = meetingsNeeds / ww;
  const dailyConvs = daily * pct(rc);
  const dailyMeetings = dailyConvs * pct(rm);
  const weeklyMeetingsFromDaily = dailyMeetings * sd;
  const yearlyOppsFromDaily = weeklyMeetingsFromDaily * ww * pct(oc);
  const monthlyMeetingsFromDaily = weeklyMeetingsFromDaily * 4.333;

  const coverageLabel =
    w <= 20 ? "5x+" : w <= 25 ? "4–5x" : w <= 33 ? "3–4x" : "2–3x";
  const pipelineNeeded = oppsNeeds * d;

  return {
    winsYear, oppsNeeds, meetingsNeeds, convsNeeds, touchesNeeds,
    weeklyMeetingsNeed, dailyConvs, dailyMeetings,
    weeklyMeetingsFromDaily, yearlyOppsFromDaily, monthlyMeetingsFromDaily,
    coverageLabel, pipelineNeeded,
  };
}

function statusFor(metric: keyof HealthInputs, value: number): Status {
  if (value === 0) return "none";
  switch (metric) {
    case "showRate":      return value > 70 ? "green" : value >= 55 ? "yellow" : "red";
    case "meetingToOpp":  return value > 35 ? "green" : value >= 25 ? "yellow" : "red";
    case "multiThread":   return value > 60 ? "green" : value >= 40 ? "yellow" : "red";
    case "stageVelocity": return value < 14 ? "green" : value <= 21 ? "yellow" : "red";
  }
}

const badgeClass: Record<Status, string> = {
  green:  "bg-green-100 text-green-800 border border-green-200",
  yellow: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  red:    "bg-red-100 text-red-800 border border-red-200",
  none:   "bg-zinc-100 text-zinc-500 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700",
};

const badgeLabel: Record<Status, string> = {
  green: "Green", yellow: "Yellow", red: "Red", none: "—",
};

const inputLabels: Record<keyof Inputs, string> = {
  annualQuota:  "Annual quota ($)",
  avgDealSize:  "Average deal size ($)",
  winRate:      "Win rate (%)",
  convRate:     "Outreach → conversation (%)",
  meetingRate:  "Conversation → meeting (%)",
  sellDays:     "Selling days / week",
  workWeeks:    "Working weeks / year",
  dailyTouches: "Daily outreach touches",
  oppConvRate:  "Meeting → opportunity (%)",
};

const TABS = [
  { id: "builder" as const,     label: "Quota Builder" },
  { id: "sensitivity" as const, label: "Activity Sensitivity" },
  { id: "health" as const,      label: "GTM Health Check" },
] as const;

type Tab = (typeof TABS)[number]["id"];

export default function SalesMotionPlaybook() {
  const [inputs, setInputs] = useState<Inputs>(defaultInputs);
  const [health, setHealth] = useState<HealthInputs>(defaultHealth);
  const [tab, setTab] = useState<Tab>("builder");

  const update = (key: keyof Inputs, raw: string) => {
    const v = Number(raw);
    if (!Number.isNaN(v)) setInputs((p) => ({ ...p, [key]: v }));
  };

  const updateHealth = (key: keyof HealthInputs, raw: string) => {
    const v = Number(raw);
    if (!Number.isNaN(v)) setHealth((p) => ({ ...p, [key]: v }));
  };

  const m = useMemo(() => calcMetrics(inputs), [inputs]);

  const sensitivity = useMemo(() => ({
    low: calcMetrics({
      ...inputs,
      oppConvRate: Math.max(1, inputs.oppConvRate - 15),
      meetingRate: Math.max(1, inputs.meetingRate - 5),
    }),
    baseline: m,
    high: calcMetrics({
      ...inputs,
      oppConvRate: Math.min(100, inputs.oppConvRate + 10),
      meetingRate: Math.min(100, inputs.meetingRate + 10),
    }),
  }), [inputs, m]);

  const statuses = useMemo(
    () => Object.fromEntries(
      (Object.keys(health) as (keyof HealthInputs)[]).map((k) => [k, statusFor(k, health[k])])
    ) as Record<keyof HealthInputs, Status>,
    [health]
  );

  const filledCount = (Object.values(health) as number[]).filter((v) => v > 0).length;
  const greenCount  = Object.values(statuses).filter((s) => s === "green").length;

  const downloadCSV = () => {
    const rows = [
      ["Metric", "Value"],
      ["Annual quota", `$${inputs.annualQuota.toLocaleString()}`],
      ["Average deal size", `$${inputs.avgDealSize.toLocaleString()}`],
      ["Win rate", `${inputs.winRate}%`],
      ["Outreach → conversation", `${inputs.convRate}%`],
      ["Conversation → meeting", `${inputs.meetingRate}%`],
      ["Meeting → opp", `${inputs.oppConvRate}%`],
      ["Daily touches", String(inputs.dailyTouches)],
      ["Wins needed", m.winsYear.toFixed(1)],
      ["Opps needed", m.oppsNeeds.toFixed(1)],
      ["Meetings needed", m.meetingsNeeds.toFixed(1)],
      ["Weekly meetings target", m.weeklyMeetingsNeed.toFixed(1)],
      ["Pipeline value needed", `$${m.pipelineNeeded.toLocaleString()}`],
      ["Pipeline coverage", m.coverageLabel],
    ];
    const blob = new Blob([rows.map((r) => r.join(",")).join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gtm-plan.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 p-6 shadow-sm">
      {/* Tab nav */}
      <div className="flex gap-1 mb-6 border-b border-zinc-200 dark:border-zinc-700 pb-0">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t -mb-px transition-colors ${
              tab === t.id
                ? "bg-indigo-600 text-white border border-b-white dark:border-b-zinc-900 border-indigo-600"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab 1: Quota Builder ── */}
      {tab === "builder" && (
        <div className="grid gap-5 md:grid-cols-[1fr_1.2fr]">
          {/* Left: inputs */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Sales Motion Inputs</h2>
            {(Object.entries(inputs) as [keyof Inputs, number][]).map(([key, value]) => {
              const isRate = key.includes("Rate") || key === "oppConvRate";
              const isMoney = key === "annualQuota" || key === "avgDealSize";
              return (
                <div key={key}>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    {inputLabels[key]}
                  </label>
                  <input
                    type="number"
                    value={value}
                    step={isMoney ? 1000 : 0.1}
                    min={isRate ? 0 : 1}
                    max={isRate ? 100 : undefined}
                    onChange={(e) => update(key, e.target.value)}
                    className="mt-1 w-full rounded-md border border-zinc-300 dark:border-zinc-600 px-3 py-2 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                </div>
              );
            })}
            <div className="flex gap-3 flex-wrap pt-2">
              <button
                type="button"
                onClick={() => setInputs(defaultInputs)}
                className="rounded-md bg-zinc-100 dark:bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
              >
                Reset defaults
              </button>
              <button
                type="button"
                onClick={downloadCSV}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                Download CSV
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Print
              </button>
            </div>
          </div>

          {/* Right: outputs */}
          <div className="space-y-5">
            {/* Summary */}
            <div className="rounded-xl bg-zinc-50 dark:bg-zinc-800 p-4">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">Live summary</h3>
              <p className="text-sm text-zinc-700 dark:text-zinc-300">
                To hit <strong>${inputs.annualQuota.toLocaleString()}</strong> with {inputs.dailyTouches} touches/day, you need ~{m.monthlyMeetingsFromDaily.toFixed(0)} meetings/month and ~{m.yearlyOppsFromDaily.toFixed(0)} opps/year at current funnel rates.
              </p>
            </div>

            {/* Key targets */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 p-4">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-3">Key annual targets</h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {[
                  ["Wins needed",          m.winsYear],
                  ["Opps needed",          m.oppsNeeds],
                  ["Meetings needed",      m.meetingsNeeds],
                  ["Conversations needed", m.convsNeeds],
                  ["Touches needed",       m.touchesNeeds],
                  ["Opps from daily plan", m.yearlyOppsFromDaily],
                ].map(([label, value]) => (
                  <div key={label as string} className="rounded-lg bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 p-3">
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">{label as string}</p>
                    <p className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">{(value as number).toFixed(1)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Pipeline coverage callout */}
            <div className="rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950 p-4">
              <h3 className="text-lg font-semibold text-indigo-900 dark:text-indigo-100 mb-3">Pipeline Coverage</h3>
              <div className="flex gap-6 mb-4">
                <div>
                  <p className="text-xs text-indigo-600 dark:text-indigo-400">Required multiple</p>
                  <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">{m.coverageLabel}</p>
                  <p className="text-xs text-indigo-500 dark:text-indigo-400">at {inputs.winRate}% win rate</p>
                </div>
                <div>
                  <p className="text-xs text-indigo-600 dark:text-indigo-400">Pipeline value needed</p>
                  <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                    ${(m.pipelineNeeded / 1_000_000).toFixed(2)}M
                  </p>
                  <p className="text-xs text-indigo-500 dark:text-indigo-400">opps × avg deal</p>
                </div>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-indigo-500 dark:text-indigo-400 border-b border-indigo-200 dark:border-indigo-800">
                    <th className="text-left pb-1 font-semibold">Win rate</th>
                    <th className="text-left pb-1 font-semibold">Required coverage</th>
                  </tr>
                </thead>
                <tbody className="text-indigo-800 dark:text-indigo-200">
                  {[
                    ["≤ 20%",  "5x+",  inputs.winRate <= 20],
                    ["21–25%", "4–5x", inputs.winRate > 20 && inputs.winRate <= 25],
                    ["26–33%", "3–4x", inputs.winRate > 25 && inputs.winRate <= 33],
                    ["≥ 34%",  "2–3x", inputs.winRate > 33],
                  ].map(([wr, cov, active]) => (
                    <tr key={wr as string} className={active ? "font-bold" : "opacity-60"}>
                      <td className="py-0.5">{wr as string}</td>
                      <td className="py-0.5">{cov as string}{active ? " ← you are here" : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Funnel ratio */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 p-4">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">Funnel Ratio</h3>
              {[
                ["Touches",       m.touchesNeeds,  "bg-indigo-300 dark:bg-indigo-700"],
                ["Conversations", m.convsNeeds,    "bg-blue-300 dark:bg-blue-700"],
                ["Meetings",      m.meetingsNeeds, "bg-teal-300 dark:bg-teal-700"],
              ].map(([label, value, color]) => {
                const width = m.touchesNeeds > 0
                  ? Math.min(100, ((value as number) / m.touchesNeeds) * 100)
                  : 0;
                return (
                  <div key={label as string} className="mb-2">
                    <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
                      <span>{label as string}</span>
                      <span>{(value as number).toFixed(0)}</span>
                    </div>
                    <div className="h-3 rounded bg-zinc-100 dark:bg-zinc-800">
                      <div className={`h-3 rounded ${color as string}`} style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Weekly schedule */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 p-4">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-3">Weekly Block Schedule</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-700 text-sm">
                  <thead className="bg-zinc-100 dark:bg-zinc-800">
                    <tr>
                      <th className="px-2 py-2 text-left text-xs font-semibold uppercase text-zinc-600 dark:text-zinc-400">Time</th>
                      {["Mon", "Tue", "Wed", "Thu", "Fri"].map((d) => (
                        <th key={d} className="px-2 py-2 text-left text-xs font-semibold uppercase text-zinc-600 dark:text-zinc-400">{d}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                    {[
                      ["8–9 AM",    "Outbound email/LI", "Outbound email/LI", "Outbound",     "Outbound",       "Outbound"],
                      ["9–10 AM",   "Account research",  "Discovery prep",    "Discovery prep","Account research","Pipeline planning"],
                      ["10–12 PM",  "Outbound calls",    "Meetings",          "Meetings",      "Outbound calls", "Meetings"],
                      ["1–2 PM",    "Follow-up",         "Follow-up",         "POC strategy",  "Follow-up",      "1:1 coaching"],
                      ["2–4 PM",    "Outbound sequences","Multi-thread",      "Top-ups",       "Meetings",       "Prospecting"],
                      ["4–5 PM",    "CRM + notes",       "CRM + priorities",  "CRM + hygiene", "Forecast check", "Win debrief"],
                    ].map(([time, ...days]) => (
                      <tr key={time}>
                        <td className="px-2 py-2 font-medium text-zinc-700 dark:text-zinc-300">{time}</td>
                        {days.map((task, i) => (
                          <td key={i} className="px-2 py-2 text-zinc-700 dark:text-zinc-300">{task}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab 2: Activity Sensitivity ── */}
      {tab === "sensitivity" && (
        <div className="space-y-6">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Compares three conversion rate scenarios side-by-side. Inputs are shared with the Quota Builder tab.
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full rounded-xl border border-zinc-200 dark:border-zinc-700 overflow-hidden text-sm">
              <thead>
                <tr>
                  <th className="bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-left font-semibold text-zinc-700 dark:text-zinc-300 w-48">
                    Metric
                  </th>
                  <th className="bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-right font-semibold text-zinc-700 dark:text-zinc-300">
                    <div>Low</div>
                    <div className="text-xs font-normal text-zinc-500">Opp −15%, Mtg −5%</div>
                  </th>
                  <th className="bg-indigo-600 px-4 py-3 text-right font-semibold text-white">
                    <div>Baseline</div>
                    <div className="text-xs font-normal text-indigo-200">Your inputs</div>
                  </th>
                  <th className="bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-right font-semibold text-zinc-700 dark:text-zinc-300">
                    <div>High</div>
                    <div className="text-xs font-normal text-zinc-500">Opp +10%, Mtg +10%</div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                {[
                  {
                    label: "Weekly meetings needed",
                    low:      sensitivity.low.weeklyMeetingsNeed.toFixed(1),
                    baseline: sensitivity.baseline.weeklyMeetingsNeed.toFixed(1),
                    high:     sensitivity.high.weeklyMeetingsNeed.toFixed(1),
                  },
                  {
                    label: "Annual opps needed",
                    low:      sensitivity.low.oppsNeeds.toFixed(0),
                    baseline: sensitivity.baseline.oppsNeeds.toFixed(0),
                    high:     sensitivity.high.oppsNeeds.toFixed(0),
                  },
                  {
                    label: "Annual touches needed",
                    low:      sensitivity.low.touchesNeeds.toFixed(0),
                    baseline: sensitivity.baseline.touchesNeeds.toFixed(0),
                    high:     sensitivity.high.touchesNeeds.toFixed(0),
                  },
                  {
                    label: "Pipeline coverage",
                    low:      sensitivity.low.coverageLabel,
                    baseline: sensitivity.baseline.coverageLabel,
                    high:     sensitivity.high.coverageLabel,
                  },
                  {
                    label: "Pipeline value needed",
                    low:      `$${(sensitivity.low.pipelineNeeded / 1_000_000).toFixed(2)}M`,
                    baseline: `$${(sensitivity.baseline.pipelineNeeded / 1_000_000).toFixed(2)}M`,
                    high:     `$${(sensitivity.high.pipelineNeeded / 1_000_000).toFixed(2)}M`,
                  },
                ].map(({ label, low, baseline, high }) => (
                  <tr key={label} className="bg-white dark:bg-zinc-900">
                    <td className="px-4 py-3 font-medium text-zinc-700 dark:text-zinc-300">{label}</td>
                    <td className="px-4 py-3 text-right text-zinc-600 dark:text-zinc-400">{low}</td>
                    <td className="px-4 py-3 text-right font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950">{baseline}</td>
                    <td className="px-4 py-3 text-right text-zinc-600 dark:text-zinc-400">{high}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="rounded-xl bg-zinc-50 dark:bg-zinc-800 p-4 text-sm text-zinc-600 dark:text-zinc-400">
            <p>If your actual conversion rates run at the low-end scenario, pipeline fill will be significantly below target — and the shortfall won&apos;t be visible until month 3 or 4. Use the Quota Builder tab to dial in your real numbers.</p>
          </div>
        </div>
      )}

      {/* ── Tab 3: GTM Health Check ── */}
      {tab === "health" && (
        <div className="space-y-6">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Enter your observed metrics from the last 30 days. Each indicator is rated against published B2B SaaS benchmarks.
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            {([
              {
                key:    "showRate" as const,
                label:  "Meeting show rate (%)",
                green:  ">70%", yellow: "55–70%", red: "<55%",
                note:   "Below 55% at day 30 is an ICP or sequence mismatch — do not wait for day 60.",
              },
              {
                key:    "meetingToOpp" as const,
                label:  "Meeting → Opp conversion (%)",
                green:  ">35%", yellow: "25–35%", red: "<25%",
                note:   "Below 25% typically indicates a discovery quality problem.",
              },
              {
                key:    "multiThread" as const,
                label:  "Multi-thread rate (% deals with 3+ contacts)",
                label2: "3+ stakeholder contacts",
                green:  ">60%", yellow: "40–60%", red: "<40%",
                note:   "Deals with 3+ contacts close at 2.4x the rate of single-threaded deals.",
              },
              {
                key:    "stageVelocity" as const,
                label:  "Stage velocity: discovery → eval (days)",
                green:  "<14 days", yellow: "14–21 days", red: ">21 days",
                note:   "Slippage here usually means missing economic buyer access.",
              },
            ] as const).map(({ key, label, green, yellow, red, note }) => {
              const s = statuses[key];
              return (
                <div key={key} className="rounded-xl border border-zinc-200 dark:border-zinc-700 p-4 bg-white dark:bg-zinc-900">
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{label}</label>
                  <div className="flex items-center gap-3 mb-3">
                    <input
                      type="number"
                      value={health[key] || ""}
                      placeholder="Enter value"
                      min={0}
                      onChange={(e) => updateHealth(key, e.target.value)}
                      className="w-28 rounded-md border border-zinc-300 dark:border-zinc-600 px-3 py-2 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                    />
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${badgeClass[s]}`}>
                      {badgeLabel[s]}
                    </span>
                  </div>
                  <div className="flex gap-3 text-xs mb-2">
                    <span className="text-green-600 dark:text-green-400">Green: {green}</span>
                    <span className="text-yellow-600 dark:text-yellow-400">Yellow: {yellow}</span>
                    <span className="text-red-600 dark:text-red-400">Red: {red}</span>
                  </div>
                  {s === "red" && (
                    <p className="text-xs text-red-600 dark:text-red-400 italic">{note}</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Summary banner */}
          {filledCount > 0 && (
            <div className={`rounded-xl p-4 border ${
              greenCount === filledCount
                ? "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100"
                : greenCount >= Math.ceil(filledCount / 2)
                  ? "bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800 text-yellow-900 dark:text-yellow-100"
                  : "bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100"
            }`}>
              <p className="font-semibold">
                {greenCount} of {filledCount} entered indicators are healthy
              </p>
              {greenCount < filledCount && (
                <p className="text-sm mt-1 opacity-80">
                  Any Red metric at day 30 is a stop-and-fix signal — more time will not improve the data, only delay the fix.
                </p>
              )}
            </div>
          )}

          {/* Reference table */}
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 overflow-hidden">
            <div className="bg-zinc-100 dark:bg-zinc-800 px-4 py-2 text-xs font-semibold uppercase text-zinc-600 dark:text-zinc-400">
              Threshold Reference
            </div>
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-700 text-sm">
              <thead className="bg-zinc-50 dark:bg-zinc-900">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-zinc-700 dark:text-zinc-300">Metric</th>
                  <th className="px-4 py-2 text-center font-semibold text-green-600">Green</th>
                  <th className="px-4 py-2 text-center font-semibold text-yellow-600">Yellow</th>
                  <th className="px-4 py-2 text-center font-semibold text-red-600">Red — Stop & Fix</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700 bg-white dark:bg-zinc-900">
                {[
                  ["Meeting show rate",         ">70%",     "55–70%",    "<55%"],
                  ["Meeting → Opp rate",        ">35%",     "25–35%",    "<25%"],
                  ["Multi-thread rate",         ">60%",     "40–60%",    "<40%"],
                  ["Stage velocity (disc→eval)","<14 days", "14–21 days",">21 days"],
                ].map(([metric, g, y, r]) => (
                  <tr key={metric}>
                    <td className="px-4 py-2 text-zinc-700 dark:text-zinc-300">{metric}</td>
                    <td className="px-4 py-2 text-center text-green-700 dark:text-green-400">{g}</td>
                    <td className="px-4 py-2 text-center text-yellow-700 dark:text-yellow-400">{y}</td>
                    <td className="px-4 py-2 text-center text-red-700 dark:text-red-400">{r}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
