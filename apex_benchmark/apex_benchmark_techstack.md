# ApexBench: Tech Stack & Implementation Blueprint
## Designed for Claude Code Execution on AWS

This document serves as the standalone technical specification and step-by-step execution roadmap for building **ApexBench**. It defines a strictly bounded minimum viable product (MVP) structured around a containerized AWS architecture, following the core progression principles of the project playbook.

---

## 1. Core Tech Stack (Boring, Predictable AWS Monolith)

To minimize operational overhead, configuration fragmentation, and deployment friction, the application is designed as a single containerized monolith.

| Layer | Technology | Selection Strategy |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.11+ / FastAPI** | High performance, native async execution, rapid prototyping, automatic OpenAPI document generation. |
| **Frontend/UI Layer** | **Jinja2 + Tailwind CSS (via CDN) + Alpine.js** | Server-rendered templates avoiding the complexity of a decoupled SPA framework. High reactivity via Alpine.js. |
| **Database Engine** | **Amazon RDS PostgreSQL** | Fully managed relational storage engine. Built on a cost-effective Single-AZ `db.t4g.micro` instance. |
| **Containerization** | **Docker** | Guarantees absolute environment parity between local testing loops and production AWS targets. |
| **Compute / Hosting** | **AWS App Runner** | Managed container execution environment. Eliminates the manual networking, cluster, and scaling configuration overhead of AWS ECS/EKS. |
| **Authentication Engine** | **Amazon Cognito Hosted UI** (or **Supabase Auth**) | Fully managed user management and cryptographic protection. Bypasses custom security implementation risks. |
| **Storage / Backups** | **Amazon S3** | Secure, highly durable object storage target for automated daily database transaction logs. |

---

## 2. Sequential Milestone & Implementation Plan

### Phase 1: The Walking Skeleton (Front-Load AWS Connection Pain)
*Objective: Build an end-to-end cloud pipeline to verify networking, container compilation, and database routing boundaries before implementing core product features.*

#### Milestone 1.1: Local Repository & Container Scaffolding
* **Objective:** Establish the foundational directory layout and configure a local multi-tier container execution setup.
* **Action Steps:**
    1. Scaffold standard directories: `app/api`, `app/core`, `app/db`, `app/models`, `app/templates`, and `tests`.
    2. Write a minimal FastAPI `main.py` application exposing a `/health` endpoint.
    3. Construct a production-ready `Dockerfile` multi-stage build pattern utilizing a clean virtual environment block.
* **Verification Command:**
  ```bash
  docker build -t apexbench . && docker run -d -p 8000:8000 apexbench && sleep 2 && curl http://localhost:8000/health