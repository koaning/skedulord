import os
import pathlib

import pytest
from typer.testing import CliRunner

from skedulord.common import skedulord_path
from skedulord.db import fetch_runs
from skedulord.__main__ import app
from skedulord import __version__ as lord_version


@pytest.fixture()
def clean_start_small():
    os.system("python -m skedulord wipe disk --really --yes")
    os.system("python -m skedulord run foo 'python jobs/pyjob.py'")
    os.system("python -m skedulord run bar 'python jobs/pyjob.py'")
    os.system("python -m skedulord run buz 'python jobs/pyjob.py'")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")


@pytest.fixture()
def dirty_start_small():
    os.system("python -m skedulord wipe disk --yes --really")
    os.system("python -m skedulord run buz 'python jobs/pyjob.py'")
    os.system("python -m skedulord run bad 'python jobs/badpyjob.py' --wait 1")
    yield 1
    os.system("python -m skedulord wipe disk --yes --really")


@pytest.fixture()
def dirty_start_via_schedule():
    os.system("python -m skedulord wipe disk --yes --really")
    os.system("python -m skedulord run good-job --settings-path tests/schedule.yml")
    os.system("python -m skedulord run bad-job --settings-path tests/schedule.yml --wait 1")
    os.system("python -m skedulord run printer --settings-path tests/schedule.yml")
    yield 1
    os.system("python -m skedulord wipe disk --yes --really")


def test_basic_history(clean_start_small):
    assert len(list(fetch_runs())) == 3


def test_adv_heartbeat_file(dirty_start_small):
    assert len(list(fetch_runs())) == 2


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert lord_version in result.output


def test_history_name(clean_start_small):
    runner = CliRunner()
    result = runner.invoke(app, ["history"])
    assert any(["bar" in line for line in result.output.split("\n")])
    result = runner.invoke(app, ["history", "--jobname", "baz"])
    assert all(["foo" not in line for line in result.output.split("\n")])


def test_history_only_failures(dirty_start_small):
    runner = CliRunner()
    result = runner.invoke(app, ["history"])
    assert "bad" in result.output
    result = runner.invoke(app, ["history", "--only-failures"])
    assert "bad" in result.output
    assert "buz" not in result.output


def test_jobs_run_via_schedule(dirty_start_via_schedule):
    runner = CliRunner()
    result = runner.invoke(app, ["history"])
    assert "good-job" in result.output
    result = runner.invoke(app, ["history", "--only-failures"])
    assert "bad-job" in result.output
    assert "good-job" not in result.output
    printer_path = skedulord_path() / "printer"
    logfile = next(printer_path.glob("*.txt"))
    printer_logs = pathlib.Path(logfile).read_text()
    assert "--this that" in printer_logs
    assert "--one two" in printer_logs
    assert "--three 3" in printer_logs
