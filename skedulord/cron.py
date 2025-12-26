from pathlib import Path

import typer
from clumper import Clumper
from crontab import CronTab


def clean_cron(user: str):
    """Removes all entries in cron."""
    cron = CronTab(user=user)
    cron.remove_all()
    cron.write()


def parse_job_from_settings(settings: dict, name: str) -> dict:
    """Parse a job from a settings dictionary. """
    if len(settings) == 0:
        print(f"The name `{name}` doesn't appear in supplied schedule config.")
        raise typer.Exit(code=1)
    cmd_settings = settings[0]
    arguments = " ".join([f"--{k} {v}" for k, v in cmd_settings.get('arguments', {}).items()])
    
    # Ensure we remove the space at the end.
    return {
        "command": f"{cmd_settings['command']} {arguments}".rstrip(),
        "retry": cmd_settings.get("retry", 2),
        "wait": cmd_settings.get("wait", 60),
    }


class Cron:
    def __init__(self, settings_path):
        self.settings_path = Path(settings_path).resolve()
        self.settings = Clumper.read_yaml(self.settings_path).unpack("schedule").collect()

    def parse_cmd(self, setting: dict) -> str:
        """
        Parse single cron setting into elaborate command for crontab.
        """
        big_cmd = f'uv run python -m skedulord run {setting["name"]} --settings-path {str(self.settings_path)}'
        return big_cmd.rstrip()

    def set_new_cron(self):
        cron = CronTab(user=self.settings[0]["user"])
        cron.remove_all()

        for s in self.settings:
            s["name"] = s["name"].replace(" ", "-")
            cmd = self.parse_cmd(s)
            job = cron.new(command=cmd, comment=s["name"])
            job.setall(s["cron"])
        cron.write()
