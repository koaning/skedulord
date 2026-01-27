import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from skedulord.__main__ import app
from skedulord.dashboard import export_static_site
from skedulord.db import fetch_runs


@pytest.fixture()
def clean_start_with_runs():
    """Create some test runs before export."""
    os.system("python -m skedulord wipe disk --really --yes")
    os.system("python -m skedulord run job-one 'python jobs/pyjob.py'")
    os.system("python -m skedulord run job-two 'python jobs/pyjob.py'")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")


@pytest.fixture()
def empty_start():
    """Start with empty database."""
    os.system("python -m skedulord wipe disk --really --yes")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")


def test_export_creates_directory_structure(clean_start_with_runs):
    """Export should create the expected directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        export_static_site(output_dir)

        assert output_dir.exists()
        assert (output_dir / "api").exists()
        assert (output_dir / "api" / "runs.json").exists()
        assert (output_dir / "api" / "logs").exists()


def test_export_runs_json_format(clean_start_with_runs):
    """Export should create runs.json with correct format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        export_static_site(output_dir)

        runs_json = output_dir / "api" / "runs.json"
        data = json.loads(runs_json.read_text())

        assert isinstance(data, list)
        assert len(data) >= 2  # At least the 2 test runs

        # Check each run has expected fields
        for run in data:
            assert "id" in run
            assert "name" in run
            assert "command" in run
            assert "status" in run
            assert "start" in run
            assert "end" in run
            assert "logpath" in run


def test_export_creates_log_files(clean_start_with_runs):
    """Export should create a log JSON file for each run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        export_static_site(output_dir)

        runs_json = output_dir / "api" / "runs.json"
        runs = json.loads(runs_json.read_text())

        logs_dir = output_dir / "api" / "logs"
        for run in runs:
            log_file = logs_dir / f"{run['id']}.json"
            assert log_file.exists(), f"Log file for run {run['id']} should exist"

            log_data = json.loads(log_file.read_text())
            assert "logpath" in log_data
            assert "content" in log_data


def test_export_empty_database(empty_start):
    """Export should work with empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        count = export_static_site(output_dir)

        assert count == 0
        assert (output_dir / "api" / "runs.json").exists()

        runs = json.loads((output_dir / "api" / "runs.json").read_text())
        assert runs == []


def test_export_cli_command(clean_start_with_runs):
    """The export CLI command should work."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        result = runner.invoke(app, ["export", "--output", str(output_dir)])

        assert result.exit_code == 0
        assert "Exported" in result.output
        assert (output_dir / "api" / "runs.json").exists()


def test_export_returns_run_count(clean_start_with_runs):
    """Export should return the number of runs exported."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "export"
        count = export_static_site(output_dir)

        # Count should match what's in runs.json
        runs_json = output_dir / "api" / "runs.json"
        runs = json.loads(runs_json.read_text())
        assert count == len(runs)
