# GEMINI.md - Project Context & Instructions

This repository is a multi-layered portfolio project belonging to Jonathan Lohr. It encompasses a central Next.js portfolio website, a Python-based labor market data pipeline, and two significant technical projects: **AWS Compliance Collector** and **Channel Stream**.

---

## 🚀 Project Overview

### 1. Main Portfolio (`/`)
- **Tech Stack:** Next.js (App Router), React 19, TypeScript, Tailwind CSS v4.
- **Architecture:** **Static Export** (`output: "export"`). Deployed via GitHub Actions to S3 + CloudFront.
- **Key Feature:** North Carolina labor market occupation dashboard.
- **Data Strategy:** Currently uses inline JSON in pages, but intended to consume processed data from the Python ETL pipeline.

### 2. AWS Compliance Collector (`/AWS Compliance collector`)
- **Purpose:** Automated NIST 800-53 compliance evidence collection and assessment for AWS.
- **Tech Stack:** Python, Boto3, ReportLab (PDF generation), DynamoDB (Single-table design).
- **Core Logic:** Maps findings from Security Hub, Config, and IAM to NIST controls. Detects drift between scans.

### 3. Channel Stream (`/Channel_Stream`)
- **Purpose:** A discovery layer for sports fans to find where to watch games.
- **Tech Stack:** 
  - **Backend:** Go (API + Ingestion worker), Redis (Caching).
  - **Database:** PostgreSQL via Supabase (local development encouraged).
  - **Frontend:** Next.js (Web dashboard).
- **Data Source:** Polls ESPN's public API for live scores and broadcast info.

### 4. Data Science & ETL (`/scripts`, `/data-science-projects`)
- **Scripts:** Python ETL pipeline pulling from BLS and Census APIs.
- **Data Science:** Probabilities and golf-related data analysis projects.

---

## 🛠 Building & Running

### Portfolio Root
```bash
cd jonathanlohr-portfolio
npm install          # Install dependencies
npm run dev          # Start local development (http://localhost:3000)
npm run build        # Static export to 'out/' directory
npm run lint         # Run ESLint
```

### Python Data Pipeline
Ensure the `.venv` is active before running scripts.
```bash
python scripts/build_occupation_dashboard.py   # Transform Census ACS data
python scripts/ingest_labor_data.py            # Pull from BLS/Census APIs
```

### AWS Compliance Collector
```bash
cd "AWS Compliance collector"
pip install -r requirements.txt
make test            # Run pytest suite (botocore.Stubber & moto)
make lint            # Run Ruff linter
```

### Channel Stream
Local development uses Docker-backed Supabase.
```bash
cd Channel_Stream
supabase start       # Start local DB/Auth/Studio
go run ./cmd/server  # Start Go backend API
npm run dev          # Start Next.js frontend
```

---

## 📐 Development Conventions

### General
- **Tone:** Professional, direct, and technical.
- **Context:** Always consider which sub-project you are working in. The constraints for the portfolio (static export) do NOT apply to Channel Stream (full-stack).

### Next.js (Main Portfolio)
- **Static Constraints:** No server-side logic (e.g., `getServerSideProps` or standard API routes). Every page must be statically renderable.
- **Client Components:** Most interactive pages currently use `"use client"`.
- **Styling:** Tailwind CSS v4 using zinc/blue palette. Use `dark:` variants for dark mode support.
- **Testing:** Currently no automated tests in the JS layer.

### Python (ETL & AWS Collector)
- **Tooling:** Use `ruff` for linting/formatting.
- **Testing:** AWS Collector has high test coverage using `botocore.Stubber` for AWS mocking.
- **Data Models:** Centralized in `src/models.py` for the collector.

### Channel Stream
- **Database:** Uses Supabase migrations (`supabase/migrations/`) and seeds (`supabase/seed.sql`).
- **Caching:** Redis is used for feed caching with 90s-10m TTLs.

---

## 📁 Directory Structure (Key Paths)

- `app/`: Main portfolio pages (App Router).
- `components/`: Shared React components.
- `scripts/`: Python ETL pipeline scripts.
- `AWS Compliance collector/`: NIST compliance project.
- `Channel_Stream/`: Sports discovery platform project.
- `data/processed/`: Target for ETL scripts; source for portfolio data.

---

## 📝 TODOs & Future State
- [ ] Consume `data/processed/*.json` in portfolio pages instead of inline data.
- [ ] Implement automated tests for the portfolio frontend.
- [ ] Migrate "Coming Soon" placeholders in `/consulting` and `/architecture-cases`.
- [ ] Finalize Channel Stream Phase 2 (Frontend dashboard).
