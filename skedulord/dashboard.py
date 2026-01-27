import io
import json
import shutil
import datetime as dt
from pathlib import Path
from clumper import Clumper
from rich.console import Console
from skedulord.common import skedulord_path
from skedulord.db import fetch_runs
from importlib.resources import files
from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_html(logpath):
    text = Path(logpath).read_text()

    console = Console(record=True, file=io.StringIO(), log_path=False, log_time=False, width=2000)
    for line in text.split("\n"):
        console.print(line)
    console.save_html(str(logpath).replace(".txt", ".html"))


def build_site():
    heartbeats = Clumper.read_jsonl(Path(skedulord_path()) / "heartbeat.jsonl")
    clump = (heartbeats
             .mutate(jobname=lambda d: d['name'],
                     details=lambda d: "link")
             .group_by("jobname")
             .agg(start=("start", "last"),
                  end=("end", "last"),
                  status=("status", "last"))
             .mutate(start_time = lambda d: dt.datetime.strptime(d['start'], "%Y-%m-%d %H:%M:%S"),
                     end_time = lambda d: dt.datetime.strptime(d['end'], "%Y-%m-%d %H:%M:%S"),
                     timediff = lambda d: (d['end_time'] - d['start_time']).seconds)
             .sort(lambda d: d['start_time'], reverse=True))

    env = Environment(
        loader=FileSystemLoader(str(files("skedulord").joinpath("templates"))),
        autoescape=select_autoescape(['html', 'xml'])
    )

    main_page = env.get_template('index.html').render(jobs=clump.collect())
    Path(Path(skedulord_path()) / "index.html").write_text(main_page)
    
    for item in clump.collect():
        jobname = item['jobname']
        subset = (heartbeats
                  .keep(lambda d: d['name'] == jobname)
                  .mutate(start_time = lambda d: dt.datetime.strptime(d['start'], "%Y-%m-%d %H:%M:%S"),
                          end_time = lambda d: dt.datetime.strptime(d['end'], "%Y-%m-%d %H:%M:%S"),
                          timediff = lambda d: (d['end_time'] - d['start_time']).seconds,
                          txt_path = lambda d: f"{jobname}/{d['start'].replace(' ', 'T')}.txt",
                          html_path = lambda d: f"{jobname}/{d['start'].replace(' ', 'T')}.html",)
                  .sort(lambda d: d['start_time'], reverse=True))
        
        job_page = env.get_template('job.html').render(jobname=jobname, runs=subset.collect())
        Path(Path(skedulord_path()) / f"{jobname}.html").write_text(job_page)
    
    for p in Path(skedulord_path()).glob("*/*.txt"):
        create_html(p)


def export_static_site(output_dir: Path) -> None:
    """Export a static site with JSON API mocks that can be hosted without a server."""
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create api directories
    api_dir = output_dir / "api"
    api_dir.mkdir(exist_ok=True)
    logs_dir = api_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Fetch all runs from database
    runs = list(fetch_runs())
    runs_data = [
        {
            "id": row["id"],
            "name": row["name"],
            "command": row["command"],
            "status": row["status"],
            "start": row["start"],
            "end": row["end"],
            "logpath": row["logpath"],
        }
        for row in runs
    ]

    # Write api/runs.json
    (api_dir / "runs.json").write_text(json.dumps(runs_data, indent=2))

    # Write api/logs/{runId}.json for each run
    for run in runs_data:
        run_id = run["id"]
        logpath = run["logpath"]
        log_content = ""

        if logpath and Path(logpath).exists():
            try:
                log_content = Path(logpath).read_text()
            except Exception:
                log_content = f"Error reading log file: {logpath}"

        log_data = {
            "logpath": logpath,
            "content": log_content,
        }
        (logs_dir / f"{run_id}.json").write_text(json.dumps(log_data, indent=2))

    # Copy webapp dist if it exists
    webapp_dist = Path(__file__).parent.parent / "webapp" / "dist"
    if webapp_dist.exists():
        for item in webapp_dist.iterdir():
            dest = output_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    else:
        # Try installed package location
        try:
            pkg_webapp = files("skedulord").joinpath("webapp_dist")
            if pkg_webapp.is_dir():
                for item in pkg_webapp.iterdir():
                    dest = output_dir / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
        except Exception:
            pass

    return len(runs_data)
