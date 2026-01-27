import getpass
import shutil
import subprocess
from pathlib import Path
from typing import Union

import typer
import yaml
from rich import print
from rich.table import Table
from clumper import Clumper

from skedulord import __version__ as lord_version
from skedulord.auth import hash_password
from skedulord.job import JobRunner
from skedulord.common import SKEDULORD_PATH
from skedulord.cron import Cron, clean_cron, parse_job_from_settings
from skedulord.db import (
    delete_user,
    fetch_runs,
    fetch_user,
    init_db,
    insert_user,
    update_user_password,
)
from skedulord.dashboard import export_static_site
from skedulord.templating import render_tokens
from skedulord.api import create_app

app = typer.Typer(
    name="SKEDULORD",
    add_completion=False,
    help="SKEDULORD: helps with cronjobs and logs.",
    invoke_without_command=True,
)

users_app = typer.Typer(help="Manage users for the API/dashboard.")
app.add_typer(users_app, name="users")


@users_app.command("add")
def add_user(
    username: str = typer.Option(..., "--username", help="Username to add."),
    password: str = typer.Option(
        None,
        "--password",
        help="Password for the user (prompted if omitted).",
    ),
):
    """Create a new user."""
    if fetch_user(username):
        print(f"[red]User '{username}' already exists.[/]")
        raise typer.Exit(code=1)
    if password is None:
        password = typer.prompt(
            "Password",
            hide_input=True,
            confirmation_prompt=True,
        )
    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    if not insert_user(username, password_hash):
        print(f"[red]User '{username}' already exists.[/]")
        raise typer.Exit(code=1)
    print(f"[green]User '{username}' added.[/]")


@users_app.command("update")
def update_user(
    username: str = typer.Option(..., "--username", help="Username to update."),
    password: str = typer.Option(
        None,
        "--password",
        help="New password (prompted if omitted).",
    ),
):
    """Update an existing user's password."""
    if not fetch_user(username):
        print(f"[red]User '{username}' does not exist.[/]")
        raise typer.Exit(code=1)
    if password is None:
        password = typer.prompt(
            "Password",
            hide_input=True,
            confirmation_prompt=True,
        )
    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    if not update_user_password(username, password_hash):
        print(f"[red]User '{username}' does not exist.[/]")
        raise typer.Exit(code=1)
    print(f"[green]User '{username}' updated.[/]")


@users_app.command("remove")
def remove_user(
    username: str = typer.Option(..., "--username", help="Username to remove."),
):
    """Remove an existing user."""
    if not delete_user(username):
        print(f"[red]User '{username}' does not exist.[/]")
        raise typer.Exit(code=1)
    print(f"[green]User '{username}' removed.[/]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show help if no command is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def version():
    """Show the version."""
    print(lord_version)


@app.command()
def init(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Directory to write .env and schedule.yml.",
    ),
    force: bool = typer.Option(False, help="Overwrite existing files."),
):
    """Initialize .env, schedule.yml, and sqlite."""
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)

    user = getpass.getuser()
    env_path = path / ".env"
    schedule_path = path / "schedule.yml"
    script_path = path / "example_job.py"
    targets = [env_path, schedule_path, script_path]

    if not force:
        existing = [target for target in targets if target.exists()]
        if existing:
            print("[yellow]Skipped init because files already exist:[/]")
            for target in existing:
                print(f"[yellow]- {target}[/]")
            print("[yellow]Re-run with --force to overwrite.[/]")
            raise typer.Exit(code=1)

    env_contents = "\n".join(
        [
            "# Skedulord environment (edit as needed).",
            "SKEDULORD_NO_AUTH=0",
            "SKEDULORD_EXAMPLE_MESSAGE=hello from skedulord",
            "",
        ]
    )

    schedule_contents = "\n".join(
        [
            "user: " + user,
            "schedule:",
            "  - name: example",
            f"    command: {script_path}",
            "    cron: \"*/5 * * * *\"",
            "",
        ]
    )

    script_contents = "\n".join(
        [
            "#!/usr/bin/env -S uv run python",
            "# /// script",
            "# dependencies = [\"python-dotenv\"]",
            "# ///",
            "from __future__ import annotations",
            "",
            "from pathlib import Path",
            "import os",
            "",
            "from dotenv import load_dotenv",
            "",
            "env_path = Path(__file__).with_name(\".env\")",
            "load_dotenv(env_path)",
            "",
            "message = os.getenv(\"SKEDULORD_EXAMPLE_MESSAGE\", \"hello from skedulord\")",
            "print(message)",
            "",
        ]
    )

    for target, contents, label in [
        (env_path, env_contents, ".env"),
        (schedule_path, schedule_contents, "schedule.yml"),
        (script_path, script_contents, "example_job.py"),
    ]:
        target.write_text(contents, encoding="utf8")
        print(f"[green]Wrote {label} to {target}.[/]")

    init_db()
    print(f"[green]Initialized sqlite database at {Path(SKEDULORD_PATH) / 'skedulord.db'}.[/]")


