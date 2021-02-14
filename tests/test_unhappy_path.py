import os

import pytest
from click.testing import CliRunner


@pytest.fixture()
def clean_slate():
    os.system("lord wipe disk --really --yes")
    yield 1
    os.system("lord wipe disk --really --yes")


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
