import shutil

import click
from rich import print
from rich.table import Table
from clumper import Clumper

from skedulord import __version__ as lord_version
from skedulord.job import JobRunner
from skedulord.common import SKEDULORD_PATH, heartbeat_path
from skedulord.cron import set_new_cron, clean_cron


@click.group()
def main():
    """
    SKEDULORD:
    keeps track of logs so you don't have to.
    """
    pass


@click.command()
def version():
    """confirm the version"""
    print(lord_version)


@click.command()
@click.argument("name")
@click.argument("command")
@click.option("--retry", default=1, help="max number of tries")
@click.option("--wait", default=60, help="seconds between tries")
def run(name, command, retry, wait):
    """run (and log) a command, can retry"""
    runner = JobRunner(retry=retry, wait=wait)
    runner.cmd(name=name, command=command)


@click.command()
@click.argument("config")
@click.option("--clean", default=False, is_flag=True)
def schedule(config, clean):
    """(re)schedule cron jobs"""
    if clean:
        clean_cron(config)
    else:
        set_new_cron(config)


@click.command()
@click.option("--yes", prompt=True, is_flag=True)
@click.option("--really", prompt=True, is_flag=True)
def clean(yes, really):
    """hard reset of disk state"""
    if yes and really:
        shutil.rmtree(SKEDULORD_PATH)
        print("Disk state has been cleaned.")
    else:
        print("Crisis averted.")


@click.command()
@click.option("--failures", default=False, is_flag=True, help="only show the failures")
@click.option(
    "--rows", "-r", default=None, type=int, help="maximum number of rows to show"
)
@click.option("--date", "-d", default=None, help="only show specific date")
@click.option("--jobname", "-j", default=None, help="only show specific jobname")
def history(rows, failures, date, jobname):
    """show historical log overview"""
    clump = Clumper.read_jsonl(heartbeat_path()).sort(lambda d: d["start"], reverse=True)
    if failures:
        clump = clump.keep(lambda d: d['status'] != 'success')
    if jobname:
        clump = clump.keep(lambda d: d['name'] != jobname)
    if date:
        clump = clump.keep(lambda d: d['start'][:10] != date)
    if rows:
        clump = clump.head(rows)
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


main.add_command(run)
main.add_command(clean)
main.add_command(version)
main.add_command(history)
main.add_command(schedule)

if __name__ == "__main__":
    main()
