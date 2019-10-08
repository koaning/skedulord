import json
import os

import click

from skedulord.common import SKEDULORD_PATH, HEARTBEAT_PATH


class CliLogger():
    def __init__(self):
        self.i = 0
        self.lines = []

    def __call__(self, msg, color=None):
        self.i += 1
        if isinstance(msg, dict):
            for k, v in msg.items():
                click.echo(click.style(f"  - {k}: {v}", fg='green' if msg['status'] == 0 else 'red'))
        else:
            click.echo(click.style(f"{msg}", fg=color))


logcli = CliLogger()


def log_to_disk(run_id, name, command, tic, toc, output):
    log_folder = os.path.join(SKEDULORD_PATH, "logs", name.replace(" ", "-").replace(".", "-"))
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
    logcli(heartbeat)

    # we don't want the settings path in the flask server
    heartbeat['log'] = heartbeat['log'].replace(SKEDULORD_PATH, "")
    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")

    logcli(f"will be served over {heartbeat['log']}")