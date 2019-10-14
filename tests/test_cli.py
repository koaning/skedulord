import os
import json

import pytest

from skedulord.common import HEARTBEAT_PATH
from skedulord.web.app import create_app


@pytest.fixture()
def clean_start_small():
    os.system("skedulord nuke --really --sure")
    os.system("skedulord init")
    os.system("skedulord run foo 'python jobs/pyjob.py'")
    os.system("skedulord run bar 'python jobs/pyjob.py'")
    os.system("skedulord run buz 'python jobs/pyjob.py'")
    print("created new skedulord env")
    yield 1
    os.system("skedulord nuke --really --sure")


@pytest.fixture()
def dirty_start_small():
    os.system("skedulord nuke --really --sure")
    os.system("skedulord init")
    os.system("skedulord run buz 'python jobs/pyjob.py'")
    os.system("skedulord run bad 'python jobs/badpyjob.py'")
    print("created new skedulord env")
    yield 1
    os.system("skedulord nuke --really --sure")


def test_basic_heartbeat_file(clean_start_small):
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 3
    assert {_['name'] for _ in jobs} == {'foo', 'bar', 'buz'}


def test_basic_heartbeat_server(clean_start_small):
    test_app = create_app().test_client()
    json_blob = test_app.get("/api/test_heartbeats").get_json()
    assert len(json_blob) == 3
    assert {_['name'] for _ in json_blob} == {'foo', 'bar', 'buz'}


def test_adv_heartbeat_file(dirty_start_small):
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    assert len(jobs) == 2
    assert {_['name'] for _ in jobs} == {'buz', 'bad'}


def test_adv_heartbeat_server(dirty_start_small):
    test_app = create_app().test_client()
    json_blob = test_app.get("/api/test_heartbeats").get_json()
    assert len(json_blob) == 2
    assert {_['name'] for _ in json_blob} == {'buz', 'bad'}
