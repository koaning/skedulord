import io
import time
import uuid
import pathlib
import subprocess
import datetime as dt
from contextlib import redirect_stdout

import click

from skedulord.logger import log_to_disk, logcli


class JobChain:
    def __init__(self, name, attemps=3, wait=10):
        self.name = name
        self.attemps = attemps
        self.wait = wait
        self.steps = []

    def then(self, func, args, kwargs):
        self.steps.append((func, args, kwargs))
        return self

    def run(self):
        f = io.StringIO()
        tic = dt.datetime.now()
        with redirect_stdout(f):
            for func, args, kwargs in self.steps:
                tries = 0
                stop = False
                while not stop:
                    try:
                        msg = f"attempt {tries + 1} - about to run {func.__name__} args:{args}, kwargs:{kwargs}"
                        click.echo(msg)
                        func(*args, **kwargs)
                        stop = True
                    except:
                        tries += 1
                        if tries >= self.attemps:
                            raise RuntimeError("max attempts reached")
                        time.sleep(self.wait)
        tock = dt.datetime.now()
        log_to_disk(run_id=str(uuid.uuid4())[:8],
                    name=self.name,
                    command="jobchain",
                    tic=tic,
                    tries=tries,
                    toc=tock,
                    succeed=(tries < (self.attemps + 1)),
                    output=f.getvalue(),
                    silent=True)
        return self


class JobRunner:
    def __init__(self, attemps=3, wait=60):
        self.attemps = attemps
        self.wait = wait

    def sleep(self, s=60):
        time.sleep(s)

    def run(self, jobname, func, *args, **kwargs):
        f = io.StringIO()
        tic = dt.datetime.now()
        with redirect_stdout(f):
            tries = 0
            stop = False
            while not stop:
                try:
                    msg = f"attempt {tries + 1} - about to run {func.__name__} args:{args}, kwargs:{kwargs}"
                    click.echo(msg)
                    func(*args, **kwargs)
                    stop = True
                except:
                    tries += 1
                    if tries >= self.attemps:
                        raise RuntimeError("max attempts reached")
                    time.sleep(self.wait)
        tock = dt.datetime.now()
        log_to_disk(run_id=str(uuid.uuid4())[:8],
                    name=jobname,
                    command=f"{func.__name__}-{args}-{kwargs}",
                    tic=tic,
                    tries=tries,
                    toc=tock,
                    succeed=tries < (self.attemps + 1),
                    output=f.getvalue(),
                    silent=True)
        return self

    def cmd(self, name, command):
        tries = 1
        tic = dt.datetime.now()
        run_id = str(uuid.uuid4())[:8]
        stop = False
        logs = ""

        while not stop:
            logs += f"{command} - {run_id} - attempt {tries} - {str(dt.datetime.now())} \n"
            output = subprocess.run(command.split(" "),
                                    cwd=str(pathlib.Path().cwd()),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    encoding='utf-8',
                                    universal_newlines=True)

            logs += output.stdout
            if output.returncode == 0:
                stop = True
            else:
                tries += 1
                if tries > self.attemps:
                    stop = True
                else:
                    time.sleep(self.wait)
        log_to_disk(run_id=run_id,
                    name=name,
                    command=command,
                    tries=tries,
                    tic=tic,
                    toc=dt.datetime.now(),
                    succeed=(tries < (self.attemps + 1)),
                    output=logs)
        return self


if __name__ == "__main__":
    def printsleep(t=1, text="yo"):
        time.sleep(t)
        for i in range(10):
            logcli(text)

    (JobRunner()
     .run("sleep1", printsleep, t=1, text="fast")
     .run("sleep2", printsleep, t=1, text="faster"))