@app.command()
def run(
    name: str = typer.Argument(..., help="The name you want to assign to the run."),
    command: str = typer.Argument(
        None, help="The command you want to run (in parentheses)."
    ),
    settings_path: Union[Path, None] = typer.Option(None, help="Schedule config to reference."),
    retry: Union[int, None] = typer.Option(None, help="The number of tries, should a job fail."),
    wait: Union[int, None] = typer.Option(None, help="The number of seconds between tries."),
):
    """Run a single command, which is logged by skedulord."""
    if settings_path:
        settings = Clumper.read_yaml(settings_path).unpack("schedule").keep(lambda d: d['name'] == name).collect()
        parsed = parse_job_from_settings(settings, name)
        command = parsed["command"]
        retry = parsed["retry"] if retry is None else retry
        wait = parsed["wait"] if wait is None else wait
    if not command:
        raise typer.Exit(code=1)
    command = render_tokens(command)
    JobRunner(retry=retry or 2, wait=wait or 60, name=name, cmd=command).run()


@app.command()
def schedule(
    config: Path = typer.Argument(
        Path("schedule.yml"), help="The config file containing the schedule."
    )
):
    """Set (or reset) cron jobs based on config."""
    config = config.expanduser().resolve()
    if not config.exists():
        print(f"[red]Config file not found: {config}[/]")
        raise typer.Exit(code=1)
    Cron(config).set_new_cron()


@app.command()
def add(
    file: Path = typer.Argument(..., help="The file/command to schedule."),
    cron: str = typer.Option(..., "--cron", "-c", help="Cron expression (e.g. '0 * * * *')."),
    name: str = typer.Option(None, "--name", "-n", help="Job name (defaults to filename)."),
    config: Path = typer.Option(
        Path("schedule.yml"),
        "--config",
        "-f",
        help="Path to schedule.yml file.",
    ),
    update_schedule: bool = typer.Option(
        True,
        "--schedule/--no-schedule",
        "-s",
        help="Update crontab after adding job.",
    ),
):
    """Add a job to the schedule config file."""
    file = file.expanduser().resolve()
    config = config.expanduser().resolve()

    if not file.exists():
        print(f"[red]File not found: {file}[/]")
        raise typer.Exit(code=1)

    if not config.exists():
        print(f"[red]Config file not found: {config}[/]")
        print("[yellow]Run 'skedulord init' first or specify a config file with --config.[/]")
        raise typer.Exit(code=1)

    job_name = name if name else file.stem.replace("_", "-").replace(" ", "-")

    with open(config) as f:
        data = yaml.safe_load(f)

    existing_names = [job["name"] for job in data.get("schedule", [])]
    if job_name in existing_names:
        print(f"[red]Job '{job_name}' already exists in {config}.[/]")
        raise typer.Exit(code=1)

    new_job = {
        "name": job_name,
        "command": str(file),
        "cron": cron,
    }
    data["schedule"].append(new_job)

    with open(config, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"[green]Added job '{job_name}' to {config}.[/]")

    if update_schedule:
        Cron(config).set_new_cron()
        print("[green]Crontab updated.[/]")


