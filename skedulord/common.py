import os

SKEDULORD_PATH = os.path.join(os.path.expanduser("~/.skedulord"))
CONFIG_PATH = os.path.join(SKEDULORD_PATH, "config.yml")
HEARTBEAT_PATH = os.path.join(SKEDULORD_PATH, "heartbeat.jsonl")
