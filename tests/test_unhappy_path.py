import os

import pytest
from click.testing import CliRunner

from skedulord.cli import init


@pytest.fixture()
def clean_slate():
    os.system("lord nuke --really --sure")
    yield 1
    os.system("lord nuke --really --sure")


@pytest.fixture()
def cli():
    return CliRunner()


def test_run_without_init(clean_slate, cli):
    assert os.system('lord run pyjob "python jobs/badpyjob.py"') != 0


def test_history_without_init(clean_slate, cli):
    assert os.system('lord history') != 0


def test_summary_without_init(clean_slate, cli):
    assert os.system('lord summary"') != 0


def test_serve_without_init(clean_slate, cli):
    assert os.system('lord serve"') != 0


def test_init_complains(clean_slate, cli):
    # let us initialize first
    result = cli.invoke(init)
    # and check if we get a notification after
    result = cli.invoke(init)
    print(result.output)
    assert ".skedulord allready exists" in result.output