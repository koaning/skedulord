import subprocess
from clumper import Clumper
from crontab import CronTab


def grab_nums(setting):
    return int("".join([s for s in setting["every"] if s.isdigit()]))


def parse_cmd(settings):
    """
    Parse settings into elaborate command for CRON.
    """
    # If no venv is given we assume the one you're currently in.
    python = "python"
    if "venv" not in settings.keys():
        output = subprocess.run(["which", "python"], capture_output=True)
        python = output.stdout.decode("ascii").replace("\n", "")
        print(python)
    # Set base values.
    retry = settings.get("retry", 1)
    wait = settings.get("wait", 60)
    # We only want to replace python if it is at the start.
    cmd = settings["command"]
    if cmd.startswith("python"):
        cmd = cmd.replace("python", python, 1)
    big_cmd = f'{python} -m skedulord run {settings["name"]} "{cmd}" --retry {retry} --wait {wait}'
    print(big_cmd)
    return big_cmd


def clean_cron(settings_file):
    settings = Clumper.read_yaml(settings_file).collect()[0]
    cron = CronTab(user=settings["user"])
    cron.remove_all()


def set_new_cron(settings_file):
    settings = Clumper.read_yaml(settings_file).unpack("schedule").collect()
    cron = CronTab(user=settings[0]["user"])
    cron.remove_all()

    for s in settings:
        s["name"] = s["name"].replace(" ", "-")
        cmd = parse_cmd(s)
        job = cron.new(command=cmd, comment=s["name"])
        num_every = grab_nums(s)
        if "min" in s["every"]:
            job.minute.every(num_every)
        if "hour" in s["every"]:
            job.hour.every(num_every)
        if "day" in s["every"]:
            job.day.every(num_every)

    cron.write()
