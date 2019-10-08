import os
import json

import pytest

from skedulord.common import HEARTBEAT_PATH
from skedulord.web.app import create_app


@pytest.fixture()
def clean_start():
    os.system("skedulord nuke --really --sure")
    os.system("skedulord setup --name yoyo --attempts 3 --wait 1")
    yield 1
    os.system("skedulord nuke --really --sure")


def test_basic_heartbeat1(clean_start):
    os.system("skedulord run foo 'python jobs/run.py'")
    os.system("skedulord run bar 'python jobs/run.py'")
    os.system("skedulord run foo 'python jobs/run.py'")
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 3
    assert {_['name'] for _ in jobs} == {'foo', 'bar'}


def test_basic_heartbeat2(clean_start):
    os.system("skedulord run foo 'python jobs/run.py'")
    os.system("skedulord run bar 'python jobs/run.py'")
    os.system("skedulord run foo 'python jobs/run.py'")
    os.system("skedulord run bar 'python jobs/run.py'")
    os.system("skedulord run buz 'python jobs/run.py'")
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 5
    assert {_['name'] for _ in jobs} == {'foo', 'bar', 'buz'}


def test_basic_heartbeat_server(clean_start):
    os.system("skedulord run foo 'python jobs/run.py'")
    os.system("skedulord run bar 'python jobs/run.py'")
    os.system("skedulord run buz 'python jobs/run.py'")
    test_app = create_app().test_client()
    json_blob = test_app.get("/api/test_heartbeats").get_json()
    print(json_blob)
    assert len(json_blob) == 3
    assert {_['name'] for _ in json_blob} == {'foo', 'bar', 'buz'}
