from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from skedulord.db import fetch_run, fetch_runs


def create_app() -> FastAPI:
    app = FastAPI(title="Skedulord API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

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
        if not logpath.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        return {"logpath": str(logpath), "content": logpath.read_text()}

    return app


app = create_app()
