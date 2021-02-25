import io
import time
import uuid
import pathlib
import subprocess
import datetime as dt
from skedulord.common import job_name_path, log_heartbeat
from rich.console import Console


class JobRunner:
    """
    Object in charge of running a job and logging it.
    """

    def __init__(self, retry=3, wait=60):
        self.retry = retry
        self.wait = wait
        self.console = Console(
            record=True, file=io.StringIO(), width=120, log_path=False, log_time=False
        )

    def _attempt_cmd(self, command, name, run_id):
        tries = 1
        stop = False
        while not stop:
            print(tries)
            self.console.log(f"run_id={run_id}")
            self.console.log(f"name={name}")
            self.console.log(f"command={command}")
            self.console.log(f"attempt={tries}")
            output = subprocess.run(
                command.split(" "),
                cwd=str(pathlib.Path().cwd()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                universal_newlines=True,
            )
            print(output)
            for line in output.stdout.split("\n"):
                self.console.log(line)
            if output.returncode == 0:
                stop = True
            else:
                tries += 1
                if tries > self.retry:
                    stop = True
                else:
                    time.sleep(self.wait)
        return "fail" if tries > self.retry else "success"

    def cmd(self, name, command):
        """
        Run and log a command.
        """
        run_id = str(uuid.uuid4())[:8]
        start_time = str(dt.datetime.now())[:19]
        status = self._attempt_cmd(command=command, name=name, run_id=run_id)
        endtime = str(dt.datetime.now())[:19]
        filename = start_time.replace(" ", "T")
        job_name_path(name).mkdir(parents=True, exist_ok=True)
        log_heartbeat(
            run_id=run_id,
            name=name,
            command=command,
            status=status,
            tic=start_time,
            toc=endtime,
            logpath=str(job_name_path(name) / f"{filename}.txt"),
        )
        self.console.save_text(
            job_name_path(name) / f"{filename}.txt", clear=False
        )
        self.console.save_html(
            job_name_path(name) / f"{filename}.html", clear=False
        )
        return self
