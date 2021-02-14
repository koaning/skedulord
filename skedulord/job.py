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
        self.fancy_console = Console(
            record=True, file=io.StringIO(), width=120, log_path=False
        )
        self.basic_console = Console(
            record=True, file=io.StringIO(), width=120, log_path=False, log_time=False
        )

    def _logline(self, stuff):
        """
        Log a line to both consoles.
        """
        self.fancy_console.log(stuff)
        self.basic_console.log(stuff)

    def _attempt_cmd(self, command, name, run_id):
        tries = 1
        stop = False
        while not stop:
            self._logline(f"run_id={run_id}")
            self._logline(f"name={name}")
            self._logline(f"command={command}")
            self._logline(f"attempt={tries}")
            output = subprocess.run(
                command.split(" "),
                cwd=str(pathlib.Path().cwd()),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                universal_newlines=True,
            )
            for line in output.stdout.split("\n"):
                self._logline(line)
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
        self.basic_console.save_text(
            job_name_path(name) / f"{filename}.txt", clear=False
        )
        self.fancy_console.save_html(
            job_name_path(name) / f"{filename}.html", clear=False
        )
        return self
