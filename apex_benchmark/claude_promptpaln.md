The "Scaffolding Mode" Strategy
When running in this mode, Claude's job is strictly to:

Create the complete directory tree.

Install configuration files (Dockerfile, requirements.txt, Makefile).

Write empty Python classes, functions, and API routes using strict Type Hinting and raise NotImplementedError() or pass statements.

Add clear code comments and TODO tags explaining what you need to implement.

Step 1: Initialize the Workspace & Set the Learning Rules
Create an empty directory, save this prompt structure, and feed it to Claude Code as your initial frame of reference.

Copy/Paste Prompt 1: The Guardrails

Plaintext
I am building an athletic metrics and workout scaling web app called ApexBench using FastAPI, RDS PostgreSQL, and AWS App Runner. 

I am using this project to learn Python and backend development. Your role is strictly to act as an Architectural Scaffolder. 

CRITICAL RULES:
1. Do NOT write the actual business logic, mathematical calculation formulas, or database seeding data.
2. DO create the exact folder structure, configuration files, Dockerfiles, and deployment configurations.
3. For Python files, write complete code stubs: include all imports, typed function definitions, classes, Pydantic schemas, and API route definitions, but leave the function bodies empty using `raise NotImplementedError("User to implement")` or `TODO` comments.
4. Confirm you understand that you are only creating the empty frameworks so I can write the code myself. Do not write any code yet.
Step 2: Phase 1 Prompts — The Infrastructure Skeleton
This phase lets Claude handle the tedious DevOps configuration (which can be a barrier to entry) while leaving the application development entirely to you.

Copy/Paste Prompt 2: Directory & System Scaffolding

Plaintext
Let's build Phase 1: The Walking Skeleton Framework. 

Please create the folder structure and configuration files exactly as follows:
1. Create directories: `app/api`, `app/core`, `app/db`, `app/models`, `app/schemas`, `app/templates`, `tests`, and `scripts`.
2. Create a `requirements.txt` containing: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic, jinja2, pytest, httpx.
3. Create a multi-stage `Dockerfile` that sets up a virtual environment, copies the `app` directory, installs requirements, and prepares to run `uvicorn app.main:main --host 0.0.0.0 --port 8000`.
4. Create a barebones `app/main.py` that initializes FastAPI, mounts a static folder, sets up Jinja2 templates, and includes an implemented `/health` route (so we can test the container). All other core initialization should be stubbed out.

Verify that the container builds and runs locally using:
`docker build -t apexbench . && docker run -d -p 8000:8000 apexbench && sleep 2 && curl http://localhost:8000/health`
Stop here and show me the structural layout.
Copy/Paste Prompt 3: Database Lifecycle & Connection Stubs

Plaintext
Now, let's scaffold the database connection layer in `app/db/session.py`. 
1. Use SQLAlchemy to set up the engine and sessionmaker declarations.
2. Read the database URL from an environment variable (`DATABASE_URL`), defaulting to a local postgres placeholder if not found.
3. Write an empty generator function `get_db()` with type annotations that handles yielding and closing a session wrapper. Use comments to show where the transaction lifecycle boundary sits.
4. In `app/db/base.py`, import a declarative base so my future models can register to it.
Step 3: Phase 2 Prompts — Data Model & Seeding Stubs
Here, Claude will build out the structural definitions of your data tables, leaving the table mappings and script mechanics for you to populate.

Copy/Paste Prompt 4: Database Models & Seeding Framework

Plaintext
Let's scaffold our relational database schemas and seed entrypoints:
1. In `app/models/athletic.py`, declare empty SQLAlchemy classes for `Metric` (to hold tests like 40-Yard dash), `Benchmark` (to hold elite standards), and `Protocol` (to hold workouts). Include column definitions using Type Hinting (e.g., Integer, String, Float, ForeignKey) but leave relationships or advanced properties as TODO blocks.
2. In `app/schemas/athletic.py`, create the Pydantic validation stubs: `MetricResponse`, `UserEvaluationRequest`, and `WorkoutResponse` with the structural fields but no advanced validator logic.
3. In `app/db/seed.py`, write an entrypoint script shell with a `def seed_database(db: Session):` function. Inside, add descriptive comments pointing out exactly where I should write the insert statements for the 40-Yard Dash, Vertical Jump, Back Squat, and VO2 Max elite parameters.
Step 4: Phase 3 Prompts — The Core Learning Engine
This is where the learning happens. You want Claude to give you clean API routes and empty Python modules so you can sit down and program the core features.

Copy/Paste Prompt 5: Route & Algorithm Scaffolding

Plaintext
Let's scaffold the core service engine and API layer where I will be writing my code:
1. Create `app/services/evaluation.py`. Write two typed function definitions:
   - `def evaluate_timed_metric(user_score: float, elite_baseline: float) -> float:`
   - `def evaluate_output_metric(user_score: float, elite_baseline: float) -> float:`
   Add a docstring to each explaining that timed metrics mean lower is better, and output metrics mean higher is better. Put `pass` in the function body.
2. Create `app/api/endpoints.py`. Setup a FastAPI `APIRouter()`.
3. Add empty route endpoints for:
   - `GET /metrics` (to retrieve the directory)
   - `POST /evaluate` (to process user input and return scores)
4. Use dependency injection syntax (`Depends(get_db)`) on the endpoints, but leave the route logic blocks as `raise NotImplementedError("Implement evaluation mechanics")`.
Step 5: Phase 4 Prompts — Frontend Layout Stubs
Instead of writing complex UI layouts, Claude will handle the page structure bindings so you can write the interaction layer using pure HTML and styles.

Copy/Paste Prompt 6: Frontend Layout Scaffolding

Plaintext
Let's scaffold the web templates using Jinja2:
1. Create `app/templates/base.html`. Put a semantic HTML5 shell in it. Include the Tailwind CSS CDN link and the Alpine.js script tag in the `<head>`. Define a `{% block content %}{% endblock %}` injection frame.
2. Create `app/templates/dashboard.html` extending `base.html`. Inside, write a clean, empty HTML structural form for inputting individual user athletic numbers, and an empty results wrapper block. 
3. Use HTML comments to point out where I should bind Alpine.js variables (`x-data`, `x-model`) and where Jinja tags should loop through metrics.
🚀 Why this workflow rules for learning:
Zero DevOps Friction: Claude sets up the Docker configurations, virtual environment links, and dependencies perfectly, meaning your environment compiles without error.

No Code Overwhelm: You open up clean, professionally structured files with explicit signatures (def evaluate_timed_metric(user_score: float, elite_baseline: float) -> float:).

Targeted Implementation: Your only task is to step through the files, replace the pass or TODO lines with actual Python math and database queries, and watch your application come to life piece by piece.