from pathlib import Path

import pytest
from skedulord.cron import parse_job_from_settings, Cron

checks = [
    {
        "name": "foo",
        "command": "python foobar.py",
        "arguments": {"hello": "world"},
        "expected": "python foobar.py --hello world",
    },
    {
        "name": "foo",
        "command": "python foobar.py",
        "arguments": {"hello": "world", "one": 1},
        "expected": "python foobar.py --hello world --one 1",
    },
    {
        "name": "download",
        "command": "python -m gitwit download apache/airflow",
        "expected": "python -m gitwit download apache/airflow",
    }
]


@pytest.mark.parametrize("check", checks)
def test_job_parsing(check):
    """Test that the job is parsed correctly from the settings"""
    res = parse_job_from_settings(settings=[check], name=check["name"])
    assert res["command"] == check["expected"]
    assert res["retry"] == check.get("retry", 2)
    assert res["wait"] == check.get("wait", 60)


def test_cron_obj_parsing():
    """Test that the cron object parses the schedule appropriately"""
    c = Cron("tests/schedule.yml")
    expected_path = Path("tests/schedule.yml").resolve()
    for s in c.settings:
        parsed_command = c.parse_cmd(s)
        assert parsed_command.rstrip() == parsed_command
        assert "uv run python -m skedulord run" in parsed_command
        assert "--settings-path" in parsed_command
        assert str(expected_path) in parsed_command
