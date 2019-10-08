import os
from functools import reduce


import yaml
from skedulord.logger import CliLogger

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
        logcli("no instance of skedulord detected")
        return {"attempts": BASE_ATTEMPTS_VALUE,
                "wait": BASE_WAIT_VALUE}


def consolidate_settings(*filepaths):
    """Give it filepaths, it outputs a single dictionary."""
    return reduce(lambda a, b: a.update(b), [read_settings(f) for f in filepaths])


def run_cmd(func, *config_files, **kwargs):
    configs = reduce(lambda a, b: a.update(b), [read_settings(f) for f in config_files])
    settings = configs.update(kwargs)
    return func(**settings)


def run_func(func, *config_files, **kwargs):
    configs = reduce(lambda a, b: a.update(b), [read_settings(f) for f in config_files])
    settings = configs.update(kwargs)
    return func(**settings)


