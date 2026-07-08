# Running VisionOps AI locally

This guide gets the whole platform running on your machine and set up nicely in
VS Code (or any editor). **Docker is the supported way to run the stack** — it
provides Python 3.12, PostgreSQL, Redis, MinIO, and MediaMTX in containers so you
don't install any of them on your host.

- Web UI → http://localhost:3000
- API → http://localhost:8000 (`/health`, `/ready`, `/docs`)
- MinIO console → http://localhost:9001
- Gateway → http://localhost:8080

---

## 1. Prerequisites

| Tool | Why | Install (macOS) |
| --- | --- | --- |
| **Docker Desktop** | Runs the whole stack | `brew install --cask docker` then open it |
| **Node ≥ 20 + pnpm ≥ 9** | Frontend tooling, lint, editor IntelliSense | `brew install node && corepack enable` |
| Git | Version control | preinstalled / `brew install git` |

Python, Postgres, Redis, etc. are **not** required on the host — Docker supplies
them. (A local Python venv is only needed if you want backend IntelliSense/tests
in the editor — see §5.)

Verify:
```bash
docker --version        # Docker daemon must be running (whale icon in menu bar)
node --version
pnpm --version
```

---

## 2. First run (Docker — the whole stack)

From the project root:

```bash
cp .env.example .env    # if you don't already have a .env
pnpm install            # JS deps (editor IntelliSense + lint; not needed to run containers)
npm run dev             # or `pnpm dev` — builds + starts the whole stack
```

`npm run dev` runs `docker compose up --build`. It streams all service logs and
stays in the foreground — press **Ctrl+C** to stop. The API **auto-applies
database migrations on startup**, so there is no manual schema step (even after
`down -v`).

In a second terminal, confirm everything is healthy:
```bash
docker compose ps
curl localhost:8000/ready     # -> postgres "up", redis "up"
```

Open **http://localhost:3000** and register an account.

> Prefer detached mode (no log stream)? Use `docker compose up -d --build`, then
> `npm run dev:logs` to tail.

### Email in dev
SMTP is intentionally unset in dev, so verification / password-reset emails are
**written to the API logs instead of being sent**. Grab your verification link:

```bash
docker compose logs api | grep -oE 'http://localhost:3000/verify-email\?token=[A-Za-z0-9_-]+' | tail -1
```

Paste it into the browser to verify, then log in. (To send real email instead,
set `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` in `.env` and restart the `api` and
`worker` services.)

---

## 3. Everyday commands

```bash
docker compose up -d              # start (add --build only when code changed)
docker compose down               # stop, keep data
docker compose down -v            # stop and WIPE db/volumes (then re-run migrations)
docker compose ps                 # service status
docker compose logs -f api        # tail one service
docker compose exec api bash      # shell into the api container
docker compose restart api        # restart one service after a code change
```

> After editing backend code, rebuild just that service:
> `docker compose up -d --build api` (or `worker` / `ai-engine`).

---

## 4. Frontend-only quick loop (no Docker)

The Next.js UI is pure Node, so you can iterate on it without containers. The
backend still needs to be up (via Docker) for API calls to work.

```bash
pnpm --filter @visionops/web dev   # http://localhost:3000, hot reload
```

---

## 5. Editor setup

### VS Code (recommended)
1. Open the folder. VS Code will prompt to install the **recommended extensions**
   (`.vscode/extensions.json`): Python, Ruff, ESLint, Prettier, Tailwind, Docker,
   Go. Accept.
2. `.vscode/settings.json` is already configured: format-on-save (Prettier for
   TS/JSON, Ruff for Python), ESLint auto-fix, and hidden build noise.
3. Run tasks from **Terminal → Run Task…** (`.vscode/tasks.json`):
   *Stack: Up*, *Stack: Down*, *DB: Migrate*, *Web: Dev server*,
   *Dev: Get email verification link*, *Lint: all packages*, etc.
4. Debug from the **Run and Debug** panel (`.vscode/launch.json`):
   *Web: Next.js dev* and *Web: Debug in Chrome*.

**Frontend IntelliSense** works immediately after `pnpm install` (Node is local).

**Backend (Python) IntelliSense** — the API code runs in Docker, so to get import
resolution, type hints, and `pytest` in the editor, create a local venv with the
same deps (needs Python 3.12):

```bash
brew install python@3.12
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
Then in VS Code: **Cmd+Shift+P → Python: Select Interpreter →**
`apps/api/.venv/bin/python`. Repeat per app (`apps/worker`, `apps/ai-engine`) if
you want IntelliSense there too. This venv is for the editor only — the app still
runs via Docker.

### Cursor / Windsurf
Same as VS Code — they read `.vscode/` settings, extensions, tasks, and launch
configs directly. Install the recommended extensions when prompted.

### JetBrains (PyCharm / WebStorm)
- Open the repo root. Mark `apps/web/src` etc. as sources if needed.
- **Python interpreter:** point PyCharm at `apps/api/.venv` (create it as in §5)
  or use its Docker Compose interpreter (`api` service).
- **Node:** WebStorm auto-detects `pnpm`; run scripts from the npm tool window.
- Run the stack from the built-in terminal with the `docker compose` commands
  in §3, or via the Docker plugin.

### Any other editor (Neovim, Zed, …)
The editor just needs the language servers; running is always the same
`docker compose` commands. Install `pnpm install` for TS, and a Python 3.12 venv
(§5) for Python LSP (pyright/pylsp) if desired.

---

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker: command not found` | Docker Desktop not installed / not on PATH — open a new terminal after install |
| `uvicorn`/`celery: command not found` | You ran `npm run dev:native` (runs everything natively, needs local Python 3.12 + Go). Use `npm run dev` (Docker) instead. |
| API keeps restarting | `docker compose logs api` to see the error. Migrations run automatically on startup, so this is usually a code/config issue. |
| "Please verify your email" | Grab the link from the API logs (§2). Dev doesn't send real email. |
| Port already in use (3000/8000) | Stop the other process, or change the host port mapping in `docker-compose.yml` |
| Data gone after `down -v` | Expected (volumes wiped). Migrations re-run automatically on the next `npm run dev` — just re-register. |
