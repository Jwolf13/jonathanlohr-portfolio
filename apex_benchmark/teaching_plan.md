To transform Claude Code into an effective interactive teacher, you need to establish a feedback-driven execution loop. Instead of asking it to do things for you, you will use it to provide structural guardrails, review your code, explain errors conceptually, and map out mental models before you start typing.

Here is the best way to structure your interaction with Claude Code to maximize your learning as you build ApexBench.

1. Setting the "Teacher Persona"
Every time you open a new terminal session with Claude Code, establish the ground rules immediately. This keeps the AI from writing code for you when you ask for help.

Paste this at the start of your session:

Plaintext
We are working on the ApexBench app. Your role is my Senior Code Reviewer and Tech Lead. 
Do not write implementation code for me unless I explicitly use the word "SPOILER". 

Instead, follow this teaching protocol:
1. When I ask how to do something, provide a conceptual breakdown, pseudo-code, or an ASCII architecture diagram showing the data flow.
2. Provide hints, code signatures, or point me to relevant documentation/libraries.
3. If I submit code, give me a code review focusing on Python best practices, security, and logic errors.
2. The Interactive Commands (Your Toolkit)
Use these four specific prompt styles as you work through the empty framework files:

📋 Scenario A: You don't know where to start on a file
Before you write code for a specific feature (like the evaluation logic), ask for a conceptual blueprint. This helps you visualize how data moves through your Python code.

What to prompt:

Plaintext
I'm ready to write the logic inside `app/services/evaluation.py` for `evaluate_timed_metric`. Can you draw a quick ASCII map showing how the user_score and elite_baseline interact, and give me a 3-step pseudo-code logic breakdown for how to handle a timed test where a lower score is better?
🛠️ Scenario B: You wrote code and want a code review
Once you fill in a function or an API route, do not just run it blind. Have your "teacher" review your work first.

What to prompt:

Plaintext
I have implemented the code inside `app/api/endpoints.py` for the `POST /evaluate` route. I'm going to display the code below. Please review it for:
1. Correct FastAPI dependency usage.
2. Edge cases (like what happens if a user inputs a 0 or a negative number).
3. Pythonic readability. 
Do not rewrite it; just give me bullet points of what I can improve.

[Paste your code here]
❌ Scenario C: Your code crashes or tests fail
Debugging is where the best learning happens. If a test fails or uvicorn throws an error, don't ask Claude to fix it. Ask it to explain why it broke.

What to prompt:

Plaintext
I ran `pytest tests/test_evaluation.py` and it failed with this error message:
[Paste error here]

Can you explain conceptually what this error means in Python, what typically causes it, and point me to the file/line where I made the mistake? Let me try to fix it myself first.
🛡️ Scenario D: You want to learn AWS best practices
Since you are deploying a containerized application to AWS, you can use Claude to understand the operational side of things without getting bogged down in configuration.

What to prompt:

Plaintext
We are about to set up the connection to Amazon RDS PostgreSQL. Can you explain how the application container running inside AWS App Runner securely talks to the RDS database using environment variables? Show me an ASCII diagram of the network flow so I can understand how secrets stay hidden from the GitHub repository.
3. The Recommended Coding Order for Maximum Learning
To keep your momentum moving forward without feeling overwhelmed, tackle the empty scaffolding files in this exact sequence:

The Pure Logic (app/services/evaluation.py): Start here because it's pure Python math. No databases, no web requests. Just inputs, processing, and outputs. Write the code, write the tests, run pytest.

The Data Engine (app/models/athletic.py & app/db/seed.py): Learn how SQLAlchemy maps Python objects to PostgreSQL tables. Write your data structures, then write the script to insert the real-world athlete data.

The API Layer (app/api/endpoints.py): Learn how FastAPI takes web inputs (JSON requests), interacts with your database session, passes data to your services layer, and returns a response.

The UI Interface (app/templates/dashboard.html): Tie it all together. Learn how HTML forms send information back into your Python application and display the results dynamically.

What You Are Doing First: The "Walking Skeleton"
In plain English, you are building a hollow, empty frame of your application. You are creating a single, boring webpage that connects to a completely empty database, wraps it inside a container, and deploys it to the cloud (AWS).

