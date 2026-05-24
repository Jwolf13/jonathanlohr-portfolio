# Portfolio Audit & Optimization Plan
_Audit date: 2026-05-24 · Repo: `jwolf13/jonathanlohr-portfolio`_

## 1. What you actually have today

You have **one Git repo** (`jonathanlohr-portfolio`) that is doing four jobs at once:

1. A Next.js 16 static-export portfolio site (App Router, Tailwind v4, TS).
2. A Python BLS/Census ETL pipeline (`scripts/`, `data/`).
3. Four full sub-projects checked in as folders (`AWS Compliance collector/`, `Channel_Stream/`, `apex_benchmark/`, `API Builder/`, plus `pipeline-tuneup-v3/`, `data-science-projects/`).
4. A GitHub Actions deploy → S3 → CloudFront workflow that is already wired up and working.

The Next.js side has four routes live: `/` (NC occupation dashboard), `/projects` (a near-duplicate of `/`), `/consulting` and `/architecture-cases` (both still "Coming Soon"), and `/gtm-calculator` (the one polished interactive page). `components/PipelineTuneUp.tsx` and `SalesMotionPlaybook.tsx` exist; only `SalesMotionPlaybook` is wired to a page.

The deploy workflow at `.github/workflows/deploy.yml` is in good shape: on push to `main`, it runs `npm run build:static`, syncs `out/` to S3, and invalidates CloudFront. That part you should leave alone.

## 2. The five things hurting the workflow right now

### 2.1 Nested folder of the same name
Your working directory is `jonathanlohr-portfolio/` and **inside it** is another `jonathanlohr-portfolio/` which is the real repo. The outer folder has stray files (`GEMINI.md`, `package-lock.json`, `personal-project-playbook.pdf`) that don't belong to either. Every tool you use has to guess which one you mean.

**Fix:** move the contents of the inner folder up one level (or open the inner folder directly as your workspace). Pick one.

### 2.2 Secrets are committed to the repo
Three files in `Channel_Stream/` contain real credentials:
- `channel-stream-deploy_accessKeys.csv` — AWS access keys
- `client_secret_390417865664-...googleusercontent.com.json` — Google OAuth client secret
- `client_secret_661448655156-...googleusercontent.com.json` — Google OAuth client secret

**Fix today, in this order:**
1. Rotate all three (AWS IAM → delete the key + create a new one; Google Cloud Console → reset OAuth client secret).
2. Add patterns to `.gitignore`: `*accessKeys*.csv`, `client_secret_*.json`, `**/*.env*`.
3. Purge them from history with `git filter-repo --invert-paths --path Channel_Stream/channel-stream-deploy_accessKeys.csv ...` then force-push. Until you do this, anyone reading the public repo has the keys.

### 2.3 Build artifacts, venvs, and `node_modules` are tracked
`.venv/`, `apex_benchmark/.venv/`, `API Builder/.venv/`, `pipeline-tuneup-v3/venv/`, `Channel_Stream/node_modules/`, and `.next/` (in places) are all in the repo. Your `.gitignore` lists `/.next` and `/node_modules` at the root level, but the patterns don't cascade into sub-projects.

**Fix:** rewrite `.gitignore` with `**/` patterns (see Section 4) and untrack what's already in: `git rm -r --cached .venv */.venv */node_modules .next out`.

### 2.4 `/` and `/projects` are duplicates
`app/page.tsx` and `app/projects/page.tsx` ship the same NC occupation dashboard with cosmetic differences and embedded JSON. The labor data already exists in `data/processed/occupation_dashboard.json` — the page just isn't reading it.

**Fix:** make `/` a real landing page (hero + project cards) and turn `/projects` into an index that links out to individual project case-study pages. The dashboard becomes its own `/projects/nc-labor-market` route that imports the processed JSON.

### 2.5 Each sub-project is a black box to the website
`Channel_Stream/`, `AWS Compliance collector/`, `apex_benchmark/`, etc. live in the repo but have zero presence on the site itself. A visitor browsing your portfolio sees a labor dashboard and two "Coming Soon" pages — none of the deeper work.

