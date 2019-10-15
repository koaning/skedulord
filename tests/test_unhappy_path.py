import os
import pathlib
import subprocess

import pytest


@pytest.fixture()
def clean_slate():
    os.system("lord nuke --really --sure")
    yield 1
    os.system("lord nuke --really --sure")


def test_run_without_init(clean_slate):
    assert os.system('lord run pyjob "python jobs/badpyjob.py"') != 0


def test_history_without_init(clean_slate):
    assert os.system('lord history') != 0


def test_summary_without_init(clean_slate):
    assert os.system('lord summary"') != 0


def test_serve_without_init(clean_slate):
    assert os.system('lord serve"') != 0
