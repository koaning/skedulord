import io
import datetime as dt
from pathlib import Path
from clumper import Clumper
from rich.console import Console
from skedulord.common import skedulord_path
from pkg_resources import resource_filename
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
        loader=FileSystemLoader(resource_filename('skedulord', 'templates')),
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
