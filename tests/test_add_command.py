import yaml
from typer.testing import CliRunner

from skedulord.__main__ import app


def test_add_job_to_schedule(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text("user: testuser\nschedule: []\n", encoding="utf8")
    script_path = tmp_path / "my_script.py"
    script_path.write_text("print('hello')\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", str(script_path), "--cron", "0 * * * *", "--config", str(schedule_path), "--no-schedule"],
    )

    assert result.exit_code == 0
    assert "Added job 'my-script'" in result.output

    data = yaml.safe_load(schedule_path.read_text(encoding="utf8"))
    assert len(data["schedule"]) == 1
    assert data["schedule"][0]["name"] == "my-script"
    assert data["schedule"][0]["command"] == str(script_path)
    assert data["schedule"][0]["cron"] == "0 * * * *"


def test_add_with_custom_name(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text("user: testuser\nschedule: []\n", encoding="utf8")
    script_path = tmp_path / "script.py"
    script_path.write_text("print('hello')\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", str(script_path), "--cron", "*/5 * * * *", "--name", "my-custom-job", "--config", str(schedule_path), "--no-schedule"],
    )

    assert result.exit_code == 0
    assert "Added job 'my-custom-job'" in result.output

    data = yaml.safe_load(schedule_path.read_text(encoding="utf8"))
    assert data["schedule"][0]["name"] == "my-custom-job"


def test_add_fails_when_file_not_found(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text("user: testuser\nschedule: []\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", str(tmp_path / "nonexistent.py"), "--cron", "0 * * * *", "--config", str(schedule_path)],
    )

    assert result.exit_code != 0
    assert "File not found" in result.output


def test_add_fails_when_config_not_found(tmp_path):
    script_path = tmp_path / "script.py"
    script_path.write_text("print('hello')\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", str(script_path), "--cron", "0 * * * *", "--config", str(tmp_path / "missing.yml")],
    )

    assert result.exit_code != 0
    assert "Config file not found" in result.output


def test_add_fails_when_job_name_exists(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text(
        "user: testuser\nschedule:\n  - name: my-script\n    command: /old/path\n    cron: '0 0 * * *'\n",
        encoding="utf8",
    )
    script_path = tmp_path / "my_script.py"
    script_path.write_text("print('hello')\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["add", str(script_path), "--cron", "0 * * * *", "--config", str(schedule_path)],
    )

    assert result.exit_code != 0
    assert "already exists" in result.output


def test_rm_job_from_schedule(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text(
        "user: testuser\nschedule:\n  - name: my-job\n    command: /path/to/script.py\n    cron: '0 * * * *'\n",
        encoding="utf8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["rm", "my-job", "--config", str(schedule_path), "--no-schedule"],
    )

    assert result.exit_code == 0
    assert "Removed job 'my-job'" in result.output

    data = yaml.safe_load(schedule_path.read_text(encoding="utf8"))
    assert len(data["schedule"]) == 0


def test_rm_fails_when_job_not_found(tmp_path):
    schedule_path = tmp_path / "schedule.yml"
    schedule_path.write_text("user: testuser\nschedule: []\n", encoding="utf8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["rm", "nonexistent-job", "--config", str(schedule_path)],
    )

    assert result.exit_code != 0
    assert "not found" in result.output


def test_rm_fails_when_config_not_found(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["rm", "some-job", "--config", str(tmp_path / "missing.yml")],
    )

    assert result.exit_code != 0
    assert "Config file not found" in result.output
