import altair as alt
from fh_altair import altair2fasthtml, altair_headers
import polars as pl 
import traceback
import io
from pathlib import Path
import yaml
import re
import tomllib
import time 
import uuid 
import datetime as dt
import nbformat
import subprocess
from nbconvert.preprocessors import ExecutePreprocessor
from crontab import CronTab
from fasthtml.common import (
    # These are the HTML components we use in this app
    A, AX, Button, Card, CheckboxX, Container, Div, Form, Grid, Group, H1, H2, Hidden, Input, Li, Main, Script, Style, Textarea, Title, Titled, Ul,
    # These are FastHTML symbols we'll use
    Beforeware, FastHTML, fast_app, SortableJS, fill_form, picolink, serve,
    # These are from Starlette, Fastlite, fastcore, and the Python stdlib
    FileResponse, NotFoundError, RedirectResponse, database, patch, dataclass
)
from fasthtml.common import *
from fasthtml.core import *
import click
from contextlib import redirect_stdout


home_dir = Path.home() / ".skedulord"
log_dir = home_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
db = database(home_dir/ 'skedulord.db')
jobruns, users = db.t.jobruns, db.t.users

if jobruns not in db.t:
    users.create(dict(name=str, pwd=str), pk='name')
    jobruns.create(id=str, time_id=int, jobname=str, status=str, time_taken=int, dt=str, pk='id')


def parse_inline_metadata(script_content: str):
    metadata_pattern = r'^# /// script\n((?:# .*\n)+)# ///'
    match = re.search(metadata_pattern, script_content, re.MULTILINE)
    
    if not match:
        return None
    
    metadata_lines = match.group(1).strip().split('\n')
    metadata = {}
    
    # Join the metadata lines into a single string and parse it as TOML
    toml_string = '\n'.join(line.lstrip('# ') for line in metadata_lines)
    parsed_toml = tomllib.loads(toml_string)
    
    # Extract the required information from the parsed TOML
    if 'requires-python' in parsed_toml:
        metadata['python_version'] = parsed_toml['requires-python']
    if 'dependencies' in parsed_toml:
        metadata['dependencies'] = parsed_toml['dependencies']
    return metadata


def run_jupyter(notebook_path, output_path):
    print(f"About to run {notebook_path}.")
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    metadata = parse_inline_metadata(nb.cells[0].source)
    parsed_deps = ["nbconvert", "jupyterlab"] + metadata.get('dependencies', [])
    with_deps = []
    for dep in parsed_deps:
        with_deps.append("--with")
        with_deps.append(dep)
    
    uvpath = home_dir / "settings.yml"

    with open(uvpath, 'r') as file:
        data = yaml.safe_load(file)

    cmd = [data['uvpath'], "run"] + with_deps + ["jupyter", "nbconvert", "--allow-errors", "--to", "html", "--execute"]

    if output_path:
        cmd.append("--output")
        cmd.append(output_path)
    cmd.append(notebook_path)
    print(" ".join(cmd))

    # This is a bit of a hack, but the output cell with a mime-type can detect failure
    subprocess.check_output(cmd)
    tag = 'class="jp-RenderedText jp-OutputArea-output" data-mime-type="application/vnd.jupyter.stderr"'
    return tag not in Path(output_path + ".html").read_text()



class JobRunner:
    def __init__(self, job_name):
        self.job_name = job_name
    
    def write_logfile(self, time_id, out):
        log_file = log_dir / self.job_name / f"{time_id}.log"
        log_file.parent.mkdir(exist_ok=True, parents=True)
        Path(log_file).write_text(out)
        print(f"Logfile {log_file} updated.")

    def run_jupyter_notebook(self, notebook_path):
        print(f"Runner starting notebook run {notebook_path}. Output @{(log_dir / self.job_name)}")
        (log_dir / self.job_name).mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        run_id = str(uuid.uuid4())[:23]
        time_id = int(start_time)
        succes = run_jupyter(notebook_path, str(log_dir / self.job_name / f"{time_id}.ipynb"))
        end_time = time.time()
        info = dict(jobname=self.job_name, 
                    id=run_id, 
                    time_id=time_id,
                    status='succes', 
                    time_taken=end_time - start_time, 
                    dt=dt.datetime.now().isoformat())
        if succes:
            jobruns.insert(info)
            return run_id
        info['status'] = 'fail'
        jobruns.insert(info)
        return "fail"


@click.group()
def cli():
    """Skedulord CLI for scheduling and running jobs."""
    pass


