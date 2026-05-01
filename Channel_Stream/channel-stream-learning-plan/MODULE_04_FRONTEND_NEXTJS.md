# Module 4 — Frontend: The Next.js Dashboard
### Building the Web Companion that Talks to Your API

---

> **Goal**: Build a real, deployable web dashboard that displays all four Channel Stream feeds using Next.js. This is the companion app users open on their phone or browser to manage their profiles, adjust preferences, and see their feeds — while the TV experience is handled by the Roku/Fire TV apps.

> **Time**: ~6–8 hours

---

## 4.1 Why Next.js? And How It Relates to React

### React: The Foundation

React is a JavaScript library for building user interfaces. The core idea: instead of manually manipulating the HTML of a webpage, you describe what the page *should look like* based on data — and React updates the DOM for you.

```jsx
// Without React (manual DOM manipulation — messy):
document.getElementById('title').innerText = 'Severance';
document.getElementById('provider').innerText = 'Apple TV+';
document.getElementById('progress').style.width = '62%';

// With React (declarative — just describe the result):
function FeedCard({ title, provider, progressPct }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <p>{provider}</p>
      <div className="progress" style={{ width: `${progressPct}%` }} />
    </div>
  );
}
```

The JSX syntax (`<div>`, `<h3>`) looks like HTML but it's actually JavaScript. React converts it to real HTML.

### Next.js: React with Superpowers

Next.js is a framework built on top of React. It adds:

| Feature | What It Does |
|---|---|
| **File-based routing** | A file at `app/feed/page.tsx` automatically becomes the page `/feed` |
| **Server-side rendering** | The server builds the HTML before sending it to the browser (faster initial load, better SEO) |
| **API routes** | You can put backend endpoints inside the Next.js project at `app/api/...` |
| **TypeScript support** | Built-in — you get type checking for free |
| **Image optimization** | Automatic image resizing and lazy loading |
| **Deployment** | One command to deploy to Vercel (free tier available) |

---

## 4.2 Create the Next.js Project

```bash
cd ~/channel-stream
```

The Next.js project already lives at the repository root (not in a `web/` subfolder). The folder structure:
```
channel-stream/
├── src/
│   └── app/
│       ├── layout.tsx       ← Shell that wraps all pages
│       ├── page.tsx         ← Homepage (/)
│       └── globals.css      ← Global styles
├── public/                  ← Static files (images, icons)
├── next.config.ts           ← Next.js configuration
├── tailwind.config.ts       ← Tailwind CSS configuration
├── tsconfig.json            ← TypeScript configuration
├── package.json             ← Node.js dependencies (runs on port 3001)
├── cmd/server/              ← Go backend
├── internal/                ← Go business logic
└── supabase/                ← Database migrations
```

### Start the Frontend Dev Server

```bash
cd ~/channel-stream
npm run dev
```

Open http://localhost:3001 — you should see the Next.js welcome page. The dev server hot-reloads — any file you save instantly updates the browser. No manual refresh needed.

---

## 4.3 Understanding TypeScript (JavaScript + Types)

TypeScript is JavaScript that lets you label what type of data every variable holds. This catches bugs before you even run your code.

```typescript
// Plain JavaScript — no type labels
function formatProgress(pct) {
  return pct + "%";  // What if someone passes "not a number"? Runtime crash.
}

// TypeScript — explicit types
function formatProgress(pct: number): string {
  return `${pct}%`;  // TypeScript WILL NOT COMPILE if pct is not a number
}

// TypeScript catches mistakes before you run:
formatProgress("hello"); // ERROR: Argument of type 'string' is not assignable to parameter of type 'number'
```

### Defining Types for Channel Stream Data

When your Go API returns JSON, TypeScript needs to know the "shape" of that data.

Create `src/types/api.ts`:

