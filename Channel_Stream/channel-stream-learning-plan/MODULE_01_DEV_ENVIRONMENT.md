# Module 1 — Your Dev Environment & Tools
### Setting Up Your Machine So You Can Build Channel Stream

---

> **Goal**: By the end of this module, every tool you need is installed, verified, and understood. You should never have to Google "how do I install Go" again — it's all here.

> **Time**: ~60–90 minutes (most of it is download time)

---

## 1.1 Understanding What You're Installing and Why

Before running any install command, understand what you're actually getting:

| Tool | Why You Need It | Where It Lives |
|---|---|---|
| **VS Code** | The editor where you write all your code | Your Applications folder |
| **Docker Desktop** | Runs PostgreSQL and Redis locally (in isolated containers) | Your system, runs in background |
| **Go** | The language your backend is written in | `/usr/local/go` on Mac/Linux |
| **Node.js** | Runs the Supabase CLI and the Next.js frontend | `/usr/local` |
| **Supabase CLI** | A command-line tool to manage your local database | Your PATH |
| **Git** | Tracks every change you make to your code | Built into Mac, needs install on Windows |
| **Claude Code** | AI coding assistant that works inside your terminal | Installed via npm |

---

## 1.2 Install Order (Do These in Order)

### Step 1: Install VS Code

1. Go to https://code.visualstudio.com/
2. Download the version for your operating system
3. Install it (drag to Applications on Mac, run installer on Windows)
4. Open VS Code

**Install these extensions** (click the Extensions icon in the left sidebar, search each name):
- `Go` (by Google) — syntax highlighting and tools for Go code
- `PostgreSQL` (by Chris Kolkman) — see your database inside VS Code
- `ESLint` — catches JavaScript/TypeScript errors
- `Prettier` — automatically formats your code to look clean
- `GitLens` — shows who changed what line of code and when
- `Thunder Client` — test API endpoints without leaving VS Code (like Postman, but simpler)
- `Docker` (by Microsoft) — see and manage your Docker containers

---

### Step 2: Install Docker Desktop

Docker lets you run software (like PostgreSQL and Redis) in isolated "containers" without installing them directly on your machine. Think of containers like lunchboxes — each one is self-contained.

1. Go to https://www.docker.com/products/docker-desktop/
2. Download for your OS
3. Install and open Docker Desktop
4. Wait for the whale icon in your system tray/menu bar to stop animating (it's ready when it's still)

**Verify**:
```bash
docker --version
# Expected output: Docker version 24.x.x, build xxxxxxx

docker run hello-world
# Expected: Prints "Hello from Docker!" and some text
```

If you see "Hello from Docker!" — Docker is working. If you see an error, make sure Docker Desktop is open and running.

---

### Step 3: Install Node.js

Node.js lets you run JavaScript outside of a browser. The Supabase CLI and Next.js both need it.

1. Go to https://nodejs.org/
2. Download the **LTS** (Long Term Support) version — NOT the "Current" version
3. Install it

**Verify**:
```bash
node --version
# Expected: v20.x.x  (or higher)

npm --version
# Expected: 10.x.x  (or higher)
```

---

### Step 4: Install Go

Go is the programming language your backend is written in. It was created by Google and is known for being fast and simple.

1. Go to https://go.dev/dl/
2. Download the installer for your OS
3. Run the installer

**Verify**:
```bash
go version
# Expected: go version go1.22.x linux/amd64  (or darwin for Mac)
```

**Understand your Go workspace**:
```bash
go env GOPATH
# This shows where Go stores your code and downloaded packages
# Usually: /home/yourname/go  (Linux/Mac) or C:\Users\yourname\go  (Windows)
```

---

### Step 5: Install the Supabase CLI

Supabase is a service that wraps PostgreSQL with extra tools. The CLI lets you run it locally.

