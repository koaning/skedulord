import shutil
import subprocess
import webbrowser
from pathlib import Path

import typer
from rich import print
from rich.table import Table
from clumper import Clumper

from skedulord import __version__ as lord_version
from skedulord.job import JobRunner
from skedulord.common import SKEDULORD_PATH, heartbeat_path
from skedulord.cron import Cron, clean_cron
from skedulord.dashboard import Dashboard

app = typer.Typer(
    name="SKEDULORD",
    add_completion=False,
    help="SKEDULORD: helps with cronjobs and logs.",
)


@app.command()
def version():
    """Show the version."""
    print(lord_version)


@app.command()
def run(
    name: str = typer.Argument(..., help="The name you want to assign to the run."),
    command: str = typer.Argument(
        ..., help="The command you want to run (in parentheses)."
    ),
    retry: int = typer.Option(1, help="The number of re-tries, should a job fail."),
    wait: int = typer.Option(60, help="The number of seconds between tries."),
):
    """Run a single command, which is logged by skedulord."""
    runner = JobRunner(retry=retry, wait=wait)
    runner.cmd(name=name, command=command)


@app.command()
def schedule(
    config: Path = typer.Argument(
        ..., help="The config file containing the schedule.", exists=True
    )
):
    """Set (or reset) cron jobs based on config."""
    Cron(config).set_new_cron()


@app.command()
def wipe(
    what: str = typer.Argument(..., help="What to wipe. Either `disk` or `schedule`."),
    yes: bool = typer.Option(False, is_flag=True, prompt=True, help="Are you sure?"),
    really: bool = typer.Option(False, is_flag=True, prompt=True, help="Really sure?"),
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
    only_failures: bool = typer.Option(False, is_flag=True, help="Only show failures."),
    date: str = typer.Option(None, is_flag=True, help="Only show specific date."),
    jobname: str = typer.Option(
        None, is_flag=True, help="Only show jobs with specific name."
    ),
):
    """Shows a table with job status."""
    clump = Clumper.read_jsonl(heartbeat_path()).sort(
        lambda _: _["start"], reverse=True
    )
    if only_failures:
        clump = clump.keep(lambda _: _["status"] != "success")
    if jobname:
        clump = clump.keep(lambda _: jobname in _["name"])
    if date:
        clump = clump.keep(lambda _: date in _["start"])
    table = Table(title=None)
    table.add_column("status")
    table.add_column("date")
    table.add_column("name")
    table.add_column("logfile")
    for d in clump.head(n).collect():
        table.add_row(
            f"[{'red' if d['status'] == 'fail' else 'green'}]{d['status']}[/]",
            d["start"],
            d["name"],
            d["logpath"],
        )
    print(table)


@app.command(name="build")
def build_site():
    """
    Builds static html files so you may view a dashboard.
    """
    data = Clumper.read_jsonl(heartbeat_path()).collect()
    Dashboard(data).build()


@app.command()
def serve(
    build: bool = typer.Option(
        True, is_flag=True, help="Build the dashboard before opening it."
    )
):
    """
    Opens the dashboard in a browser.
    """
    if build:
        build_site()
    webbrowser.open_new_tab(f"file://{heartbeat_path().parent / 'index.html'}")


if __name__ == "__main__":
    app()
