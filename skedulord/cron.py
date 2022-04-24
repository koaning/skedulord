import typer
import subprocess
from clumper import Clumper
from crontab import CronTab


def clean_cron(user: str):
    """Removes all entries in cron."""
    cron = CronTab(user=user)
    cron.remove_all()
    cron.write()


def parse_job_from_settings(settings: dict, name: str) -> str:
    """Parse a job from a settings dictionary. """
    if len(settings) == 0:
        print(f"The name `{name}` doesn't appear in supplied schedule config.")
        raise typer.Exit(code=1)
    cmd_settings = settings[0]
    arguments = " ".join([f"--{k} {v}" for k, v in cmd_settings.get('arguments', {}).items()])
    
    # Ensure we remove the space at the end.
    return f"{cmd_settings['command']} {arguments}".rstrip()


class Cron:
    def __init__(self, settings_path):
        self.settings = Clumper.read_yaml(settings_path).unpack("schedule").collect()

    def parse_cmd(self, setting: dict) -> str:
        """
        Parse single cron setting into elaborate command for crontab.
        """
        # If no venv is given we assume the one you're currently in.
        python = "python"
        if "venv" not in setting.keys():
            output = subprocess.run(["which", "python"], capture_output=True)
            python = output.stdout.decode("ascii").replace("\n", "")
        
        # Set base values.
        retry = setting.get("retry", 2)
        wait = setting.get("wait", 60)
        
        # We only want to replace python if it is at the start.
        cmd = setting["command"]
        if cmd.startswith("python"):
            cmd = cmd.replace("python", python, 1)
        big_cmd = f'{python} -m skedulord run {setting["name"]} "{cmd}" --retry {retry} --wait {wait}'
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