```typescript
// These types MIRROR the structs in your Go backend (internal/feed/feed.go)
// Keeping them in sync is a discipline — if Go changes, update TypeScript too.

export interface FeedItem {
  content_id: string;
  title: string;
  type: "movie" | "series" | "episode" | "sport_event";  // union type: must be one of these
  provider: string;
  progress_pct?: number;          // ? means optional (may be undefined)
  resume_position_sec?: number;
  rating?: string;
  deeplink?: string;
  last_watched?: string;          // ISO date string
  score?: number;
  reason?: string;
}

export interface FeedResponse {
  feed: string;
  generated_at: string;
  items: FeedItem[];              // array of FeedItem
  count: number;
}

export interface WatchOption {
  network: string;
  app?: string;           // streaming app slug; empty = cable only
  app_display: string;    // "Disney+ (ESPN)", "Paramount+", "Fox (cable/satellite)"
  requires_cable: boolean;
}

export interface TeamInfo {
  id: string;
  name: string;
  abbr: string;
}

export interface GameScore {
  home: string;
  away: string;
}

export interface SportEvent {
  game_id: string;
  sport: string;
  league: string;
  home_team: TeamInfo;
  away_team: TeamInfo;
  start_time: string;
  status: "live" | "scheduled" | "final";
  status_detail?: string;   // "Q3 4:12", "Bot 6th", "2nd Period"
  score?: GameScore;
  venue?: string;
  watch_on: WatchOption[];
}

export interface SportsResponse {
  feed: string;
  generated_at: string;
  events: SportEvent[];
  count: number;
}

export interface ProviderLink {
  provider: string;
  linked_at: string;
  token_expires?: string;
  status: "valid" | "expired" | "expiring_soon" | "never_expires";
}

export interface ProvidersResponse {
  account_id: string;
  providers: ProviderLink[];
  count: number;
}
```

---

## 4.4 Understanding Tailwind CSS

Tailwind is a CSS framework where instead of writing CSS files, you apply small utility classes directly in your HTML/JSX.

```html
<!-- Old way: write CSS separately -->
<div class="card">...</div>
/* In CSS: .card { background: white; border-radius: 8px; padding: 16px; } */

<!-- Tailwind way: classes describe the style inline -->
<div class="bg-white rounded-lg p-4 shadow-md hover:shadow-lg transition-shadow">
```

Common Tailwind classes you'll use:

| Class | What It Does |
|---|---|
| `flex` | Makes a container use flexbox layout |
| `grid` | Makes a container use grid layout |
| `p-4` | Padding of 16px (1rem) on all sides |
| `px-4 py-2` | Padding 16px horizontal, 8px vertical |
| `m-4` | Margin of 16px |
| `gap-4` | Gap of 16px between grid/flex children |
| `rounded-lg` | Border radius (rounded corners) |
| `bg-gray-900` | Background color: dark gray |
| `text-white` | Text color: white |
| `text-sm` | Font size: small |
| `font-bold` | Font weight: bold |
| `w-full` | Width: 100% of container |
| `max-w-4xl` | Maximum width: 896px |
| `mx-auto` | Auto horizontal margin (centers the element) |
| `hover:bg-blue-700` | On hover: blue background |
| `hidden md:block` | Hidden on mobile, visible on medium+ screens |

---

## 4.5 Create an API Client (`src/lib/api.ts`)

This file centralizes all calls to your Go backend. Every time you need data, you call these functions — you never write `fetch()` directly in a component.

