# Architecture & Contributor Guide

This is the map and the manual for the portfolio. Read it once end-to-end, then keep it open while you make changes. The companion diagram lives at `docs/architecture.drawio` — open it in [diagrams.net](https://app.diagrams.net) to see the same picture visually.

## 1. The mental model

Three layers, that's it.

**Layer 1 — Routes.** Files under `app/`. One `page.tsx` per URL. Next.js looks at the folder name and turns it into a URL: `app/sales-tools/page.tsx` becomes `/sales-tools`.

**Layer 2 — Components.** Files under `components/`. Reusable React. Routes import them, render them. Components don't know what page they're on; they just take props and render UI.

**Layer 3 — Content registries.** Files under `content/`. Plain TypeScript arrays describing what content exists. **The registries are the source of truth.** Routes read from them. To add a project or a sales tool, you edit a registry — you do not write a new page.

```
Registry (the data) ──► Route (the page) ──► Component (the UI)
content/projects.ts      app/projects/         components/
                         page.tsx              ProjectCard.tsx
```

Why this matters: if you want to add a new project, you don't write code. You add one entry to `content/projects.ts` and create one TSX file with the write-up. Everything else — landing-page card, projects-index entry, dedicated `/projects/<slug>` page — happens automatically because the routes are reading the registry.

## 2. The deploy pipeline (top of the diagram)

You push code → GitHub runs CI → if main, GitHub builds and ships the result to AWS.

| Step | What happens | File |
| --- | --- | --- |
| 1. Local | You edit, save, see it at `localhost:3000` | `npm run dev` |
| 2. Push | Code goes to `github.com/jwolf13/jonathanlohr-portfolio` | `git push` |
| 3. CI | GitHub runs lint + typecheck + build on every PR | `.github/workflows/ci.yml` |
| 4. Deploy | On push to `main`: build static site, sync to S3, invalidate CloudFront | `.github/workflows/deploy.yml` |
| 5. Live | Visitors hit CloudFront → CloudFront serves from S3 | (AWS) |

The deploy workflow needs five GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`. They're already set up.

**The IAM user behind those keys should only have:**
- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on your bucket
- `cloudfront:CreateInvalidation` on your distribution

Nothing else. If you ever regenerate keys, keep that scope.

## 3. Routes — every URL on the site

| URL | File | What it does | Reads from |
| --- | --- | --- | --- |
| `/` | `app/page.tsx` | Hero + two big cards (Sales Tools, Projects) | nothing |
| `/sales-tools` | `app/sales-tools/page.tsx` | Lists all sales tools as cards | `content/sales-tools.ts` |
| `/projects` | `app/projects/page.tsx` | Lists all projects, grouped by category | `content/projects.ts` |
| `/projects/<slug>` | `app/projects/[slug]/page.tsx` | One page per project (case study) | `content/projects.ts` + `content/case-studies/<slug>.tsx` |
| `/gtm-calculator` | `app/gtm-calculator/page.tsx` | The interactive GTM calculator | uses `components/SalesMotionPlaybook.tsx` |
| `/blog` | `app/blog/page.tsx` | "Coming soon" placeholder | nothing |
| `/about` | `app/about/page.tsx` | Bio + contact | nothing |
| `/consulting` | `app/consulting/page.tsx` | Category landing — funnels into GTM projects | `content/projects.ts` |
| `/architecture-cases` | `app/architecture-cases/page.tsx` | Category landing — infra + fullstack projects | `content/projects.ts` |

`app/layout.tsx` wraps every page with the `<SiteNav />` header and footer. Edit it once, see the effect everywhere.

## 4. Components — what's in `/components`

| File | Purpose | Used by |
| --- | --- | --- |
| `SiteNav.tsx` | The sticky top nav | `app/layout.tsx` |
| `ProjectCard.tsx` | The clickable card on `/` and `/projects` | `app/page.tsx`, `app/projects/page.tsx` |
| `CaseStudyLayout.tsx` | Wraps each case study (title, tags, GitHub link) | `app/projects/[slug]/page.tsx` |
| `NcLaborDashboard.tsx` | Interactive labor dashboard (client component) | `content/case-studies/nc-labor-market.tsx` |
| `SalesMotionPlaybook.tsx` | The GTM calculator itself | `app/gtm-calculator/page.tsx` |
| `PipelineTuneUp.tsx` | Pipeline diagnostic tool | (not currently mounted — available to reuse) |

## 5. Content registries — the source of truth

### `content/projects.ts`

```ts
export const projects: Project[] = [
  {
    slug: "channel-stream",                       // URL slug → /projects/channel-stream
    title: "Channel Stream",
    hook: "One-sentence outcome (not tech).",
    category: "fullstack",                        // "fullstack" | "data" | "infra" | "gtm"
    stack: ["Go", "Next.js", "Supabase"],         // tech tags
    github: "https://github.com/jwolf13/channel-stream",
    demo: "https://...",                          // optional
    status: "wip",                                // "live" | "wip" | "archived"
    featured: true,                               // shows on the homepage
  },
  // ...
];
```

### `content/sales-tools.ts`

```ts
export const salesTools: SalesTool[] = [
  {
    slug: "gtm-pipeline-calculator",
    title: "GTM Pipeline Calculator",
    description: "Long-form description shown on the card.",
    href: "/gtm-calculator",                      // where Open → goes
    status: "live",                               // "live" | "framework" | "wip"
    featured: true,
  },
  // ...
];
```

### `content/case-studies/`

One file per project, named with the slug. Each file exports a default React component that renders the case-study body (problem, architecture, decisions). `index.ts` maps slugs to components — that's what `/projects/[slug]/page.tsx` looks up.

Pattern for a case study:

```tsx
import { Section } from "@/components/CaseStudyLayout";

export default function MyProject() {
  return (
    <>
      <Section title="The problem">
        <p>What you were solving.</p>
      </Section>
      <Section title="Architecture">
        <p>How it's built.</p>
      </Section>
      <Section title="Hard decisions">
        <p>The trade-offs.</p>
      </Section>
      <Section title="What I'd do next">
        <p>The honest gap analysis.</p>
      </Section>
    </>
  );
}
```

## 6. The data pipeline (bottom of the diagram)

Public APIs → Python scripts → JSON → React component. Build-time only — nothing runs on the user's browser.

```
BLS API ─┐
         ├─► scripts/*.py ──► data/raw/*.json ──► data/processed/*.json
Census ──┘                                                │
                                                          │ imported at build time
                                                          ▼
                                            components/NcLaborDashboard.tsx
```

To refresh the data:

```bash
# from the repo root, with .venv active
python scripts/build_occupation_dashboard.py
git add data/processed/
git commit -m "data: refresh labor dashboard"
git push
```

The CI build picks up the new JSON and the deploy ships it.

## 7. Recipes — the everyday motions

### Add a new project

```bash
# 1. Add the entry to the registry
# Open content/projects.ts and add one object to the projects array.

# 2. Create the case study
# content/case-studies/my-new-project.tsx
#   (copy any existing one as a starting point)

# 3. Register the slug
# content/case-studies/index.ts: add the import + map entry.

# 4. Verify locally
npm run dev
# Open http://localhost:3000/projects/my-new-project

# 5. Ship it
git checkout -b feat/my-new-project
git add content/
git commit -m "feat: add my-new-project case study"
git push -u origin feat/my-new-project
# Open a PR on GitHub, CI runs, merge to main → live in ~2 minutes
```

### Add a new sales tool

```bash
# 1. Add the entry
# content/sales-tools.ts: add one object to the salesTools array.
#   If the tool lives at an existing URL (like /gtm-calculator), point href there.
#   If you need a new route, also create app/your-tool/page.tsx.

# 2. Verify
npm run dev
# Open http://localhost:3000/sales-tools

# 3. Ship (same as above)
```

### Edit the home page

```
File: app/page.tsx
```
It's a regular React component. The hero text, the two cards, the contact strip — all in one file. To add a third card or move things around, just edit JSX.

### Edit the nav

```
File: components/SiteNav.tsx
```
There's a `links` array at the top. Add/remove an entry to add/remove a nav item.

### Change the global look (colors, font, footer)

```
Files: app/layout.tsx and app/globals.css
```
`layout.tsx` controls the footer and what wraps every page. `globals.css` is where Tailwind v4 imports live. Color scheme is zinc + blue-600 throughout; if you change one place, change the rest with find-replace.

### Add a brand-new top-level route (like `/notes`)

```bash
mkdir app/notes
# create app/notes/page.tsx with:
#   export default function NotesPage() { return <div>...</div>; }
# add { href: "/notes", label: "Notes" } to the links array in components/SiteNav.tsx
```

### Push a change

```bash
git checkout -b feat/short-description
# edit
npm run dev          # eyeball at localhost:3000
npm run lint         # quick sanity check
npx tsc --noEmit     # catches type errors before CI does
git add -A
git commit -m "feat: short description"
git push -u origin feat/short-description
gh pr create --fill          # if you have GitHub CLI installed
# OR open the PR URL GitHub prints and click Create
```

Once CI passes and you merge, the deploy workflow takes over.

## 8. Common pitfalls and how to spot them

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| New page 404s in production | You added a route but forgot it's a dynamic `[slug]`-style route and `generateStaticParams()` didn't include it | Make sure the slug is in `content/projects.ts` (or whatever registry the route reads) |
| `useState` / `useEffect` throws "is not a function" at build | The file uses hooks but isn't marked `"use client"` | Add `"use client";` as the first line of the file |
| Build fails on `generateStaticParams` | The dynamic route is marked `"use client"` (server-only export) | Remove `"use client"` from the route file — push the interactive part into a child component that is `"use client"` |
| Image / SVG missing in production | File isn't under `public/` | Put it in `public/images/...` and reference as `/images/...` |
| Style changes don't apply | Tailwind class typo, or class is dynamically built from a string | Use complete class names; don't construct them with string concatenation (Tailwind only sees the literal strings in source) |
| Data update doesn't show up live | Forgot to commit the regenerated JSON in `data/processed/` | `git add data/processed && git commit` |
| `next dev` says port in use | Stale dev server still running | `npx kill-port 3000` or just use a new port: `npm run dev -- -p 3001` |

## 9. Where to learn what

| If you want to learn... | Open these files first |
| --- | --- |
| How Next.js routing works | `app/projects/[slug]/page.tsx` — minimal dynamic route with `generateStaticParams` |
| How a React component receives props | `components/ProjectCard.tsx` |
| How a typed TS registry works | `content/projects.ts` |
| How static export imports data | `components/NcLaborDashboard.tsx` (the `import dashboardData from "@/data/processed/..."` line) |
| How GitHub Actions deploys | `.github/workflows/deploy.yml` |
| How CI catches breakage | `.github/workflows/ci.yml` |

## 10. The sub-project folders (Channel_Stream, AWS Compliance collector, etc.)

These live in the repo but are NOT part of the website build. They're separate codebases (Go, Python, FastAPI, etc.). The portfolio links to them as if they were external repos — the case studies in `content/case-studies/` describe them and point to their `github` URL.

Eventually each one should be its own repo on GitHub (`github.com/jwolf13/channel-stream`, etc.) and removed from this folder, so the website repo stays thin. For now they can coexist; the deploy workflow only ships `out/` (the built Next.js output), so the sub-projects don't slow anything down.

## 11. Files you should rarely touch

- `tsconfig.json` — TypeScript compiler options. Touch only if you're adding a new tooling integration.
- `next.config.ts` — Next.js configuration. The `output: "export"` line is what makes this a static site. Don't remove it without rewiring the deploy.
- `postcss.config.mjs`, `eslint.config.mjs` — toolchain configs. Stable.
- `package-lock.json` — auto-managed by npm. Commit it when it changes, but never edit by hand.
- `.next/` and `out/` — build artifacts. Already gitignored. If something goes weird, `rm -rf .next out && npm run dev` is a safe reset.

## 12. When you're stuck

1. Open `docs/architecture.drawio` and look at the diagram. Most "where does this live?" questions answer themselves.
2. Check this guide's recipe section.
3. Run `npm run dev` and `npx tsc --noEmit` simultaneously — type errors usually point straight at what's broken.
4. The error message + file path is almost always enough to feed to a search or to me directly.
