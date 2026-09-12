# SecureTrack

A small vulnerability and asset tracker: a Flask REST API backed by SQLite, and a React
(Vite) frontend for browsing and editing the data.

Track your **assets** (servers, databases, applications) and the **vulnerabilities**
found on them, with severity and remediation status on each finding.

```
securetrack/
├── docker-compose.yml      backend + frontend + a volume for the SQLite file
├── run-local.sh            build and start the whole stack
├── test-local.sh           run the backend + frontend test suites
├── backend/            Flask API + SQLite
│   ├── app/
│   │   ├── __init__.py         app factory
│   │   ├── models.py           SQLAlchemy models
│   │   ├── validation.py       request-body validation helpers
│   │   ├── errors.py           JSON error handlers
│   │   └── routes/             health, assets, vulnerabilities blueprints
│   ├── tests/                  pytest suite
│   ├── run.py                  dev entrypoint, and the gunicorn target
│   ├── seed.py                 optional sample data
│   └── Dockerfile              python:3.12-slim + gunicorn
└── frontend/           React + Vite
    ├── src/
    │   ├── api.js              fetch wrapper
    │   ├── App.jsx             layout, state, tabs
    │   ├── components/         forms and tables
    │   └── *.test.jsx          vitest suite
    ├── nginx.conf              static hosting + /api proxy to the backend
    └── Dockerfile              node build stage → nginx runtime
```

## Requirements

There are two ways to run SecureTrack. Pick one:

- **With Docker** — Docker Desktop (or Docker Engine) with Compose v2. Nothing else.
- **Directly on your machine** — Python 3.10+ and Node.js 18+.

## Quick start with Docker

```bash
./run-local.sh
```

That builds both images, starts the stack, waits until each service answers, and prints
the URLs. Open <http://localhost:5173>.

To come up with some data already in place:

```bash
./run-local.sh --seed
```

Everything the script takes:

| Command                    | What it does                                          |
| -------------------------- | ----------------------------------------------------- |
| `./run-local.sh`           | Build, start, wait for health, print URLs             |
| `./run-local.sh --seed`    | ...and load sample assets and findings                |
| `./run-local.sh --logs`    | ...and then follow the logs                           |
| `./run-local.sh --down`    | Stop and remove the stack                             |
| `./run-local.sh --down -v` | ...and delete the SQLite volume, wiping all your data |

