import os

import pytest
from fastapi.testclient import TestClient

from skedulord.api import create_app
from skedulord.common import skedulord_path
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


def test_logs_endpoint_returns_full_content(clean_slate):
    logpath = skedulord_path() / "test" / "test.log"
    logpath.parent.mkdir(parents=True, exist_ok=True)
    logpath.write_text("line-0\nline-1\nline-2")

    insert_run(
        run_id="run-test",
        name="test",
        command="echo test",
        status="success",
        start="2024-01-01 00:00:00",
        end="2024-01-01 00:00:01",
        logpath=str(logpath),
    )

    client = TestClient(create_app(no_auth=True))
    response = client.get("/api/logs/run-test")
    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "line-0\nline-1\nline-2"
    assert "logpath" in payload


def test_config_endpoint_returns_no_auth_false_by_default(clean_slate):
    client = TestClient(create_app(no_auth=False))
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == {"no_auth": False}


def test_config_endpoint_returns_no_auth_true_when_enabled(clean_slate):
    client = TestClient(create_app(no_auth=True))
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == {"no_auth": True}


def test_config_endpoint_accessible_without_auth(clean_slate):
    # When auth is required, /api/config should still be accessible
    client = TestClient(create_app(no_auth=False))
    # No auth headers provided
    response = client.get("/api/config")
    assert response.status_code == 200
