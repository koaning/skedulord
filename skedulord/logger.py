import os
import json
import pathlib

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
                click.echo(click.style(f"  - {k}: {v}", fg='green' if msg['succeed'] else 'red'))
        else:
            click.echo(click.style(f"{msg}", fg=color))


logcli = CliLogger()


def joblog_path(jobname, tic):
    log_folder = pathlib.Path(SKEDULORD_PATH) / "jobs" / jobname
    log_file = str(tic)[:19].replace(" ", "T") + ".txt"
    pathlib.Path(log_folder).mkdir(parents=True, exist_ok=True)
    return os.path.join(log_folder, log_file)


def log_output(jobname, tic, output):
    with open(joblog_path(jobname, tic), "w") as f:
        f.write(output)


def log_to_disk(run_id, name, command, tic, toc, succeed, output, tries, silent=False):
    heartbeat = {
        "id": run_id,
        "name": name,
        "tries": tries,
        "command": command,
        "start": str(tic)[:19],
        "end": str(toc)[:19],
        "succeed": succeed,
        "log": joblog_path(jobname=name, tic=tic)
    }
    if not silent:
        logcli(heartbeat)

    # we don't want the settings path in the flask server
    heartbeat['log'] = heartbeat['log'].replace(SKEDULORD_PATH, "")
    # first we log the logfile that belongs to the job
    log_output(jobname=name, tic=tic, output=output)
    # then we wrap up by logging the heartbeat to disk
    with open(HEARTBEAT_PATH, "a") as f:
        f.write(json.dumps(heartbeat) + "\n")
