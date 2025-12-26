import os

import pytest
from typer.testing import CliRunner


@pytest.fixture()
def clean_slate():
    os.system("python -m skedulord wipe disk --really --yes")
    yield 1
    os.system("python -m skedulord wipe disk --really --yes")


@pytest.fixture()
def cli():
    return CliRunner()


def test_history_without_init(clean_slate, cli):
    assert os.system("python -m skedulord history") != 0


def test_summary_without_init(clean_slate, cli):
    assert os.system("python -m skedulord summary") != 0

