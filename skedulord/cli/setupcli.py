import os
import uuid
import json
import logging
import pathlib
import subprocess
import datetime as dt

import yaml
import click

from skedulord.common import SETTINGS_PATH, CONFIG_PATH, HEARTBEAT_PATH


@click.group()
def main():
    pass


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--name', prompt='what is the name for this service')
def setup(name):
    settings = {"name": name}
    logger.info(f"creating new settings")
    path = pathlib.Path(SETTINGS_PATH)
    path.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(settings, f, default_flow_style=False)
    logger.info(f"settings file created: {CONFIG_PATH}")
    path = pathlib.Path(SETTINGS_PATH) / "logs"
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"paths created")
    logger.info(f"done")


@click.command()
@click.argument('command')
def log(command):
    run_id = str(uuid.uuid4())[:13]
    tic = dt.datetime.now()
    logger.info(f"about to run '{command}'")
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
    print(heartbeat)

    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")
    logger.info(f"heartbeat logged")

    pathlib.Path(log_folder).mkdir(parents=True, exist_ok=True)
    with open(heartbeat["log"], "w") as f:
        f.write(output.stdout)
    logger.info(f"log written at {heartbeat['log']}")
    logger.info(f"done with `{command}` with status code {output.returncode}")


main.add_command(setup)
main.add_command(log)

if __name__ == "__main__":
    main()