It will have zero features. No athletic tests, no workout scaling, no calculations, and no logic. It will literally just say "Healthy" or "Hello World."

Why Are You Doing This?
Most people make the mistake of spending three weeks writing beautiful Python code, building database tables, and designing a gorgeous frontend on their own laptop. Then, they try to deploy it to AWS, it crashes, and they spend a week staring at error messages because they don't know if their Python code is broken or if their AWS settings are wrong.

By building a "Walking Skeleton" first, you are testing the plumbing before you buy the fancy faucets. You prove that:

Your computer can talk to AWS.

Your web server can talk to your database.

Your app can live on the internet.

Once the plumbing works, you can write your Python code with 100% confidence, knowing that the moment you hit "save," it will work perfectly in the cloud.

What Exactly Are You Creating Right Now?
You are setting up the empty canvas. You are telling Claude Code to create:

The Folders: Organizes where your database code, your web pages, and your math logic will live later.

The Config Files: A requirements.txt file (a shopping list of Python packages you need) and a Dockerfile (a set of instructions that boxes up your app so it runs exactly the same on your laptop as it does on AWS).

The Base Server (main.py): A file that turns on FastAPI (your web framework) and listens for a simple connection check.

Your First Prompt for Claude Code
Open up Claude Code in your completely empty project directory, copy and paste this exact prompt, and hit enter. This will set Claude up as your teacher and build your empty framework.

Plaintext
I am building an athletic metrics and workout scaling web app called ApexBench using FastAPI, RDS PostgreSQL, and AWS App Runner. 

I am using this project to learn Python, backend development, and AWS. Your role is strictly to act as my Tech Lead and Teacher. 

CRITICAL RULES FOR YOU:
1. Do NOT write any actual business logic, mathematical calculation formulas, or database data yet.
2. DO create the exact folder structure, configuration files, Dockerfiles, and empty code frameworks so I can write the code myself later.
3. For Python files, write empty code stubs: include all necessary imports, typed function definitions, classes, and API route structures, but leave the function bodies empty using `raise NotImplementedError("User to implement")` or `TODO` comments.

STEP 1 TASK:
Please scaffold Phase 1 (The Walking Skeleton):
- Create these empty directories: `app/api`, `app/core`, `app/db`, `app/models`, `app/schemas`, `app/templates`, and `tests`.
- Create a `requirements.txt` file listing: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic, jinja2, pytest, httpx.
- Create a multi-stage `Dockerfile` that installs these requirements and prepares to run the app on port 8000.
- Create a barebones `app/main.py` that initializes FastAPI and includes a simple, fully working `/health` route that returns `{"status": "healthy"}`.

When you are done, run the local docker build and a curl command in the terminal to veri

ou are learning how to build a production-grade, layered software system.

In professional software engineering, applications are separated into distinct "layers" so that if you change the database or the user interface, the core math doesn't break. You are learning how to manage data storage, how to write defensive business logic, how to expose that logic to the internet via an API, and how to host it safely in a secure cloud ecosystem.

Plaintext
+-------------------------------------------------------+
|                 YOUR APPLICATION LAYERS               |
|                                                       |
|   1. THE UI TIER     --> Jinja2 / Tailwind / Alpine   |
|         |                                             |
|   2. THE API TIER    --> FastAPI Routers            |
|         |                                             |
|   3. THE LOGIC TIER  --> Pure Python Algorithms       |
|         |                                             |
|   4. THE DATA TIER   --> SQLAlchemy ORM & Postgres    |
+-------------------------------------------------------+
The Textbook Roadmap: Phase-by-Phase
Here is your syllabus. For each phase, we break down the Theory (the computer science concepts) and the Practice (how to prompt Claude to be your interactive teacher).

Phase 1: Database Design & Object-Relational Mapping (ORM)
The Theory: You will learn how databases organize information using columns, data types (integers, strings, floats), and relationships (Foreign Keys). You will learn about ORMs (Object-Relational Mapping), which is a translation layer that lets you manipulate database rows using pure Python classes instead of writing raw SQL database commands.

Cybersecurity Angle: You will learn how database connection strings use secret environment variables so passwords never get leaked or checked into public source control.

