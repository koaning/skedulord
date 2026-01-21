# Contributing

## Local demo server

This repo ships with a small end‑to‑end demo that seeds a few runs, starts the API, and lets
you launch the React webapp against it.

### Prerequisites

- Python 3.9+
- `uv`
- Node.js 18+

### Quickstart

```bash
make demo-install
make demo-run
```

This will:

- wipe `~/.skedulord` state
- run a handful of demo jobs (including a failing one)
- build the webapp and serve it from FastAPI at `http://127.0.0.1:8000` (API is under `/api/*`, docs at `/docs`)

The demo server uses the following credentials:

- **Username:** `admin`
- **Password:** `admin`

In another terminal, you can also run the webapp dev server:

```bash
make demo-web
```

### Cleanup

```bash
make demo-clean
```

## Notes

- The API is read‑only for now; job triggering will require auth.
- Demo jobs are defined in `jobs/` and run via `uv run python`.