```typescript
// src/lib/api.ts

import type { FeedResponse, SportsResponse, ProvidersResponse } from "@/types/api";

// The base URL for your Go backend
// In development: Go server running locally
// In production: will be your deployed API URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Test profile and account from seed.sql
const DEFAULT_PROFILE_ID = "00000000-0000-0000-0000-000000000002";
const DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001";

// Helper: make a GET request and parse JSON
// Generic function: <T> means "this function works with any type, and returns that type"
async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    // In production, add: Authorization: `Bearer ${token}`
  });

  if (!response.ok) {
    // response.ok is true for 200-299 status codes
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

// ── API Functions ─────────────────────────────────────────────────────────────

export async function getUpNextFeed(profileId = DEFAULT_PROFILE_ID): Promise<FeedResponse> {
  return get<FeedResponse>(`/v1/feed/up-next?profile_id=${profileId}`);
}

export async function getWatchNowFeed(
  profileId = DEFAULT_PROFILE_ID,
  accountId = DEFAULT_ACCOUNT_ID
): Promise<FeedResponse> {
  return get<FeedResponse>(
    `/v1/feed/watch-now?profile_id=${profileId}&account_id=${accountId}`
  );
}

export async function getSportsLive(profileId = DEFAULT_PROFILE_ID): Promise<SportsResponse> {
  return get<SportsResponse>(`/v1/sports/live?profile_id=${profileId}`);
}

export async function getSportsSchedule(profileId = DEFAULT_PROFILE_ID): Promise<SportsResponse> {
  return get<SportsResponse>(`/v1/sports/schedule?profile_id=${profileId}`);
}

export async function getLinkedProviders(accountId = DEFAULT_ACCOUNT_ID): Promise<ProvidersResponse> {
  return get<ProvidersResponse>(`/v1/providers/linked?account_id=${accountId}`);
}

// Check if the backend is running
export async function getHealth(): Promise<{ status: string; version: string }> {
  return get(`/v1/health`);
}
```

---

## 4.6 Build the Shared Layout (`src/app/layout.tsx`)

The layout is the shell around every page — the navigation sidebar, header, etc.

Replace the contents of `src/app/layout.tsx`:

```tsx
// tsx = TypeScript JSX — TypeScript + React components

import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

// Metadata: what shows in the browser tab and search engines
export const metadata: Metadata = {
  title: "Channel Stream",
  description: "Your unified streaming guide",
};

// Props type for children — every layout receives child page content
interface RootLayoutProps {
  children: React.ReactNode;  // ReactNode = any valid React content
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white min-h-screen">
        {/* Navigation sidebar */}
        <div className="flex min-h-screen">
          <nav className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col p-6">
            {/* Logo */}
            <div className="mb-8">
              <h1 className="text-xl font-bold text-blue-400">
                ▶ Channel Stream
              </h1>
              <p className="text-gray-400 text-xs mt-1">Your streaming guide</p>
            </div>

            {/* Navigation links */}
            <ul className="space-y-2">
              <NavLink href="/" label="Dashboard" icon="⊞" />
              <NavLink href="/watch-now" label="Watch Now" icon="▶" />
              <NavLink href="/up-next" label="Up Next" icon="⏭" />
              <NavLink href="/sports" label="Sports Live" icon="🏟" />
              <NavLink href="/providers" label="Providers" icon="🔗" />
            </ul>

            {/* Profile section at bottom */}
            <div className="mt-auto pt-6 border-t border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
                  J
                </div>
                <div>
                  <p className="text-sm font-medium">Jon</p>
                  <p className="text-xs text-gray-400">jon@test.com</p>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content area */}
          <main className="flex-1 p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

// Reusable navigation link component
function NavLink({ href, label, icon }: { href: string; label: string; icon: string }) {
  return (
    <li>
      <Link
        href={href}
        className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
      >
        <span className="text-lg">{icon}</span>
        <span>{label}</span>
      </Link>
    </li>
  );
}
```

---

## 4.7 Build the Dashboard Homepage (`src/app/page.tsx`)

The homepage shows all four feeds at a glance — a summary of the entire app.

Replace `src/app/page.tsx`:

