import os
import json

import pytest
from click.testing import CliRunner


from skedulord.__main__ import history
from skedulord.logger import log_to_disk


@pytest.fixture()
def clean_start_small():
    os.system("lord nuke --really --yes")
    os.system("lord init")
    for date in ["2019-01-01", "2019-01-02"]:
        log_to_disk(run_id="a", name="goodjob", command="cmd",
                    tic=f"{date} 00:00:00", toc=f"{date} 00:00:00",
                    succeed=True, tries=1, silent=True, output="yes")
    for date in ["2019-01-01", "2019-01-02", "2019-01-03"]:
        log_to_disk(run_id="a", name="badjob", command="fail",
                    tic=f"{date} 00:00:00", toc=f"{date} 00:00:00",
                    succeed=False, tries=1, silent=True, output="no")
    yield 1
    os.system("lord nuke --really --yes")


def test_history_failures(clean_start_small):
    result = CliRunner().invoke(history, ["--failures"])
    assert len(result.output.split("\n")) == 8


def test_history_date(clean_start_small):
    result = CliRunner().invoke(history, ["--date", "2019-01-01"])
    assert len(result.output.split("\n")) == 7
    result = CliRunner().invoke(history, ["--date", "2019-01-02"])
    assert len(result.output.split("\n")) == 7
    result = CliRunner().invoke(history, ["--date", "2019-01-03"])
    assert len(result.output.split("\n")) == 6


def test_history_name(clean_start_small):
    result = CliRunner().invoke(history, ["--jobname", "goodjob"])
    assert len(result.output.split("\n")) == 7
    result = CliRunner().invoke(history, ["--jobname", "badjob"])
    assert len(result.output.split("\n")) == 8


def test_history_rows(clean_start_small):
    result = CliRunner().invoke(history, ["--rows", "20"])
    print(result.output)
    assert len(result.output.split("\n")) == 10
    result = CliRunner().invoke(history, ["--rows", "10"])
    assert len(result.output.split("\n")) == 10
    result = CliRunner().invoke(history, ["--rows", "2"])
    assert len(result.output.split("\n")) == 7
    result = CliRunner().invoke(history, ["--rows", "1"])
    assert len(result.output.split("\n")) == 6
