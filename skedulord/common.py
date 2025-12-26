import os
import json
import pathlib

SKEDULORD_PATH = os.path.join(os.path.expanduser("~/.skedulord"))
SKEDULORD_DB_PATH = os.path.join(SKEDULORD_PATH, "skedulord.db")


def skedulord_path() -> pathlib.Path:
    path = pathlib.Path(SKEDULORD_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> pathlib.Path:
    skedulord_path()
    return pathlib.Path(SKEDULORD_DB_PATH)


def job_name_path(jobname) -> str:
    return skedulord_path() / jobname


def heartbeat_path() -> pathlib.Path:
    return skedulord_path() / "heartbeat.jsonl"


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
