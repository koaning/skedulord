import json
import shutil
import pathlib
from collections import Counter

import yaml
import click
import waitress

from skedulord import version
from skedulord.logger import logcli
from skedulord.job import JobRunner
from skedulord.web.app import create_app
from skedulord.common import SKEDULORD_PATH, CONFIG_PATH, HEARTBEAT_PATH


@click.group()
def main():
    pass


@click.command()
@click.option('--name', prompt='What is the name for this skedulord instance.')
@click.option('--attempts', prompt='What number of retries do you want to assume?', default=3)
@click.option('--wait', prompt='How many seconds between attemps do you assume?', default=60)
def setup(name, attempts, wait):
    """setup skedulord"""
    settings = {"name": name, "version": version, "attempts": attempts, "wait": wait}
    logcli(f"creating new settings")
    path = pathlib.Path(SKEDULORD_PATH)
    path.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(settings, f, default_flow_style=False)
    logcli(f"settings file created: {CONFIG_PATH}")
    path = pathlib.Path(SKEDULORD_PATH) / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    logcli(f"paths created")
    logcli(f"done")


@click.command()
@click.argument('name')
@click.argument('command')
@click.option('--attempts', default=3, help='max number of tries')
@click.option('--wait', default=60, help='seconds between tries')
def run(name, command, attempts, wait):
    """run (and log) the command, can retry"""
    runner = JobRunner(attemps=attempts, wait=wait)
    runner.cmd(name=name, command=command)


@click.command()
@click.option('--sure', prompt=True, is_flag=True)
@click.option('--really', prompt=True, is_flag=True)
def nuke(sure, really):
    """hard reset of disk state"""
    if really and sure:
        try:
            shutil.rmtree(SKEDULORD_PATH)
            logcli("nuked from orbit!")
        except FileNotFoundError:
            logcli("no skedulord files found")


@click.command()
@click.option('--host', '-h', default="0.0.0.0", help='host for the dashboard')
@click.option('--port', '-p', default=5000, help='port for the dashboard')
def serve(host, port):
    """start the simple dashboard"""
    app = create_app()
    waitress.serve(app, host=host, port=port)


@click.command()
def summary():
    """shows a summary of the logs"""
    with open(HEARTBEAT_PATH, "r") as f:
        jobs = [json.loads(_) for _ in f.readlines()]
    name, count, n_fail, time = 'name', 'total', 'n_fail', 'avg seconds'
    click.echo(f"{name:>10} {count:>5} {n_fail:>6} {time:>11}")
    for name, count in Counter([_['name'] for _ in jobs]).items():
        subset = [_ for _ in jobs if _['name'] == name]
        n_fail = sum([1 - _['status'] for _ in jobs if _['name'] == name])
        avg_time = sum(_['time'] for _ in subset)/len(subset)
        click.echo(f"{name:>10} {count:>5} {n_fail:>6} {avg_time:>11}")


main.add_command(setup)
main.add_command(run)
main.add_command(nuke)
main.add_command(serve)
main.add_command(summary)

if __name__ == "__main__":
    main()
