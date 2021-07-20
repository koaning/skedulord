import pytest
from skedulord.cron import parse_job_from_settings

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
    res = parse_job_from_settings(settings=[check], name="foo")
    assert res == check["expected"]
