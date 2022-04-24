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
    assert res == check["expected"]


def test_cron_obj_parsing():
    """Test that the cron object parses the schedule appropriately"""
    c = Cron("tests/schedule.yml")
    for s in c.settings:
        parsed_command = c.parse_cmd(s)
        assert parsed_command.rstrip() == parsed_command
        assert '--retry' in parsed_command
        assert '--wait' in parsed_command
