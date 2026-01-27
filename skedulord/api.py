import base64
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from skedulord.auth import verify_password
from skedulord.common import skedulord_path
from skedulord.db import fetch_run, fetch_runs, fetch_user


def _basic_credentials(auth_header: str | None) -> tuple[str, str] | None:
    if not auth_header:
        return None
    if not auth_header.lower().startswith("basic "):
        return None
    encoded = auth_header.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    username, sep, password = decoded.partition(":")
    if not sep:
        return None
    return username, password


def create_app(no_auth: bool = False, cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="Skedulord API", version="0.1.0")
    if cors_origins is None:
        env_origins = os.getenv("SKEDULORD_CORS_ORIGINS", "")
        cors_origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def auth_middleware(request, call_next):
        if no_auth:
            return await call_next(request)
        path = request.url.path
        if path in ("/api/health", "/api/config"):
            return await call_next(request)
        requires_auth = path.startswith("/api") or path.startswith("/docs") or path == "/openapi.json"
        if not requires_auth:
            return await call_next(request)
        credentials = _basic_credentials(request.headers.get("authorization"))
        if not credentials:
            headers = {"WWW-Authenticate": "Basic"} if path.startswith("/docs") or path == "/openapi.json" else None
            return Response(status_code=401, headers=headers)
        username, password = credentials
        row = fetch_user(username)
        if not row or not verify_password(password, row["password_hash"]):
            headers = {"WWW-Authenticate": "Basic"} if path.startswith("/docs") or path == "/openapi.json" else None
            return Response(status_code=401, headers=headers)
        return await call_next(request)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/config")
    def config() -> dict:
        return {"no_auth": no_auth}

    @app.get("/api")
    def api_root() -> dict:
        return {
            "message": "Skedulord API",
            "health": "/api/health",
            "runs": "/api/runs",
            "docs": "/docs",
        }

    @app.get("/api/runs")
    def list_runs(
        limit: Optional[int] = 50,
        name: Optional[str] = None,
        status: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        rows = fetch_runs(limit=limit, name=name, status=status, date=date)
        return [dict(row) for row in rows]

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        row = fetch_run(run_id)
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        return dict(row)

    @app.get("/api/logs/{run_id}")
    def get_log(run_id: str) -> dict:
        row = fetch_run(run_id)
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        logpath = Path(row["logpath"])
        base_path = skedulord_path().resolve()
        resolved_logpath = logpath.resolve()
        try:
            resolved_logpath.relative_to(base_path)
        except ValueError:
            raise HTTPException(status_code=403, detail="Log file is outside the skedulord data directory")
        if not logpath.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        return {
            "logpath": str(resolved_logpath),
            "content": logpath.read_text(),
        }

    package_static = Path(__file__).resolve().parent / "static"
    repo_dist = Path(__file__).resolve().parents[1] / "webapp" / "dist"
    dist_path = package_static if package_static.exists() else repo_dist
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
    else:
        @app.get("/")
        def root() -> dict:
            return {
                "message": "Skedulord API",
                "health": "/api/health",
                "runs": "/api/runs",
                "docs": "/docs",
            }

    return app


app = create_app()