How to Prompt Claude for this Lesson:

Plaintext
"I'm ready for Phase 1: Database Design. Before I write anything in `app/models/athletic.py`, act as my textbook author. Explain to me conceptually what an 'ORM' is and how a 'Foreign Key' links the Metric table to the Benchmark table. Give me a clean ASCII layout of how these tables look conceptually, and show me the empty Python class signatures with type hints I should write. Do not write the implementation code for me."
Phase 2: Core Algorithms & Defensive Programming
The Theory: You will learn how to write isolated, deterministic functions. You will master Type Hinting (declaring exactly what kind of data a function is allowed to accept and return). You will practice Defensive Programming—anticipating user errors (like entering a weight of 0 or a negative 40-yard dash time) and handling those edge cases gracefully before they crash your app. You will also learn Unit Testing by writing scripts that test your math automatically.

How to Prompt Claude for this Lesson:

Plaintext
"I am working on `app/services/evaluation.py`. I need to write the formulas for timed tests and output tests. Act as my teacher: don't write the Python code yet. Give me the pseudo-code for how to handle edge cases like a user inputting a '0'. Then, show me a blueprint for how to write a test matrix using `pytest` so I can verify my own code once I write it."
Phase 3: The Web API & Request-Response Lifecycle
The Theory: You will learn the architecture of the web: the Client-Server model. You will study HTTP verbs (GET for retrieving data, POST for sending data) and JSON payloads. You will learn Dependency Injection, a crucial design pattern used to safely open a database connection when a user makes a request, pass that connection to your route, and close it cleanly when the request finishes so your server never leaks memory.

How to Prompt Claude for this Lesson:

Plaintext
"We are moving to `app/api/endpoints.py`. Explain to me like a textbook the exact step-by-step lifecycle of an HTTP POST request from the moment a user clicks 'Submit' on a browser to the moment FastAPI returns a JSON response. Explain what 'Dependency Injection' means in the context of our database session (`get_db`), and give me the empty function headers for my routes to get me started."
Phase 4: Server-Side Templates vs. Client Reactivity
The Theory: You will learn how the visual web works. You'll explore Server-Side Rendering (Jinja2), where Python builds the HTML page dynamically before sending it over the network, vs. Client-Side Reactivity (Alpine.js), where lightweight JavaScript runs directly inside the user's browser to make the page feel snappy and interactive without forcing a full page reload every time they type a number.

How to Prompt Claude for this Lesson:

Plaintext
"I'm opening `app/templates/dashboard.html`. Explain the division of labor between Jinja2 and Alpine.js. When should Python render data, and when should JavaScript handle it on the user's screen? Show me the foundational HTML structure I need, with clear code comments pointing out where I should bind my frontend data variables."
Phase 5: Cloud Plumbing & Container Security (DevOps)
The Theory: You will learn virtualization concepts using Docker containers—packaging code, runtimes, and system tools into an isolated image that runs identically anywhere. You will learn cloud networking fundamentals on AWS: how to use firewall rules (Security Groups) to allow an application running on AWS App Runner to speak to your AWS RDS database while completely blocking the outside public internet from attacking your database.

How to Prompt Claude for this Lesson:

Plaintext
"The app is working locally! Before we deploy to AWS, teach me about cloud security. Draw an ASCII network map showing AWS App Runner, Amazon RDS, and the public internet. Explain how Security Groups act as a virtual firewall to protect our database, and walk me through the step-by-step AWS CLI commands I need to run to securely push our Docker container to Amazon ECR."
Your Exact First Step Right Now
To start the practical training loop, make sure your empty project folder is open in your terminal, initialize Claude Code, and send it this opening request to begin Phase 1 (Database & Data Modeling):

Plaintext
"Teacher, the Walking Skeleton configuration is set. I am ready to learn Phase 1: Database Design and Data Modeling. 

Before I write code in `app/models/athletic.py`, give me the conceptual lesson. Explain how SQLAlchemy models map Python classes to database tables. Draw a clear ASCII diagram of our three tables (Metric, Benchmark, Protocol) showing how they link together using Primary Keys and Foreign Keys. 

Conclude the lesson by giving me the empty Python class frameworks with type hints and TODO comments so I can write the database models myself."