**On Mac** (using Homebrew — install Homebrew first if needed: https://brew.sh):
```bash
brew install supabase/tap/supabase
```

**On Windows** (using Scoop):
```powershell
# First install Scoop if you don't have it:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
irm get.scoop.sh | iex

# Then install Supabase:
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

**On Linux**:
```bash
brew install supabase/tap/supabase
# (Homebrew works on Linux too)
```

**Verify**:
```bash
supabase --version
# Expected: 2.x.x
```

---

### Step 6: Install Git

Git tracks every change you make to your code. It's how you save versions and collaborate.

**Mac**: Git is usually pre-installed. Verify with `git --version`. If not, Xcode Command Line Tools installs it: `xcode-select --install`

**Windows**: Download from https://git-scm.com/download/win and install.

**Verify**:
```bash
git --version
# Expected: git version 2.x.x
```

**Configure Git** (do this once — it labels your commits):
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### Step 7: Install Claude Code

Claude Code is an AI coding assistant that lives in your terminal. You write commands, it writes and modifies code.

```bash
npm install -g @anthropic-ai/claude-code
```

**Verify**:
```bash
claude --version
```

To start it in any project folder:
```bash
claude
```

---

## 1.3 Create Your Project Structure

Now that your tools are installed, create the Channel Stream project folder.

```bash
# Go to your home directory
cd ~

# Create the project
mkdir channel-stream
cd channel-stream

# Initialize Git (start tracking changes)
git init

# Create a .gitignore file (tells Git what NOT to track)
cat > .gitignore << 'EOF'
# Go
*.exe
*.test
/bin/

# Environment variables (NEVER commit these — they contain secrets)
.env
.env.local
.env.*.local

# Supabase local config
supabase/.branches
supabase/.temp

# Node/Next.js
node_modules/
.next/
.vercel/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/settings.json
EOF
```

Now initialize Supabase:
```bash
supabase init
```

This creates a `supabase/` folder. You'll use this in Module 2.

Your folder now looks like:
```
channel-stream/
├── supabase/          ← Supabase config and migrations
│   └── config.toml   ← Local Supabase settings
├── .gitignore         ← Files Git ignores
└── (more folders coming in later modules)
```

---

## 1.4 Understanding Claude Code (Your AI Pair Programmer)

Claude Code works differently from a chat interface. You give it tasks in natural language, and it writes, edits, and runs code for you. Here's how to use it effectively:

### How to Start a Session

```bash
# Navigate to your project folder first
cd ~/channel-stream

# Start Claude Code
claude
```

### Good Commands to Give Claude Code

Instead of vague requests, be specific:

❌ Bad: "Make the backend work"
✅ Good: "Create a new file at `internal/feed/upnext.go`. It should have a function called `GetUpNextFeed` that takes a `profileID string` parameter, queries PostgreSQL for all watch_state records where status = 'in_progress', joins the content table, sorts by last_watched DESC, and returns a slice of `FeedItem` structs."

❌ Bad: "Fix the error"  
✅ Good: "I'm getting this error: `pgx: cannot scan into *string: oid 114 (json)`. The error is in `internal/feed/watchnow.go` at line 42. Fix it."

### Useful Claude Code Commands

| Command | What it does |
|---|---|
| `claude` | Opens interactive mode in current folder |
| `claude "explain this file"` | Asks Claude to explain a specific file |
| `claude --continue` | Continues your last session |
| `/help` | Shows available commands inside Claude |
| `/clear` | Clears the conversation |

### The Playwright MCP Connection

You mentioned you're using Claude Code with the Playwright MCP. This means Claude Code can actually *open a browser, click things, and check that the UI works*. You'll use this heavily in Module 6 (Testing).

To verify Playwright MCP is working:
```bash
# Inside a Claude Code session, ask it:
# "Open a browser and navigate to http://localhost:8080/v1/health and tell me what you see"
# If Playwright is connected, it will actually do this.
```

---

## 1.5 Make Your First Git Commit

Now that your project is set up, save your work:

```bash
# See what files are new (untracked)
git status

# Stage all files for commit
git add .

# Commit with a message describing what you did
git commit -m "Initial project setup: Supabase init, .gitignore"
```

**Git commit messages** are a record of your progress. Good messages:
- `feat: add Up Next feed endpoint`
- `fix: resolve JSON scanning error in watch_state query`
- `docs: add Redis caching explanation to README`

Bad messages:
- `stuff`
- `fix`
- `asdfgh`

---

## 1.6 Create a GitHub Repository (Remote Backup)

GitHub stores your code in the cloud so you never lose it.

1. Go to https://github.com and create an account if you don't have one
2. Click the `+` icon → **New repository**
3. Name it `channel-stream`
4. Keep it **Private** for now
5. Do NOT check "Add README" (you already have a project)
6. Click **Create repository**

GitHub will show you commands — copy the "push an existing repository" section:

```bash
git remote add origin https://github.com/YOUR_USERNAME/channel-stream.git
git branch -M main
git push -u origin main
```

Now your code is backed up on GitHub. Every time you make a commit, push it:
```bash
git push
```

---

## 1.7 Environment Variables — The Secrets File

Your app needs database passwords and API keys. These **never** go in your code — they go in a `.env` file that Git ignores.

Create your first `.env` file:
```bash
# In your channel-stream folder
touch .env
```

Open it and add:
```
# Local Supabase (these are safe defaults for local dev only)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGci...  # You'll get this after running supabase start

# Redis (local)
REDIS_URL=redis://localhost:6379

# App settings
PORT=8080
APP_ENV=development
```

**Rule**: If it's a password, a secret key, or a token — it goes in `.env`. Never in code. Never in Git.
test
---

## 1.8 Quick Reference Card

Print this or keep it in a notes app:

```
=== SUPABASE COMMANDS ===
supabase start              → Start local database
supabase stop               → Stop local database
supabase db reset           → Wipe and rebuild database from migrations
supabase migration new NAME → Create a new database migration
supabase status             → Show local URLs and keys
Open: http://localhost:54323 → Supabase Studio (database dashboard)

=== GO COMMANDS ===
go run ./cmd/server         → Start the backend server
go test ./...               → Run all tests
go build -o channel-stream ./cmd/server  → Build a deployable binary
go get <package>            → Install a dependency

=== GIT COMMANDS ===
git status                  → Show what changed
git add .                   → Stage all changes
git commit -m "message"     → Save a snapshot
git push                    → Upload to GitHub
git log --oneline           → See history of commits

=== DOCKER COMMANDS ===
docker ps                   → See running containers
docker stop <name>          → Stop a container
docker logs <name>          → See output from a container

=== REDIS (via Docker) ===
docker run -d --name channel-stream-redis -p 6379:6379 redis:7-alpine
docker exec channel-stream-redis redis-cli ping   → Should say PONG
```

---

## 1.9 Checkpoint: Before You Continue

Verify everything works:

```bash
# 1. Docker is running
docker ps

# 2. Go is installed
go version

# 3. Node is installed  
node --version

# 4. Supabase CLI is installed
supabase --version

# 5. Git is configured
git config --list | grep user
```

If all five commands return something (not an error), you're ready.

---

**Next**: [Module 2 → Database — PostgreSQL & Supabase](./MODULE_02_DATABASE.md)