> **On Windows**, run the scripts from Git Bash or WSL. From PowerShell, use the
> `docker compose` commands directly — see [Without the script](#without-the-script).

### What's running

| Service    | Image                   | URL                     |
| ---------- | ----------------------- | ----------------------- |
| `frontend` | nginx serving the build | <http://localhost:5173> |
| `backend`  | gunicorn running Flask  | <http://localhost:5000> |

nginx serves the compiled React app and proxies `/api` and `/health` through to Flask over
the compose network. Exactly as with the Vite dev proxy, the browser only ever talks to a
single origin, so CORS stays out of the picture.

The backend port is published as well, so you can still curl the API directly:

```bash
curl http://localhost:5000/health
```

### Where the data lives

The SQLite file sits on a named Docker volume (`securetrack-data`) mounted at `/data` in
the backend container, so it survives `docker compose down`, container restarts, and image
rebuilds. Only `./run-local.sh --down -v` deletes it.

To pull the database out for inspection or backup:

```bash
docker compose cp backend:/data/securetrack.db ./securetrack.db
```

If you would rather have the file sitting in the repo where you can see it, swap the named
volume for a bind mount in `docker-compose.yml`:

```yaml
volumes:
  - ./data:/data # instead of: securetrack-data:/data
```

### Without the script

The script is only a convenience wrapper. Plain Compose does the same:

```bash
docker compose up --build -d                  # start
docker compose logs -f                        # follow logs
docker compose exec backend python seed.py    # seed sample data
docker compose down                           # stop
```

## Running without Docker

You need two terminals: one for the API, one for the frontend.

### 1. Backend (port 5000)

```bash
cd backend

python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

The API is now on <http://127.0.0.1:5000>. The SQLite file `backend/securetrack.db` is
created automatically on first start.

Want some data to look at? In the same virtualenv:

```bash
python seed.py
```

Check it's alive:

```bash
curl http://127.0.0.1:5000/health
# {"status": "ok", "database": "ok"}
```

### 2. Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

The Vite dev server proxies `/api` and `/health` to Flask on port 5000. If your backend
runs somewhere else, point the proxy at it:

```bash
VITE_API_TARGET=http://127.0.0.1:8000 npm run dev
```

## Running the tests

```bash
./test-local.sh
```

That runs both suites inside Docker, so it needs no Python or Node on your machine. To use
your local toolchain instead (the virtualenv in `backend/.venv`, and `npm`):

```bash
./test-local.sh --local
```

Either mode takes an optional target:

```bash
./test-local.sh --local backend    # just pytest
./test-local.sh frontend           # just vitest, in Docker
```

The script exits non-zero if anything fails, and names the failing suite.

**Backend — 39 pytest tests** covering CRUD happy paths, validation failures, 404s,
partial updates, query filters, and the cascade delete. They run against a throwaway
in-memory SQLite database, so your `securetrack.db` is never touched.

**Frontend — 24 vitest tests** covering the API client (request shapes, the 204 case,
error and field-error extraction, an unreachable API), the list components, and `App`
itself — loading, the summary counts, tab switching, create, edit prefill, delete
confirmation, and the offline banner — with the API module mocked.

Either suite also runs the usual way:

```bash
cd backend  && pytest
cd frontend && npm test
```

## API reference

Base URL `http://127.0.0.1:5000`. All request and response bodies are JSON.

### Health

| Method | Path      | Notes                                                     |
| ------ | --------- | --------------------------------------------------------- |
| GET    | `/health` | Returns `200` with a live DB check, or `503` if unreachable |

### Assets

| Method | Path               | Notes                                    |
| ------ | ------------------ | ---------------------------------------- |
| GET    | `/api/assets`      | List all assets, newest first            |
| GET    | `/api/assets/<id>` | Fetch one asset                          |
| POST   | `/api/assets`      | Create; returns `201`                    |
| PUT    | `/api/assets/<id>` | Partial update — omitted fields are kept |
| DELETE | `/api/assets/<id>` | Returns `204`; cascades to its findings  |

Fields: `name` (required), `asset_type`, `ip_address`, `owner`, `description`.

`asset_type` is one of `server`, `workstation`, `database`, `application`, `network`,
`other` (defaults to `other`).

Responses also include a computed `vulnerability_count`.

```bash
curl -X POST http://127.0.0.1:5000/api/assets \
  -H 'Content-Type: application/json' \
  -d '{"name":"web-01","asset_type":"server","ip_address":"10.0.0.5"}'
```

### Vulnerabilities

| Method | Path                        | Notes                                    |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/vulnerabilities`      | List all findings, newest first          |
| GET    | `/api/vulnerabilities/<id>` | Fetch one finding                        |
| POST   | `/api/vulnerabilities`      | Create; returns `201`                    |
| PUT    | `/api/vulnerabilities/<id>` | Partial update — omitted fields are kept |
| DELETE | `/api/vulnerabilities/<id>` | Returns `204`                            |

Fields: `title` (required), `severity`, `status`, `cve_id`, `description`, `asset_id`.

- `severity` is one of `critical`, `high`, `medium`, `low`, `info` (defaults to `medium`)
- `status` is one of `open`, `in_progress`, `resolved`, `accepted` (defaults to `open`)
- `asset_id` is optional; it must reference a real asset, or `null` for unassigned

`GET /api/vulnerabilities` accepts optional `severity`, `status`, and `asset_id` query
filters:

```bash
curl 'http://127.0.0.1:5000/api/vulnerabilities?severity=critical&status=open'
```

### Errors

Validation failures return `400` and name every bad field at once, so a form can show all
its errors in one pass:

```json
{
  "error": "Validation failed",
  "details": {
    "title": "This field is required",
    "severity": "Must be one of: critical, high, medium, low, info"
  }
}
```

Missing records return `404` as `{"error": "Asset not found"}`.

## Notes and current limitations

- **No authentication.** Every endpoint is open. This is a local development tool as it
  stands; don't expose it to a network without putting auth in front of it.
- **No migrations.** Tables are created with `db.create_all()` at startup. If you change a
  model, delete the database and restart — `./run-local.sh --down -v` under Docker — or
  add Flask-Migrate.
- **Deleting an asset deletes its findings** along with it. The UI warns you and shows the
  count first.
- **SQLite and concurrency.** The container runs two gunicorn workers against one SQLite
  file. That is fine at this scale, but SQLite serializes writes, so this arrangement
  would not hold up under real write concurrency — that's the point to move to Postgres.
- **nginx resolves the backend hostname once, at startup.** Compose waits for the backend
  to pass its healthcheck before starting the frontend, so this is handled on the way up;
  but if you recreate the backend container on its own, restart the frontend too.
- `DATABASE_URL` overrides the SQLite location (the image sets it to
  `/data/securetrack.db`), and `CORS_ORIGINS` (comma-separated) overrides the allowed
  origins if you ever serve the frontend from another origin without a proxy.
