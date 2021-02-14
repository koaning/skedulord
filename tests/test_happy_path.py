import os
import json

import pytest
from typer.testing import CliRunner
from clumper import Clumper

from skedulord.common import heartbeat_path
from skedulord.__main__ import app
from skedulord import __version__ as lord_version


@pytest.fixture()
def clean_start_small():
    os.system("python -m skedulord wipe disk --really --yes")
    os.system("python -m skedulord wipe schedule --really --yes")
    os.system("python -m skedulord run foo 'python jobs/pyjob.py'")
    os.system("python -m skedulord run bar 'python jobs/pyjob.py'")
    os.system("python -m skedulord run buz 'python jobs/pyjob.py'")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")
    os.system("python -m skedulord wipe schedule --really --yes")


@pytest.fixture()
def dirty_start_small():
    os.system("python -m skedulord wipe disk --yes --really")
    os.system("python -m skedulord wipe schedule --really --yes")
    os.system("python -m skedulord run buz 'python jobs/pyjob.py'")
    os.system("python -m skedulord run bad 'python jobs/badpyjob.py'")
    yield 1
    os.system("python -m skedulord wipe disk --yes --really")
    os.system("python -m skedulord wipe schedule --really --yes")


def test_basic_heartbeat_file(clean_start_small):
    with open(heartbeat_path(), "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 3
    assert {_['name'] for _ in jobs} == {'foo', 'bar', 'buz'}


def test_basic_history(clean_start_small):
    assert len(Clumper.read_jsonl(heartbeat_path())) == 3


def test_adv_heartbeat_file(dirty_start_small):
    jobs = Clumper.read_jsonl(heartbeat_path()).collect()
    assert len(jobs) == 2
    assert {_['name'] for _ in jobs} == {'buz', 'bad'}


def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert lord_version in result.output