@app.command()
def rm(
    name: str = typer.Argument(..., help="The job name to remove."),
    config: Path = typer.Option(
        Path("schedule.yml"),
        "--config",
        "-f",
        help="Path to schedule.yml file.",
    ),
    update_schedule: bool = typer.Option(
        True,
        "--schedule/--no-schedule",
        "-s",
        help="Update crontab after removing job.",
    ),
):
    """Remove a job from the schedule config file."""
    config = config.expanduser().resolve()

    if not config.exists():
        print(f"[red]Config file not found: {config}[/]")
        raise typer.Exit(code=1)

    with open(config) as f:
        data = yaml.safe_load(f)

    existing_names = [job["name"] for job in data.get("schedule", [])]
    if name not in existing_names:
        print(f"[red]Job '{name}' not found in {config}.[/]")
        raise typer.Exit(code=1)

    data["schedule"] = [job for job in data["schedule"] if job["name"] != name]

    with open(config, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"[green]Removed job '{name}' from {config}.[/]")

    if update_schedule:
        Cron(config).set_new_cron()
        print("[green]Crontab updated.[/]")


@app.command()
def wipe(
    what: str = typer.Argument(..., help="What to wipe. Either `disk` or `schedule`."),
    yes: bool = typer.Option(False, prompt=True, help="Are you sure?"),
    really: bool = typer.Option(False, prompt=True, help="Really sure?"),
    user: str = typer.Option(None, help="The name of the user. Default: curent user."),
):
    """Wipe the disk or schedule state."""
    if yes and really:
        if what == "disk":
            if Path(SKEDULORD_PATH).exists():
                shutil.rmtree(SKEDULORD_PATH)
                print("Disk state has been cleaned.")
        if what == "schedule":
            if not user:
                name = subprocess.run(["whoami"], stdout=subprocess.PIPE)
                user = name.stdout.decode("utf8").strip()
            clean_cron(user=user)
            print("Cron state has been cleaned.")
    else:
        print("Crisis averted.")


@app.command()
def history(
    n: int = typer.Option(10, help="How many rows should the table show."),
    only_failures: bool = typer.Option(False, help="Only show failures."),
    date: str = typer.Option(None, help="Only show specific date."),
    name: str = typer.Option(None, "--name", "--jobname", help="Only show jobs with specific name."),
):
    """Shows a table with job status."""
    status = "fail" if only_failures else None
    rows = list(fetch_runs(limit=n, name=name, status=status, date=date))
    if not rows:
        print("No runs found.")
        raise typer.Exit(code=1)
    table = Table(title=None)
    table.add_column("status")
    table.add_column("date")
    table.add_column("name")
    table.add_column("logfile")
    for d in rows:
        table.add_row(
            f"[{'red' if d['status'] == 'fail' else 'green'}]{d['status']}[/]",
            d["start"],
            d["name"],
            d["logpath"],
        )
    print(table)


@app.command()
def export(
    output: Path = typer.Option(
        Path(".") / "skedulord-export",
        "--output",
        "-o",
        help="Output directory for the static site.",
    ),
):
    """Export dashboard to a static site."""
    output = output.expanduser().resolve()
    print(f"Exporting static site to [green]{output}[/]...")
    count = export_static_site(output)
    print(f"[green]Exported {count} runs to {output}[/]")
    print(f"[dim]Serve with: python -m http.server -d {output}[/]")


@app.command(name="serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="The host to bind."),
    port: int = typer.Option(8000, help="The port number to use."),
    reload: bool = typer.Option(False, help="Enable auto-reload."),
    no_auth: bool = typer.Option(
        False,
        "--no-auth",
        hidden=True,
        help="Disable authentication for local testing.",
    ),
    ):
    """
    Serves the skedulord API.
    """
    import socket
    import uvicorn

    desired_port = port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except OSError:
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        typer.echo(
            f"Port {desired_port} is in use, switching to http://{host}:{port}"
        )
    finally:
        sock.close()

    if no_auth and reload:
        typer.echo("Disabling reload because --no-auth requires an in-memory app instance.")
        reload = False

    if reload:
        uvicorn.run("skedulord.api:app", host=host, port=port, reload=True)
        return

    app = create_app(no_auth=no_auth)
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