```tsx
// "use client" tells Next.js: this component runs in the browser,
// not on the server. Use this when you need useEffect or state.
"use client";

import { useEffect, useState } from "react";
import { getUpNextFeed, getWatchNowFeed, getSportsLive, getHealth } from "@/lib/api";
import type { FeedResponse, SportsResponse } from "@/types/api";

export default function DashboardPage() {
  // useState: React's way to store data that can change
  // [value, setValue] — setValue triggers a re-render when called
  const [upNext, setUpNext] = useState<FeedResponse | null>(null);
  const [watchNow, setWatchNow] = useState<FeedResponse | null>(null);
  const [sports, setSports] = useState<SportsResponse | null>(null);
  const [apiStatus, setApiStatus] = useState<"loading" | "ok" | "error">("loading");

  // useEffect: run this code AFTER the component renders
  // The empty [] dependency array means: run once on mount (page load)
  useEffect(() => {
    // Check if the backend is running
    getHealth()
      .then(() => setApiStatus("ok"))
      .catch(() => setApiStatus("error"));

    // Fetch all feeds in parallel using Promise.all
    // Promise.all waits for ALL to complete before continuing
    Promise.all([
      getUpNextFeed(),
      getWatchNowFeed(),
      getSportsLive(),
    ])
      .then(([upNextData, watchNowData, sportsData]) => {
        setUpNext(upNextData);
        setWatchNow(watchNowData);
        setSports(sportsData);
      })
      .catch((err) => {
        console.error("Failed to fetch feeds:", err);
      });
  }, []);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">Good evening, Jon</p>
        </div>
        {/* API status indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              apiStatus === "ok"
                ? "bg-green-400"
                : apiStatus === "error"
                ? "bg-red-400"
                : "bg-yellow-400 animate-pulse"
            }`}
          />
          <span className="text-sm text-gray-400">
            API {apiStatus === "ok" ? "connected" : apiStatus === "error" ? "offline" : "connecting..."}
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="In Progress" value={upNext?.count ?? "—"} icon="▶" color="blue" />
        <StatCard label="Available Now" value={watchNow?.count ?? "—"} icon="⊞" color="green" />
        <StatCard label="Live Sports" value={sports?.events?.filter(e => e.status === "live").length ?? "—"} icon="🏟" color="red" />
        <StatCard label="Providers" value={4} icon="🔗" color="purple" />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-8">
        {/* Up Next Section */}
        <section>
          <SectionHeader title="Continue Watching" href="/up-next" />
          <div className="space-y-3">
            {upNext
              ? upNext.items.slice(0, 3).map((item) => (
                  <div key={item.content_id} className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{item.title}</p>
                        <p className="text-gray-400 text-sm capitalize">{item.provider.replace(/_/g, " ")}</p>
                      </div>
                      <span className="text-blue-400 text-sm">{item.progress_pct}%</span>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-3 h-1 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${item.progress_pct}%` }}
                      />
                    </div>
                  </div>
                ))
              : <LoadingSkeleton count={3} />
            }
          </div>
        </section>

        {/* Sports Section */}
        <section>
          <SectionHeader title="Sports Live" href="/sports" />
          <div className="space-y-3">
            {sports
              ? sports.events.slice(0, 3).map((event) => (
                  <div key={event.game_id} className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                      {event.status === "live" && (
                        <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded-full font-bold">
                          LIVE
                        </span>
                      )}
                      <span className="text-gray-400 text-sm uppercase">{event.league}</span>
                      {event.status_detail && (
                        <span className="text-gray-500 text-sm">{event.status_detail}</span>
                      )}
                    </div>
                    <p className="font-medium">
                      {event.home_team.abbr} vs {event.away_team.abbr}
                    </p>
                    {event.score && event.status === "live" && (
                      <p className="text-gray-300 text-sm mt-1">
                        {event.score.home} — {event.score.away}
                      </p>
                    )}
                    {/* Streaming options */}
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {event.watch_on.map((opt) => (
                        <span
                          key={opt.network}
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            opt.requires_cable
                              ? "bg-gray-700 text-gray-300"
                              : "bg-blue-900 text-blue-200"
                          }`}
                        >
                          {opt.app_display}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              : <LoadingSkeleton count={3} />
            }
          </div>
        </section>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: string;
  color: "blue" | "green" | "red" | "purple";
}) {
  const colorMap = {
    blue: "text-blue-400",
    green: "text-green-400",
    red: "text-red-400",
    purple: "text-purple-400",
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className={`text-3xl font-bold ${colorMap[color]}`}>{value}</p>
    </div>
  );
}

