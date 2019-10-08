import os
import time
import uuid
import shutil
import pathlib
import subprocess
import datetime as dt

import yaml
import click
import waitress

from skedulord import version
from skedulord.common import SKEDULORD_PATH, CONFIG_PATH, read_settings
from skedulord.logger import log_to_disk, logcli
from skedulord.web.app import create_app


SETTINGS = read_settings()


@click.group()
def main():
    pass


@click.command()
@click.option('--name', prompt='What is the name for this skedulord instance.')
@click.option('--attempts', prompt='What number of retries do you want to assume?', default=3)
@click.option('--wait', prompt='How many seconds between attemps do you assume?', default=60)
@click.option('--max-logs', prompt='Maximum number of logfiles to keep per jobname.', default=100)
@click.option('--email', prompt='Where to send an email apon failure.', default="")
def setup(name, attempts, wait, max_logs, email):
    """setup the skedulord"""
    settings = {"name": name, "version": version, "attempts": attempts,
                "wait": wait, "max_logs": max_logs, "email": email}
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
@click.option('--attempts', default=SETTINGS['attempts'], help='max number of tries')
@click.option('--wait', default=SETTINGS['wait'], help='seconds between tries')
def run(name, command, attempts, wait):
    """run (and log) the command, can retry"""
    tries = 0
    run_id = str(uuid.uuid4())[:8]
    tic = dt.datetime.now()

    log_folder = pathlib.Path(SKEDULORD_PATH) / "jobs" / name / "logs"
    log_file = str(tic)[:19].replace(" ", "T") + ".txt"
    pathlib.Path(log_folder).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(log_folder, log_file), "w") as f:
        while tries < attempts:
            f.write(f"{command} - {run_id} - attempt {tries + 1} - {str(dt.datetime.now())} \n")
            output = subprocess.run(command.split(" "),
                                    cwd=str(pathlib.Path().cwd()),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    encoding='utf-8',
                                    universal_newlines=True)

            f.write(output.stdout)
            if output.returncode == 0:
                tries += attempts
            else:
                logcli(f"detected failure, re-attempt in {wait} seconds")
                time.sleep(wait)
                tries += 1
    log_to_disk(run_id, name, command, tic=tic, toc=dt.datetime.now(), output=output)


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
def clean():
    """cleans local logs according to settings"""
    pass


main.add_command(setup)
main.add_command(run)
main.add_command(nuke)
main.add_command(serve)
main.add_command(clean)

if __name__ == "__main__":
    main()
