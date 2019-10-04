import os
import json

import yaml
import click

SETTINGS_PATH = os.path.join(os.path.expanduser("~/.skedulord"))
CONFIG_PATH = os.path.join(SETTINGS_PATH, "config.yml")
HEARTBEAT_PATH = os.path.join(SETTINGS_PATH, "heartbeat.jsonl")


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


def read_settings():
    settings_path = os.path.join(os.path.expanduser("~/.skedulord"), "config.yml")
    try:
        with open(settings_path, "r") as f:
            res = yaml.safe_load(f)
        return res
    except FileNotFoundError:
        logg("no instance of skedulord detected")
        return {"attempts": 3, "wait": 10}


def add_heartbeat(run_id, name, command, tic, toc, output):
    log_folder = os.path.join(SETTINGS_PATH, "logs", command.replace(" ", "-").replace(".", "-"))
    log_file = str(tic)[:19].replace(" ", "T") + ".txt"
    heartbeat = {
        "id": run_id,
        "name": name,
        "command": command,
        "startime": str(tic)[:19],
        "endtime": str(toc)[:19],
        "time": (toc - tic).seconds,
        "status": output.returncode,
        "log": os.path.join(log_folder, log_file)
    }
    logg(heartbeat)

    # we don't want the settings path in the flask server
    heartbeat['log'] = heartbeat['log'].replace(SETTINGS_PATH, "")
    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")

    logg(f"will be served over {heartbeat['log']}")
