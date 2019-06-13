import os
import time
import uuid
import json
import shutil
import pathlib
import subprocess
import datetime as dt

import yaml
import click
import waitress

from skedulord.common import SETTINGS_PATH, CONFIG_PATH, HEARTBEAT_PATH
from skedulord.web.app import create_app


class Logga():
    def __init__(self):
        self.i = 0
        self.lines = []

    def __call__(self, msg):
        self.i += 1
        if isinstance(msg, dict):
            for k, v in msg.items():
                click.echo(click.style(f"  - {k}: {v}", fg='green' if msg['status'] == 0 else 'red'))
        else:
            click.echo(click.style(f"{msg}"))


logg = Logga()


@click.group()
def main():
    pass


@click.command()
@click.option('--name', prompt='what is the name for this service')
def setup(name):
    """setup the skedulord"""
    settings = {"name": name}
    logg(f"creating new settings")
    path = pathlib.Path(SETTINGS_PATH)
    path.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(settings, f, default_flow_style=False)
    logg(f"settings file created: {CONFIG_PATH}")
    path = pathlib.Path(SETTINGS_PATH) / "logs"
    path.mkdir(parents=True, exist_ok=True)
    logg(f"paths created")
    logg(f"done")


def add_heartbeat(run_id, command, tic, toc, output):
    log_folder = os.path.join(SETTINGS_PATH, "logs", command.replace(" ", "-").replace(".", "-"))
    log_file = str(tic)[:19].replace(" ", "T") + ".txt"
    heartbeat = {
        "id": run_id,
        "command": command,
        "startime": str(tic)[:19],
        "endtime": str(toc)[:19],
        "time": (toc - tic).seconds,
        "status": output.returncode,
        "log": os.path.join(log_folder, log_file).replace(SETTINGS_PATH, "")
    }

    logg(heartbeat)
    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")
    logg(f"log written at {heartbeat['log']}")


@click.command()
@click.argument('command')
@click.option('--attempts', default=1, help='max number of tries')
@click.option('--wait', default=30, help='seconds between tries')
def run(command, attempts, wait):
    """run (and log) the (cron) command, can retry"""
    tries = 0
    run_id = str(uuid.uuid4())[:13]
    tic = dt.datetime.now()
    log_folder = os.path.join(SETTINGS_PATH, "logs", command.replace(" ", "-").replace(".", "-"))
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
                logg(f"detected failure, re-attempt in {wait} seconds")
                time.sleep(wait)
                tries += 1
    add_heartbeat(run_id, command, tic=tic, toc=dt.datetime.now(), output=output)



@click.command()
def nuke():
    """hard reset of disk state"""
    if click.confirm('Do you want to continue?'):
        shutil.rmtree(SETTINGS_PATH)
        logg("nuked from orbit!")
    else:
        logg("safely aborted!")


@click.command()
@click.option('--host', '-h', default="0.0.0.0", help='host for the dashboard')
@click.option('--port', '-p', default=5000, help='port for the dashboard')
def serve(host, port):
    """start the simple dashboard"""
    app = create_app()
    waitress.serve(app, host=host, port=port)


main.add_command(setup)
main.add_command(run)
main.add_command(nuke)
main.add_command(serve)

if __name__ == "__main__":
    main()
