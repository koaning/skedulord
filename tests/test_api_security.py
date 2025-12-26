import os

import pytest
from fastapi.testclient import TestClient

from skedulord.api import create_app
from skedulord.db import insert_run


@pytest.fixture()
def clean_slate():
    os.system("python -m skedulord wipe disk --really --yes")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")


def test_logs_endpoint_rejects_paths_outside_data_dir(clean_slate, tmp_path):
    external_log = tmp_path / "external.log"
    external_log.write_text("do not read")

    insert_run(
        run_id="run-outside",
        name="outside",
        command="echo outside",
        status="success",
        start="2024-01-01 00:00:00",
        end="2024-01-01 00:00:01",
        logpath=str(external_log),
    )

    client = TestClient(create_app(no_auth=True))
    response = client.get("/api/logs/run-outside")
    assert response.status_code == 403


def test_cors_disabled_by_default(clean_slate, monkeypatch):
    monkeypatch.delenv("SKEDULORD_CORS_ORIGINS", raising=False)
    client = TestClient(create_app(no_auth=True))
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_enabled_via_env(clean_slate, monkeypatch):
    monkeypatch.setenv("SKEDULORD_CORS_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app(no_auth=True))
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
