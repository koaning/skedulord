import shutil
from pathlib import Path

import typer
from rich import print
from rich.table import Table
from clumper import Clumper

from skedulord import __version__ as lord_version
from skedulord.job import JobRunner
from skedulord.common import SKEDULORD_PATH, heartbeat_path
from skedulord.cron import set_new_cron, clean_cron

app = typer.Typer(name="SKEDULORD", add_completion=False, help="SKEDULORD: helps with cronjobs and logs.")


@app.command()
def version():
    """Show the version."""
    print(lord_version)


@app.command()
def run(name: str = typer.Argument(..., help="The name you want to assign to the run."),
        command: str = typer.Argument(..., help="The command you want to run (in parentheses)."),
        retry: int = typer.Argument(..., help="The number of re-tries, should a job fail."),
        wait: int = typer.Argument(..., help="The number of seconds between tries.")):
    """Run a single command, which is logged by skedulord."""
    runner = JobRunner(retry=retry, wait=wait)
    runner.cmd(name=name, command=command)


@app.command()
def schedule(config: Path = typer.Argument(..., help="The config file containing the schedule.", exists=True)):
    """Set (or reset) cron jobs based on config."""
    set_new_cron(config)


@app.command()
def wipe(what: str = typer.Argument(..., help="What to wipe. Either `disk` or `schedule`."),
         yes: bool = typer.Option(..., is_flag=True, prompt=True, help="Are you sure?"),
         really: bool = typer.Option(..., is_flag=True, prompt=True, help="Really sure?")):
    """Wipe the disk or schedule state."""
    if yes and really:
        if what == "disk":
            shutil.rmtree(SKEDULORD_PATH)
            print("Disk state has been cleaned.")
        if what == "schedule":
            print("Not implemented.")
    else:
        print("Crisis averted.")


@app.command()
def history(n: int = typer.Option(10, help="How many rows should the table show."),
            only_failures: bool = typer.Option(..., is_flag=True, help="Only show failures."),
            date: str = typer.Option(..., is_flag=True, help="Only show specific date."),
            jobname: str = typer.Option(..., is_flag=True, help="Only show jobs with specific name.")):
    """Shows a table with job status."""
    clump = Clumper.read_jsonl(heartbeat_path()).sort(lambda _: _["start"], reverse=True)
    if only_failures:
        clump = clump.keep(lambda d: d['status'] != 'success')
    if jobname:
        clump = clump.keep(lambda d: d['name'] != jobname)
    if date:
        clump = clump.keep(lambda d: d['start'][:10] != date)
    if n:
        clump = clump.head(n)
    table = Table(title=None)
    table.add_column("status")
    table.add_column("date")
    table.add_column("name")
    table.add_column("logfile")
    for d in clump.collect():
        table.add_row(
                f"[{'red' if d['status'] == 'fail' else 'green'}]{d['status']}[/]",
                d["start"],
                d["name"],
                d["logpath"]
        )
    print(table)


if __name__ == "__main__":
    app()
