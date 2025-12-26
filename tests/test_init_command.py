from pathlib import Path

from typer.testing import CliRunner

from skedulord.__main__ import app


def test_init_creates_files_and_db(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".env").exists()
    assert (tmp_path / "schedule.yml").exists()
    assert (tmp_path / "example_job.py").exists()
    assert (Path.home() / ".skedulord" / "skedulord.db").exists()


def test_init_refuses_when_files_exist(tmp_path):
    (tmp_path / ".env").write_text("SKEDULORD_NO_AUTH=0\n", encoding="utf8")
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code != 0
    assert "Skipped init because files already exist" in result.output


def test_init_force_overwrites(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("OLD=1\n", encoding="utf8")
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--force"])
    assert result.exit_code == 0
    assert "OLD=1" not in env_path.read_text(encoding="utf8")
