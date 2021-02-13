import os
import json
import pathlib

SKEDULORD_PATH = os.path.join(os.path.expanduser("~/.skedulord"))


def job_name_path(jobname):
    return pathlib.Path(SKEDULORD_PATH) / jobname


def heartbeat_path():
    return pathlib.Path(SKEDULORD_PATH) / "heartbeat.jsonl"


def log_heartbeat(run_id, name, command, tic, toc, status, logpath):
    heartbeat = {
        "id": run_id,
        "name": name,
        "command": command,
        "start": str(tic)[:19],
        "end": str(toc)[:19],
        "status": status,
        "logpath": logpath,
    }

    with open(heartbeat_path(), "a") as f:
        f.write(json.dumps(heartbeat) + "\n")
