import os
import json

import pytest
from click.testing import CliRunner

from skedulord.common import HEARTBEAT_PATH
from skedulord.__main__ import history, summary, version
from skedulord import version as lord_version


@pytest.fixture()
def clean_start_small():
    os.system("lord nuke --really --yes")
    os.system("lord init")
    os.system("lord run foo 'python jobs/pyjob.py'")
    os.system("lord run bar 'python jobs/pyjob.py'")
    os.system("lord run buz 'python jobs/pyjob.py'")
    yield 1
    os.system("lord nuke --really --yes")


@pytest.fixture()
def dirty_start_small():
    os.system("lord nuke --yes --really")
    os.system("lord init")
    os.system("lord run buz 'python jobs/pyjob.py'")
    os.system("lord run bad 'python jobs/badpyjob.py'")
    yield 1
    os.system("lord nuke --yes --really")


def test_basic_heartbeat_file(clean_start_small):
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 3
    assert {_['name'] for _ in jobs} == {'foo', 'bar', 'buz'}


def test_basic_summary(clean_start_small):
    runner = CliRunner()
    result = runner.invoke(summary)
    print(result.output)
    assert len(result.output.split("\n")) == 8
    assert result.exit_code == 0
    assert 'foo' in result.output
    assert 'bar' in result.output
    assert 'buz' in result.output


def test_basic_history(clean_start_small):
    runner = CliRunner()
    result = runner.invoke(history)
    assert result.exit_code == 0
    assert len(result.output.split("\n")) == 8
    assert 'foo' in result.output
    assert 'bar' in result.output
    assert 'buz' in result.output
    assert '✅' in result.output


def test_adv_heartbeat_file(dirty_start_small):
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 2
    assert {_['name'] for _ in jobs} == {'buz', 'bad'}


def test_adv_history(dirty_start_small):
    runner = CliRunner()
    result = runner.invoke(history)
    assert result.exit_code == 0
    assert len(result.output.split("\n")) == 7
    assert 'bad' in result.output
    assert 'buz' in result.output
    assert '✅' in result.output
    assert '❌' in result.output


def test_adv_summary(dirty_start_small):
    runner = CliRunner()
    result = runner.invoke(history)
    assert result.exit_code == 0
    assert len(result.output.split("\n")) == 7
    assert 'bad' in result.output
    assert 'buz' in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(version)
    assert result.exit_code == 0
    assert lord_version in result.output