function SectionHeader({ title, href }: { title: string; href: string }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <a href={href} className="text-blue-400 text-sm hover:text-blue-300">
        See all →
      </a>
    </div>
  );
}

function LoadingSkeleton({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-gray-900 rounded-lg p-4 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-2" />
          <div className="h-3 bg-gray-800 rounded w-1/2" />
        </div>
      ))}
    </>
  );
}
```

---

## 4.8 Create the Up Next Page (`src/app/up-next/page.tsx`)

```bash
mkdir -p src/app/up-next
```

Create `src/app/up-next/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { getUpNextFeed } from "@/lib/api";
import type { FeedResponse, FeedItem } from "@/types/api";

export default function UpNextPage() {
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUpNextFeed()
      .then(setFeed)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Continue Watching</h1>
      <p className="text-gray-400 mb-8">Your in-progress shows and movies across all providers</p>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : feed && feed.items.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 max-w-3xl">
          {feed.items.map((item, index) => (
            <UpNextCard key={item.content_id} item={item} rank={index + 1} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="Nothing in progress"
          description="Start watching something on Netflix, Hulu, or Apple TV+ and it'll appear here."
        />
      )}
    </div>
  );
}

function UpNextCard({ item, rank }: { item: FeedItem; rank: number }) {
  const resumeTime = formatResumeTime(item.resume_position_sec);
  const providerLabel = item.provider?.replace(/_/g, " ");

  return (
    <div className="bg-gray-900 rounded-xl p-5 flex items-center gap-5">
      {/* Rank number */}
      <span className="text-3xl font-bold text-gray-700 w-8 text-center">{rank}</span>

      {/* Content info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded capitalize">
            {item.type}
          </span>
          <span className="text-gray-500 text-xs capitalize">{providerLabel}</span>
        </div>
        <h3 className="font-semibold text-lg truncate">{item.title}</h3>
        <p className="text-gray-400 text-sm mt-0.5">Resume at {resumeTime}</p>

        {/* Progress bar */}
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${item.progress_pct}%` }}
            />
          </div>
          <span className="text-gray-400 text-xs">{item.progress_pct}%</span>
        </div>
      </div>

      {/* Play button */}
      <a
        href={item.deeplink || "#"}
        target="_blank"
        rel="noopener noreferrer"
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex-shrink-0"
      >
        ▶ Resume
      </a>
    </div>
  );
}

function formatResumeTime(seconds?: number): string {
  if (!seconds) return "0:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="text-center py-16 text-gray-500">
      <p className="text-5xl mb-4">⏭</p>
      <h3 className="text-xl font-medium mb-2">{title}</h3>
      <p className="text-sm max-w-sm mx-auto">{description}</p>
    </div>
  );
}
```

---

## 4.9 Create the Providers Page (`src/app/providers/page.tsx`)

```bash
mkdir -p src/app/providers
```

Create `src/app/providers/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { getLinkedProviders } from "@/lib/api";
import type { ProvidersResponse, ProviderLink } from "@/types/api";

const PROVIDER_INFO: Record<string, { label: string; color: string }> = {
  netflix:       { label: "Netflix",      color: "bg-red-600" },
  hulu:          { label: "Hulu",         color: "bg-green-600" },
  disney_plus:   { label: "Disney+",      color: "bg-blue-800" },
  apple_tv_plus: { label: "Apple TV+",    color: "bg-gray-600" },
  amazon_prime:  { label: "Prime Video",  color: "bg-blue-600" },
  max:           { label: "Max",          color: "bg-purple-700" },
  peacock:       { label: "Peacock",      color: "bg-yellow-600" },
};

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);

  useEffect(() => {
    getLinkedProviders().then(setProviders);
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Linked Providers</h1>
      <p className="text-gray-400 mb-8">Manage your connected streaming services</p>

      {providers ? (
        <div className="grid grid-cols-2 gap-4 max-w-2xl">
          {providers.providers.map((provider) => (
            <ProviderCard key={provider.provider} provider={provider} />
          ))}
        </div>
      ) : (
        <p className="text-gray-400">Loading...</p>
      )}
    </div>
  );
}

function ProviderCard({ provider }: { provider: ProviderLink }) {
  const info = PROVIDER_INFO[provider.provider] || {
    label: provider.provider,
    color: "bg-gray-700",
  };

  const statusColor =
    provider.status === "valid"
      ? "text-green-400"
      : provider.status === "expired"
      ? "text-red-400"
      : provider.status === "expiring_soon"
      ? "text-yellow-400"
      : "text-gray-400";

  const statusLabel =
    provider.status === "valid"
      ? "Connected"
      : provider.status === "expired"
      ? "Token Expired — Re-link"
      : provider.status === "expiring_soon"
      ? "Expiring Soon"
      : "Connected";

  return (
    <div className="bg-gray-900 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg ${info.color} flex items-center justify-center text-white font-bold text-sm`}>
          {info.label[0]}
        </div>
        <div>
          <p className="font-medium">{info.label}</p>
          <p className={`text-sm ${statusColor}`}>{statusLabel}</p>
        </div>
      </div>
      {provider.token_expires && (
        <p className="text-gray-500 text-xs">
          Token expires: {new Date(provider.token_expires).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}
```

---

## 4.10 Configure the API URL for Development

Create `web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

The `NEXT_PUBLIC_` prefix means this variable is exposed to the browser (not just the server). Without this prefix, environment variables in Next.js are server-only.

---

## 4.11 Run the Full Stack

Now run everything together:

**Terminal 1** — Database:
```bash
cd ~/channel-stream
supabase start
```

**Terminal 2** — Go backend:
```bash
cd ~/channel-stream
go run ./cmd/server
```

**Terminal 3** — Next.js frontend:
```bash
cd ~/channel-stream
npm run dev
```

Open http://localhost:3001 — you should see the Channel Stream dashboard with real data from your Go backend.

---

## 4.12 What You Just Built

```
Browser → http://localhost:3001
            Next.js Dashboard
            ↓
            Calls: fetch("http://localhost:8080/v1/feed/up-next")
            ↓
            Go Backend → PostgreSQL → Returns JSON
            ↓
            React renders FeedItem components from JSON data
            ↓
            You see a styled dashboard with your real data
```

This is a complete full-stack loop. Every card on the dashboard represents a real row in your database.

---

## 4.13 Checkpoint

- [ ] `npm run dev` starts without errors
- [ ] Dashboard loads at http://localhost:3001
- [ ] Stat cards show correct counts (4 in progress, 8 watch now, etc.)
- [ ] Up Next page shows Severance, Shogun, The Bear, Ripley with progress bars
- [ ] Providers page shows 4 connected services
- [ ] You understand what `useState` and `useEffect` do
- [ ] You understand the difference between TypeScript types and runtime data
- [ ] Code is committed to GitHub

---

**Next**: [Module 5 → Caching with Redis](./MODULE_05_REDIS_CACHING.md)

 Open three terminal tabs and run one command in each:

  Terminal 1 — Supabase (database):
  supabase start

  Terminal 2 — Go backend:
  go run ./cmd/server

  Terminal 3 — Next.js frontend:
  npm run dev

  Then open http://localhost:3001 in your browser.

  To verify all three are up at once, you can run this check:
  Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in @(54322, 8080, 3001) } | Select-Object LocalPort

  You should see all three ports (54322 = Postgres, 8080 = Go API, 3001 = Next.js). The Go backend won't return real data until Supabase is started first.