@cli.command()
def empty():
    """Empty the cronjobs."""
    cron = CronTab(user=True)
    cron.remove_all()
    cron.write()
    click.echo("All existing cron jobs have been removed.")
    

@cli.command()
@click.argument('schedule_yml')
def schedule(schedule_yml):
    """Schedule a job to run at specified intervals."""
    # Remove all existing cron jobs
    cron = CronTab(user=True)
    cron.remove_all()
    cron.write()
    
    # Parse the schedule YAML file
    with open(schedule_yml, 'r') as file:
        schedule_data = yaml.safe_load(file)
    
    cron = CronTab(user=True)
    output = subprocess.run(["which", "python"], capture_output=True)
    python = output.stdout.decode("ascii").replace("\n", "")
    cwd = Path.cwd()
    for item in schedule_data['items']:
        command = f'{python} -m skedulord run {item['name']} {str(cwd / item['notebook'])}'
        job = cron.new(command=command)
        job.setall(item['schedule'])
        click.echo(f"Job '{item['name']}' scheduled with cron schedule: {item['schedule']}")
    cron.write()


@cli.command()
@click.argument('job_name')
@click.argument('notebook_path')
def run(job_name, notebook_path):
    """Run a job immediately."""
    runner = JobRunner(job_name)
    run_id = runner.run_jupyter_notebook(notebook_path)
    click.echo(f"Job '{job_name}' completed with run ID: {run_id}")


@cli.command()
def wipe():
    """Run a job immediately."""
    import shutil
    shutil.rmtree(log_dir)
    (home_dir / "skedulord.db").unlink()


app, rt = fast_app(hdrs=altair_headers)

def run_table(runs):
    return Div(
        Table(
            Thead(
                Tr(
                    Th("id", scope="col"),
                    Th("jobname", scope="col"),
                    Th("status", scope="col"),
                    Th("timestamp", scope="col"),
                    Th("time taken", scope="col"),
                )
            ),
            Tbody(
                *[Tr(
                    Th(A(run["id"], href=f"/run/{run['jobname']}/{run['time_id']}")), 
                    Th(run["jobname"]), 
                    Th(run["status"]),
                    Th(run["dt"][:19]), 
                    Th(run["time_taken"])
                ) for run in runs]
            )
        )
    )


@rt('/')
def get(): 
    jobs = db.q("select jobname, COUNT(*) as c from jobruns group by jobname")
    runs = db.q("select * from jobruns order by dt desc limit 10")
    return Div(
        Container(
            H2("skedulord"),
            H3("Jobs"),
            Table(
                Thead(
                    Tr(
                        Th("name", scope="col"),
                        Th("runcount", scope="col"),
                    )
                ),
                Tbody(
                    *[Tr(
                        Th(A(job["jobname"], href=f"/run/{job['jobname']}")), 
                        Th(job["c"]), 
                    ) for job in jobs]
                )
            ),
            H3("Runs"),
            run_table(runs),
        ),
        data_theme="light", style="background-color: var(--pico-background-color); color: var(--pico-color);"
    )

@rt('/run/{jobname}/{timeid}')
def get(jobname:str, timeid:str): 
    html_logs = Path.home() / ".skedulord" / "logs" / jobname / f"{timeid}.ipynb.html"
    return html_logs.read_text()


def time_taken_chart(runs):
    df = pl.DataFrame(runs).with_columns(timestamp=pl.col("dt").str.to_datetime())
    chart1 = alt.Chart(df).mark_line().encode(x="timestamp:T", y="time_taken:Q")
    chart2 = alt.Chart(df).mark_point().encode(x="timestamp:T", y="time_taken:Q", color=alt.Color("status", sort=["succes", "fail"]))
    return altair2fasthtml(chart1 + chart2)

@rt('/run/{jobname}')
def get(jobname:str): 
    runs = db.q(f"select * from jobruns where jobname == ?", (jobname, ))
    return Div(
            Container(
            H2(Span(A("skedulord", href="/"), "/", f"{jobname}")),
            time_taken_chart(runs),
            H3("Runs:"),
            run_table(runs),
        ),
        data_theme="light", style="background-color: var(--pico-background-color); color: var(--pico-color);"
    )

@cli.command(name='serve')
def runserver():
    """Start a web server."""
    import uvicorn
    click.echo("Starting web server...")
    uvicorn.run("skedulord.__main__:app", port=5000, log_level="info", reload=True)


if __name__ == "__main__":
    cli()
