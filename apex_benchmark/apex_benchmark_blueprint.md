# Actionable Implementation Plan: Athletic Metrics & Workout Scaling App
## Optimized for Claude Code Execution & AWS Deployment (Based on The Personal Project Playbook)

This implementation plan acts as your explicit engineering blueprint to build **ApexBench**, a web application designed to benchmark personal performance against elite athletic standards (e.g., NFL Combine, Olympic Lifting standards) and dynamically scale training protocols based on performance gaps. All infrastructure is mapped directly to Amazon Web Services (AWS).

---

## 1. Project Filter & Core Constraints
Before writing code, the project definition must satisfy the playbook's foundational product safety filters:
* **One-Sentence Scope:** "A simple web application hosted on AWS to compare personal athletic scores against top athlete milestones and receive instant, scaled workout adjustments."
* **Definition of "Done":** "I can log in via a managed provider, select an athletic test, enter my personal score, view my percentage performance gap against a top athlete benchmark, and read the scaled training guide to build up to that test."
* **Target Audience:** Built for a single primary user (you) to prevent feature creep and optimize internal validation loops.

---

## 2. System Requirements & Scope Cutting

### Functional Requirements (MVP Only)
To guarantee completion within the 3–5 weekend timeline, the feature list is strictly capped below 7 items:
1. **Managed User Authentication:** User sign-up and login via a secure managed provider (Amazon Cognito or Supabase).
2. **Metric Directory:** View a clean dashboard containing core athletic metrics across categories (Speed: *40-Yard Dash*, Power: *Vertical Jump*, Strength: *Back Squat*, Endurance: *VO2 Max*).
3. **Score Submission:** Input personal scores for a chosen test.
4. **Elite Benchmarking Engine:** Compare personal inputs against pre-seeded elite athletic datasets to determine an explicit achievement percentage.
5. **Dynamic Workout Scaling View:** Display contextual training protocols matching the user's score tiers to step-by-step progress their physical baseline.
6. **Metric Deletion:** Allow resetting or deleting personal metrics records to manage logs easily.

### Post-MVP Deferred Features (Strictly Out of Scope)
The following are **deferred** to post-MVP iterations:
* ❌ No historical tracking charts, graphs, or visual analytics dashboards.
* ❌ No custom recurring training calendar schedules or notifications.
* ❌ No multi-user social leaderboards or profile sharing capabilities.
* ❌ No native mobile application development (clean responsive web view only).
* ❌ No custom UI themes or dark mode switching engines.

### Non-Functional Requirements
* **Scalability:** Optimized for exactly 1 user (you), stripping away the need for distributed architectural complexities.
* **Latency:** Page render and API performance under 2.0 seconds is fully acceptable.
* **Availability:** Monitored informally under a personal "up when I look at it" standard.
* **Security:** High priority. Passwords must never be stored in plain text, AWS credentials must remain strictly out of the repository codebase, and interactions must run securely via HTTPS.
* **Durability:** Automated simple daily database dumps backing up directly to an Amazon S3 bucket.

---

## 3. Playbook Default Architecture (AWS Focused)
The design relies strictly on a boring, predictable, single-instance containerized architecture to eliminate configuration roadblocks while utilizing reliable AWS services.

```text
[Browser/Phone View] --------HTTPS--------> [AWS App Runner / ECS Fargate (FastAPI Monolith)]
        |                                                     |
        v                                                     v
[Managed Auth (Cognito / Supabase)]                  [Amazon RDS PostgreSQL]
                                                              |
                                                     (Daily Backup Script)
                                                              v
                                                     [Amazon S3 Bucket]