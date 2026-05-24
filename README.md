# jonathanlohr-portfolio

Personal portfolio site for Jonathan Lohr. Static-exported Next.js, deployed to S3 + CloudFront via GitHub Actions.

## Stack

- Next.js 16 (App Router, static export)
- React 19, TypeScript
- Tailwind CSS v4
- Python ETL scripts for labor-market data (BLS, Census ACS)
- GitHub Actions deploy to S3 + CloudFront

## Repo layout

```
app/                          App Router pages
  page.tsx                    Landing (hero + featured projects)
  projects/
    page.tsx                  Project index, grouped by category
    [slug]/page.tsx           Dynamic case-study route
  about/page.tsx
  gtm-calculator/page.tsx
  consulting/page.tsx
  architecture-cases/page.tsx

components/                   Reusable UI
  SiteNav.tsx
  ProjectCard.tsx
  CaseStudyLayout.tsx
  NcLaborDashboard.tsx
  PipelineTuneUp.tsx
  SalesMotionPlaybook.tsx

content/                      Source of truth for portfolio content
  projects.ts                 Typed registry of every project
  case-studies/               One TSX component per project
    index.ts                  slug -> component map
    channel-stream.tsx
    aws-compliance-collector.tsx
    ...

data/
  raw/                        Untouched JSON from BLS / Census APIs
  processed/                  ETL output, imported by pages at build time

scripts/                      Python ETL pipeline

.github/workflows/
  ci.yml                      Lint + typecheck + build on PRs
  deploy.yml                  Push to main -> S3 sync + CloudFront invalidate

# Sub-projects (each will eventually become its own GitHub repo)
Channel_Stream/
AWS Compliance collector/
apex_benchmark/
API Builder/
data-science-projects/
pipeline-tuneup-v3/
```

## Local development

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static export -> out/
npm run lint
npx tsc --noEmit
```

## Adding a new project

1. Add an entry to `content/projects.ts`.
2. Create `content/case-studies/<slug>.tsx`.
3. Register it in `content/case-studies/index.ts`.
4. PR -> CI runs -> merge -> deploy ships it.

## Deploy

Pushing to `main` triggers `.github/workflows/deploy.yml`:
1. `npm run build:static`
2. `aws s3 sync out/ s3://$AWS_S3_BUCKET/`
3. `aws cloudfront create-invalidation`

Required secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`.

See `PORTFOLIO_AUDIT.md` for the full audit and the prioritized list of structural improvements.
