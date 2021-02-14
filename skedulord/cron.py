import subprocess
from clumper import Clumper
from crontab import CronTab


def clean_cron(user):
    cron = CronTab(user=user)
    cron.remove_all()
    cron.write()


class Cron:
    def __init__(self, settings_path):
        self.settings = Clumper.read_yaml(settings_path).unpack("schedule").collect()

    def grab_nums(self, setting):
        return int("".join([s for s in setting["every"] if s.isdigit()]))

    def parse_cmd(self, settings):
        """
        Parse settings into elaborate command for CRON.
        """
        # If no venv is given we assume the one you're currently in.
        python = "python"
        if "venv" not in settings.keys():
            output = subprocess.run(["which", "python"], capture_output=True)
            python = output.stdout.decode("ascii").replace("\n", "")
        # Set base values.
        retry = settings.get("retry", 1)
        wait = settings.get("wait", 60)
        # We only want to replace python if it is at the start.
        cmd = settings["command"]
        if cmd.startswith("python"):
            cmd = cmd.replace("python", python, 1)
        big_cmd = f'{python} -m skedulord run {settings["name"]} "{cmd}" --retry {retry} --wait {wait}'
        return big_cmd

    def set_new_cron(self):
        cron = CronTab(user=self.settings[0]["user"])
        cron.remove_all()

        for s in self.settings:
            s["name"] = s["name"].replace(" ", "-")
            cmd = self.parse_cmd(s)
            job = cron.new(command=cmd, comment=s["name"])
            job.setall(s["cron"])
        cron.write()
