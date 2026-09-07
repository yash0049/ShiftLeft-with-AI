# SecureTrack

A small vulnerability and asset tracker: a Flask REST API backed by SQLite, and a React
(Vite) frontend for browsing and editing the data.

Track your **assets** (servers, databases, applications) and the **vulnerabilities**
found on them, with severity and remediation status on each finding.

```
securetrack/
├── backend/          Flask API + SQLite
│   ├── app/
│   │   ├── __init__.py       app factory
│   │   ├── models.py         SQLAlchemy models
│   │   ├── validation.py     request-body validation helpers
│   │   ├── errors.py         JSON error handlers
│   │   └── routes/           health, assets, vulnerabilities blueprints
│   ├── tests/                pytest suite
│   ├── run.py                dev entrypoint
│   └── seed.py               optional sample data
└── frontend/         React + Vite
    └── src/
        ├── api.js            fetch wrapper
        ├── App.jsx           layout, state, tabs
        └── components/       forms and tables
```

## Requirements

- Python 3.10+
- Node.js 18+

## Running it locally

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

The Vite dev server proxies `/api` and `/health` to Flask on port 5000, so the browser
only ever talks to one origin and CORS never comes into play during development. If your
backend runs somewhere else, point the proxy at it:

```bash
VITE_API_TARGET=http://127.0.0.1:8000 npm run dev
```

## Running the tests

```bash
cd backend
.venv\Scripts\Activate.ps1     # or: source .venv/bin/activate
pytest
```

39 tests cover both resources: CRUD happy paths, validation failures, 404s, partial
updates, query filters, and the cascade delete. They run against a throwaway in-memory
SQLite database, so your local `securetrack.db` is never touched.

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
  model, delete `backend/securetrack.db` and restart, or add Flask-Migrate.
- **Deleting an asset deletes its findings** along with it. The UI warns you and shows the
  count first.
- `DATABASE_URL` overrides the SQLite location, and `CORS_ORIGINS` (comma-separated)
  overrides the allowed origins if you run the frontend without the Vite proxy.
