import io
import json
import time
import uuid
import pathlib
import subprocess
import datetime as dt
from skedulord.common import job_name_path, log_heartbeat
from pathlib import Path

class JobRunner:
    """
    Object in charge of running a job and logging it.
    """

    def __init__(self, name, cmd, retry=3, wait=60):
        self.name = name
        self.cmd = cmd
        self.retry = retry
        self.wait = wait
        self.start_time = str(dt.datetime.now())[:19].replace(" ", "T")
        self.logpath = Path(job_name_path(name)) / f"{self.start_time}.txt"
        pathlib.Path(self.logpath).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.logpath).touch()
        self.file = self.logpath.open("a")

    def _attempt_cmd(self, command, name, run_id):
        tries = 1
        stop = False
        while not stop:
            info = {"name": name, "command": command, "run_id": run_id, "attempt": tries, "timestamp": str(dt.datetime.now())}
            self.file.writelines([json.dumps(info), "\n"])            
            output = subprocess.run(
                command.split(" "),
                cwd=str(pathlib.Path().cwd()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                universal_newlines=True,
            )
            for line in output.stdout.split("\n"):
                self.file.writelines([line, "\n"])
            if output.returncode == 0:
                stop = True
            else:
                tries += 1
                if tries > self.retry:
                    stop = True
                else:
                    time.sleep(self.wait)
        return "fail" if tries > self.retry else "success"

    def run(self):
        """
        Run and log a command.
        """
        run_id = str(uuid.uuid4())[:8]
        start_time = self.start_time
        status = self._attempt_cmd(command=self.cmd, name=self.name, run_id=run_id)
        endtime = str(dt.datetime.now())[:19]
        job_name_path(self.name).mkdir(parents=True, exist_ok=True)
        logpath = str(job_name_path(self.name) / f"{start_time}.txt")
        log_heartbeat(
            run_id=run_id,
            name=self.name,
            command=self.cmd,
            status=status,
            tic=start_time.replace("T", " "),
            toc=endtime,
            logpath=logpath
        )
