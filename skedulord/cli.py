import os
import sys
import json
import shutil
import pathlib
import datetime as dt
from functools import wraps
from collections import Counter

import click
import waitress
from prettytable import PrettyTable

from skedulord import version as lord_version
from skedulord.logger import logcli
from skedulord.job import JobRunner
from skedulord.web.app import create_app
from skedulord.common import SKEDULORD_PATH, HEARTBEAT_PATH


def needs_init(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not os.path.exists(SKEDULORD_PATH):
            click.echo("You need to run `lord init` first.")
            return sys.exit(1)
        return f(*args, **kwargs)
    return wrapper


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
    click.echo(lord_version)


@click.command()
def init():
    """setup skedulord"""
    path = pathlib.Path(SKEDULORD_PATH)
    if os.path.exists(SKEDULORD_PATH):
        click.echo(f"{SKEDULORD_PATH} allready exists")
    else:
        path.mkdir(parents=True, exist_ok=True)
        (pathlib.Path(SKEDULORD_PATH) / 'heartbeat.jsonl').touch()


@click.command()
@click.argument('name')
@click.argument('command')
@click.option('--attempts', default=1, help='max number of tries')
@click.option('--wait', default=60, help='seconds between tries')
@needs_init
def run(name, command, attempts, wait):
    """run (and log) a command, can retry"""
    runner = JobRunner(attemps=attempts, wait=wait)
    runner.cmd(name=name, command=command)


@click.command()
@click.option('--sure', prompt=True, is_flag=True)
@click.option('--really', prompt=True, is_flag=True)
@needs_init
def nuke(sure, really):
    """hard reset of disk state"""
    if really and sure:
            shutil.rmtree(SKEDULORD_PATH)
            logcli("nuked from orbit!")
    else:
        logcli("crisis averted.")


@click.command()
@click.option('--host', '-h', default="0.0.0.0", help='host for the dashboard')
@click.option('--port', '-p', default=5000, help='port for the dashboard')
@needs_init
def serve(host, port):
    """start the simple dashboard"""
    app = create_app()
    waitress.serve(app, host=host, port=port)


@click.command()
@needs_init
def summary():
    """shows a summary of the logs"""
    def convert_dt(b):
        fmt = "%Y-%m-%d %H:%M:%S"
        d1, d2 = b['start'], b['end']
        return (dt.datetime.strptime(d1, fmt) - dt.datetime.strptime(d2, fmt)).total_seconds()

    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    tbl = PrettyTable()
    tbl.field_names = ["jobname", "runs", "fails", "duration"]

    for name, count in Counter([_['name'] for _ in jobs]).items():
        subset = [_ for _ in jobs if _['name'] == name]
        n_fail = sum([1 - _['succeed'] for _ in jobs if _['name'] == name])

        avg_time = sum(convert_dt(_) for _ in subset)/len(subset)
        tbl.add_row([name, count, n_fail, round(avg_time, 2)])
    click.echo(tbl)


@click.command()
@click.option('--rows', '-r', default=False, help='maximum number of rows to show')
@click.option('--failures', '-d', default=False, help='only show the failures')
@click.option('--date', '-d', default=None, help='only show specific date')
@click.option('--jobname', '-j', default=None, help='only show specific jobname')
@needs_init
def history(rows, failures, date, jobname):
    """show historical log overview"""
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    jobs = sorted(jobs, key=lambda d: d['start'], reverse=True)
    if failures:
        jobs = [j for j in jobs if not j['succeed']]
    if jobname:
        jobs = [j for j in jobs if not j['name'] == jobname]
    if date:
        jobs = [j for j in jobs if j['start'][:10] == date]
    if rows:
        jobs = jobs[:rows]
    tbl = PrettyTable()
    tbl.field_names = ["stat", "jobname", "logfile"]
    for j in jobs:
        tbl.add_row(['✅' if j['succeed'] else '❌', j["name"], j["log"], ])
    click.echo(tbl)


main.add_command(run)
main.add_command(init)
main.add_command(nuke)
main.add_command(serve)
main.add_command(version)
main.add_command(summary)
main.add_command(history)

if __name__ == "__main__":
    main()
