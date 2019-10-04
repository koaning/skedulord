import os
import json

import pytest

from skedulord.common import HEARTBEAT_PATH


@pytest.fixture()
def clean_state():
    os.system("skedulord nuke --really --sure")
    os.system("skedulord setup --name yoyo --attempts 3 --wait 1")
    yield 1
    os.system("skedulord nuke --really --sure")


def test_basic_heartbeat1(clean_state):
    os.system("skedulord run 'python jobs/run.py' foo")
    os.system("skedulord run 'python jobs/run.py' bar")
    os.system("skedulord run 'python jobs/run.py' foo")
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 3
    assert {_['name'] for _ in jobs} == {'foo','bar'}


def test_basic_heartbeat2(clean_state):
    os.system("skedulord run 'python jobs/run.py' foo")
    os.system("skedulord run 'python jobs/run.py' bar")
    os.system("skedulord run 'python jobs/run.py' foo")
    os.system("skedulord run 'python jobs/run.py' bar")
    os.system("skedulord run 'python jobs/run.py' buz")
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 5
    assert {_['name'] for _ in jobs} == {'foo', 'bar', 'buz'}
