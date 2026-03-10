# Contributing

## Local demo server

### Quickstart

```bash
make demo-install
make demo-run
```

This starts the API at `http://127.0.0.1:8000` with demo data and no authentication.

Run the webapp dev server in another terminal:

```bash
cd webapp && npm install && npm run dev
```

### Testing with authentication

To test authentication:

```bash
uv run python -m skedulord serve --reload
```

Add a user:

```bash
uv run python -m skedulord users add --username myuser
```

### Cleanup

```bash
make demo-clean
```
