import os

import yaml


SKEDULORD_PATH = os.path.join(os.path.expanduser("~/.skedulord"))
CONFIG_PATH = os.path.join(SKEDULORD_PATH, "config.yml")
HEARTBEAT_PATH = os.path.join(SKEDULORD_PATH, "heartbeat.jsonl")

BASE_ATTEMPTS_VALUE = 3
BASE_WAIT_VALUE = 60


def read_settings(settings_path=None):
    if not settings_path:
        settings_path = os.path.join(os.path.expanduser("~/.skedulord"), "config.yml")
    try:
        with open(settings_path, "r") as f:
            res = yaml.safe_load(f)
        return res
    except FileNotFoundError:
        print("no instance of skedulord detected")
        return {"attempts": BASE_ATTEMPTS_VALUE,
                "wait": BASE_WAIT_VALUE}
