import io
import datetime as dt
from pathlib import Path

from clumper import Clumper
from rich.table import Table
from rich.console import Console
from rich.markdown import Markdown

from skedulord.common import heartbeat_path, skedulord_path


def create_html(logpath):
    text = pathlib.Path(logpath).read_text()

    console = Console(record=True, file=io.StringIO(), log_path=False, log_time=False, width=2000)
    for line in text.split("\n"):
        console.print(line)
    console.save_html(str(logpath).replace(".txt", ".html"))


def generate_color_link_to_log(jobdata):
    result = "x" if jobdata["status"] == "fail" else "o"
    logpath = Path(jobdata['logpath']).relative_to(skedulord_path())
    result = f"[link={str(logpath).replace('txt', 'html')}]{result}[/link]"
    result = (
        f"[red]{result}[/red]"
        if jobdata["status"] == "fail"
        else f"[green]{result}[/green]"
    )
    return result


def generate_link_to_log(jobdata):
    result = "html"
    logpath = Path(jobdata['logpath']).relative_to(skedulord_path())
    result = f"[link={str(logpath).replace('txt', 'html')}]{result}[/link]"
    result = f"{result}/[link={logpath}]txt[/link]"
    return result


def color_status(status):
    return f"[red]{status}[/red]" if status == "fail" else f"[green]{status}[/green]"


class Dashboard:
    """
    Helper class to generate the dashboards.
    """

    def __init__(self, heartbeat_data, width=80):
        self.heartbeat_data = heartbeat_data
        self.width = width

    def build(self):
        """
        Generates the landing page for the dashboard.
        """
        clump = Clumper(self.heartbeat_data).sort(lambda _: _["start"], reverse=True)

        # Generate summary data for the table on the front page.
        (clump
            .mutate(logpath=lambda d: d['logpath'].replace(".txt", ".html"))
            .group_by('name')
            .agg(
                last_status=('status', 'first'),
                last_log=('logpath', 'first'),
                last_run=('start', 'first'),
                runs=('id', 'count'),
                hit_list=('status', lambda d: d[:10]),
                log_list=('logpath', lambda d: d[:10]),
            )
            .mutate(recent=lambda d: [{'status': s, 'logpath': p} for s, p in zip(d['hit_list'], d['log_list'])])
            .drop('log_list', 'hit_list')
            .sort(lambda d: d['name'])
            .write_json(Path(skedulord_path()) / 'index.json')
        )

        # Create .csv file for each job.
        for job in clump.select("name").drop_duplicates():
            csv_path = Path(skedulord_path()) / (job['name'] + '.csv')
            (clump
                .keep(lambda d: d['name'] == job['name'])
                .sort(lambda d: d['start'], reverse=True)
                .write_csv(csv_path))

if __name__ == "__main__":
    # data = Clumper.read_jsonl(heartbeat_path()).collect()
    # Dashboard(data).build()
    import pathlib
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    heartbeats = Clumper.read_jsonl(pathlib.Path(skedulord_path()) / "heartbeat.jsonl")
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
        loader=FileSystemLoader('skedulord/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    pathlib.Path("/home/vincent/.skedulord/index.html").write_text(env.get_template('index.html').render(jobs=clump.collect()))
    
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
        pathlib.Path(f"/home/vincent/.skedulord/{jobname}.html").write_text(env.get_template('job.html').render(jobname=jobname, runs=subset.collect()))
    
    for p in pathlib.Path("/home/vincent/.skedulord/").glob("*/*.txt"):
        create_html(p)

