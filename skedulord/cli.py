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
from skedulord.common import SETTINGS_PATH, CONFIG_PATH, read_settings, logg, add_heartbeat
from skedulord.web.app import create_app


SETTINGS = read_settings()


@click.group()
def main():
    pass


@click.command()
@click.option('--name', prompt='What is the name for this skedulord instance.')
@click.option('--attempts', prompt='What number of retries do you want to assume?', default=3)
@click.option('--wait', prompt='How many seconds between attemps do you assume?', default=60)
def setup(name, attempts, wait):
    """setup the skedulord"""
    settings = {"name": name, "version": version, "attempts": attempts, "wait": wait}
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
@click.option('--name', default="", help='give this job a name')
@click.option('--attempts', default=SETTINGS['attempts'], help='max number of tries')
@click.option('--wait', default=SETTINGS['wait'], help='seconds between tries')
def run(command, name, attempts, wait):
    """run (and log) the (cron) command, can retry"""
    tries = 0
    name = command if name == "" else name
    attempts = attempts
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
    add_heartbeat(run_id, name, command, tic=tic, toc=dt.datetime.now(), output=output)


@click.command()
def nuke():
    """hard reset of disk state"""
    if click.confirm('Do you want to continue?'):
        if click.confirm('Are you **really** sure?'):
            try:
                shutil.rmtree(SETTINGS_PATH)
                logg("nuked from orbit!")
            except FileNotFoundError:
                logg("no skedulord files found")
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
