import os

import yaml

SETTINGS_PATH = os.path.join(os.path.expanduser("~/.skedulord"))
CONFIG_PATH = os.path.join(SETTINGS_PATH, "config.yml")
HEARTBEAT_PATH = os.path.join(SETTINGS_PATH, "heartbeat.csv")


def read_settings():
    settings_path = os.path.join(os.path.expanduser("~/.skedulord"), "config.yml")
    with open(settings_path, "r") as f:
        res = yaml.safe_load(f)
    return res