**Fix:** every sub-project needs a case-study page (problem → architecture → demo link → GitHub link → what you'd do next). See Section 5.

## 3. Recommended folder structure

The cleanest mental model for a developer portfolio: **the website repo is thin and project-aware, each project lives in its own repo, the website pulls metadata from a registry file.** This is how most engineering portfolios scale.

```
jonathanlohr-portfolio/              ← the only thing in this repo
├── .github/workflows/deploy.yml     ← already good, keep
├── app/
│   ├── page.tsx                     ← real landing page (hero + cards)
│   ├── layout.tsx
│   ├── globals.css
│   ├── about/page.tsx               ← bio, resume link, contact
│   ├── projects/
│   │   ├── page.tsx                 ← project index, filterable by category
│   │   └── [slug]/page.tsx          ← dynamic case-study route
│   ├── writing/                     ← (optional) blog posts as MDX
│   └── tools/
│       └── gtm-calculator/page.tsx  ← rename from /gtm-calculator
├── components/
│   ├── ProjectCard.tsx
│   ├── CaseStudyLayout.tsx
│   ├── Nav.tsx
│   └── ...your existing components
├── content/
│   ├── projects.ts                  ← typed registry of every project
│   └── case-studies/
│       ├── channel-stream.mdx
│       ├── aws-compliance-collector.mdx
│       ├── apex-benchmark.mdx
│       └── nc-labor-market.mdx
├── data/
│   └── processed/                   ← keep, import these in pages
├── public/
│   ├── images/projects/             ← screenshots, architecture diagrams
│   └── resume.pdf
├── package.json
├── next.config.ts
└── README.md
```

Everything else moves to its own GitHub repo, owned by `jwolf13`:

- `github.com/jwolf13/channel-stream`
- `github.com/jwolf13/aws-compliance-collector`
- `github.com/jwolf13/apex-benchmark`
- `github.com/jwolf13/labor-data-pipeline` (the `scripts/` + `data/` flow)
- `github.com/jwolf13/api-builder` (or fold into another repo if it's small)
- `github.com/jwolf13/data-science-notebooks` (golf + probabilities)

The portfolio site then links to each. Migration is `git subtree split` or just copy → init → push for each one.

## 4. A `.gitignore` that actually works

Replace the current root `.gitignore` with:

```gitignore
# dependencies
**/node_modules/
**/.pnp
**/.pnp.*

# build outputs
**/.next/
**/out/
**/dist/
**/build/
**/*.tsbuildinfo
next-env.d.ts

# python
**/.venv/
**/venv/
**/__pycache__/
**/.pytest_cache/
**/.ruff_cache/
**/.coverage
**/*.pyc

# env & secrets
**/.env
**/.env.*
**/*accessKeys*.csv
**/client_secret_*.json
**/*.pem

# editor & OS
.DS_Store
**/.vscode/
**/.idea/

# misc
**/playwright-report/
**/test-results/
**/.turbo/
```

## 5. How to position each project (developer-portfolio style)

Treat every project as a **case study**, not a code dump. Each one gets the same shape, which makes them comparable for a recruiter scanning fast.

The pattern for `content/case-studies/*.mdx`:

```
1. One-sentence hook (the result, not the tech)
2. The problem you were solving
3. Architecture diagram (SVG in /public/images/projects/)
4. Tech stack as a row of small tags
5. The 2–3 hardest decisions you made and why
6. Live demo link · GitHub link · Tech writeup link
7. What you'd do differently
```

Specific positioning for what you have:

- **Channel Stream** — lead with "sports discovery layer, Go API + Next.js + Supabase, polls ESPN public API." This is your most senior project; it should be the first card. You already have `system-design-channel-stream.md` — that's the case-study draft. Add a live demo URL.
- **AWS Compliance Collector** — lead with "Maps Security Hub/Config/IAM findings to NIST 800-53 controls, generates audit PDFs." This is the security/infra credibility piece. The notebooks are a strong differentiator — link the GitHub repo's notebooks directory in the case study.
- **Apex Benchmark** — FastAPI + Alembic + Docker. Lead with what it benchmarks and why. Right now the README doesn't say.
- **NC Labor Market Dashboard** — this is your current `/` page. Lead with "Python ETL → BLS/Census APIs → static JSON → React dashboard." It's the data-engineering story.
- **GTM Calculator** — already polished. Position as the GTM/business-side piece. Keep it under `/tools/`.
- **API Builder** — only two files. Either flesh it out or fold it into one of the others; on its own it weakens the portfolio.
- **Data science notebooks** (golf, probabilities) — group into one card titled "Statistical modeling notebooks" and link to the GitHub repo's notebook viewer.

The registry file (`content/projects.ts`) ties it all together:

```ts
export type Project = {
  slug: string;
  title: string;
  hook: string;
  category: 'fullstack' | 'data' | 'infra' | 'gtm';
  stack: string[];
  github: string;
  demo?: string;
  caseStudy: string;  // path to mdx
  featured: boolean;
};

export const projects: Project[] = [
  {
    slug: 'channel-stream',
    title: 'Channel Stream',
    hook: 'Real-time sports discovery — find where any game is broadcast.',
    category: 'fullstack',
    stack: ['Go', 'Next.js', 'Supabase', 'Redis', 'AWS ECS'],
    github: 'https://github.com/jwolf13/channel-stream',
    demo: 'https://channelstream.jonathanlohr.com',
    caseStudy: 'channel-stream',
    featured: true,
  },
  // ... one entry per project
];
```

The `/projects` index reads this array. Adding a new project = one entry in the registry + one MDX file. No layout work.

## 6. GitHub workflow that makes "push and ship" effortless

You already have the deploy half. Add a guard half so broken code can't reach S3.

### 6.1 Branch protection on `main`
On GitHub: Settings → Branches → Add rule for `main`. Require status checks before merge. This forces all work through PRs.

### 6.2 PR check workflow (`.github/workflows/ci.yml`)
```yaml
name: CI
on:
  pull_request:
    branches: [main]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm run build:static
```
Now a broken build fails the PR check instead of the deploy.

### 6.3 Day-to-day cadence
The shortest path from idea to live site:

```bash
git checkout -b feat/channel-stream-case-study
# edit content/projects.ts + content/case-studies/channel-stream.mdx
npm run dev        # eyeball at localhost:3000
git add -A && git commit -m "feat: add channel-stream case study"
git push -u origin feat/channel-stream-case-study
gh pr create --fill && gh pr merge --squash --auto
```

That last line auto-merges when CI passes; the existing deploy workflow then ships it to S3. Install GitHub CLI (`gh`) if you haven't — it removes the browser step entirely.

### 6.4 Preview deploys (optional, ~30 min to set up)
Add a second deploy job in `deploy.yml` triggered on PRs that syncs to `s3://your-bucket/pr-${{ github.event.number }}/`. You get a unique URL per PR to share before merging. Cheap and impressive on its own.

## 7. AWS infrastructure — what to confirm

Your deploy workflow assumes these AWS resources exist. Verify each:

- **S3 bucket** named in `AWS_S3_BUCKET` secret, configured for static website hosting OR (preferred) private with CloudFront Origin Access Control.
- **CloudFront distribution** with the bucket as origin, `index.html` as default root object, and a custom error response mapping 403/404 → `/index.html` (so client-side routing on `/projects/[slug]` works).
- **Route 53** record pointing your domain at the CloudFront distribution.
- **ACM certificate** in `us-east-1` (CloudFront requires it there) for your domain.
- **IAM user** for GitHub Actions with minimal permissions: `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on the bucket; `cloudfront:CreateInvalidation` on the distribution. Nothing more.

If any of those aren't set up yet, the cheapest robust path is one-time Terraform in a separate `infra/` repo — not in the portfolio repo.

## 8. Suggested order of operations (next 1–2 weeks)

1. **Today (urgent):** rotate the three leaked secrets; add them to `.gitignore`; `git rm --cached` them; force-push. Until this is done, treat the repo as compromised.
2. **This week:** flatten the nested `jonathanlohr-portfolio/jonathanlohr-portfolio/` folder; rewrite `.gitignore`; untrack `.venv` / `node_modules` / `.next`; move each sub-project to its own repo (`git subtree split -P "AWS Compliance collector" -b aws-compliance-collector` then push the new branch as a new repo).
3. **Next week:** rebuild the site against the new structure — landing page with project cards, dynamic `/projects/[slug]` route, MDX case studies, `content/projects.ts` registry. Wire `data/processed/occupation_dashboard.json` to the NC labor page so it's no longer inline.
4. **After that:** add the CI workflow, enable branch protection, add preview deploys.

The deploy pipeline already works — most of the lift is reorganizing what feeds into it.
