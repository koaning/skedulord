import os
import uuid
import json
import shutil
import pathlib
import subprocess
import datetime as dt

import yaml
import click

from skedulord.common import SETTINGS_PATH, CONFIG_PATH, HEARTBEAT_PATH


class Logga():
    def __init__(self):
        self.i = 0

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


@click.command()
@click.argument('command')
def log(command):
    """log the (cron) command"""
    run_id = str(uuid.uuid4())[:13]
    tic = dt.datetime.now()
    output = subprocess.run(command.split(" "),
                            cwd=str(pathlib.Path().cwd()),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            encoding='utf-8',
                            universal_newlines=True)
    toc = dt.datetime.now()
    log_folder = os.path.join(SETTINGS_PATH, command.replace(" ", "-").replace(".", "-"))
    log_file = str(tic)[:19].replace(" ", "T") + ".txt"
    heartbeat = {
        "id": run_id,
        "command": command,
        "startime": str(tic)[:19],
        "endtime": str(toc)[:19],
        "time": (toc - tic).seconds,
        "status": output.returncode,
        "log": os.path.join(log_folder, log_file)
    }

    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")

    pathlib.Path(log_folder).mkdir(parents=True, exist_ok=True)
    with open(heartbeat["log"], "w") as f:
        f.write(output.stdout)
    logg(f"log written at {heartbeat['log']}")
    logg(heartbeat)


@click.command()
def nuke():
    """hard reset of disk state"""
    if click.confirm('Do you want to continue?'):
        shutil.rmtree(SETTINGS_PATH)
        logg("nuked from orbit!")
    else:
        logg("safely aborted!")


main.add_command(setup)
main.add_command(log)
main.add_command(nuke)

if __name__ == "__main__":
    main()
