import io

from clumper import Clumper
from rich.table import Table
from rich.console import Console
from rich.markdown import Markdown

from skedulord.common import heartbeat_path

WIDTH = 80


def generate_color_link_to_log(jobdata):
    result = "x" if jobdata['status'] == 'fail' else 'o'
    result = f"[link={heartbeat_path() / jobdata['logpath'].replace('txt', 'html')}]{result}[/link]"
    result = f"[red]{result}[/red]" if jobdata["status"] == "fail" else f"[green]{result}[/green]"
    return result


def generate_link_to_log(jobdata):
    result = "html"
    result = f"[link={heartbeat_path() / jobdata['logpath'].replace('txt', 'html')}]{result}[/link]"
    result = f"{result}/[link={heartbeat_path() / jobdata['logpath']}]txt[/link]"
    return result


def make_landing_page_table(heartbeat_data):
    clump = Clumper(heartbeat_data).sort(lambda _: _["start"], reverse=True)
    data = (clump
            .group_by("name")
            .mutate(fail=lambda _: _['status'] == 'fail')
            .agg(n_total=("id", "count"), n_fail=("fail", "sum"))
            .mutate(n_succes=lambda _: _["n_total"] - _["n_fail"])
            .collect())
    table = Table(title=None, width=WIDTH)
    table.add_column("name")
    table.add_column("recent")
    table.add_column("total runs")
    table.add_column("overview")
    for d in data:
        job_data = clump.keep(lambda _: _['name'] == d['name']).head(10).collect()
        recent = ' '.join([generate_color_link_to_log(_) for _ in job_data])
        table.add_row(d['name'], recent, str(d['n_total']), f"[link={heartbeat_path().parent / d['name']}.html]link[/link]")
        make_job_overview_page(heartbeat_data, d['name'])
    console = Console(record=True, width=WIDTH, file=io.StringIO())
    console.print(Markdown("# SKEDULORD"))
    console.print(Markdown("You can find an overview of all jobs below. Feel free to click links!"))
    console.print(table)
    console.save_html(heartbeat_path().parent / "index.html")


def make_job_overview_page(heartbeat_data, jobname):
    clump = Clumper(heartbeat_data).sort(lambda _: _["start"], reverse=True)
    data = (clump
            .keep(lambda d: d['name'] == jobname)
            .collect())
    table = Table(title=None, width=WIDTH)
    table.add_column("id")
    table.add_column("status")
    table.add_column("start")
    table.add_column("end")
    table.add_column("logs")
    for d in data:
        table.add_row(d['id'], d['status'], d['start'], d['end'], generate_link_to_log(d))

    console = Console(record=True, width=WIDTH, file=io.StringIO())
    console.print(f"[link={heartbeat_path().parent / 'index.html'}]Back to index.[/link]")
    console.print(Markdown(f"# Overview for **{jobname}**"))
    console.print(Markdown("You can find an overview of all jobs below. Feel free to click links!"))
    console.print(table)
    console.save_html(heartbeat_path().parent / f"{jobname}.html")


if __name__ == "__main__":
    data = Clumper.read_jsonl(heartbeat_path()).collect()
    make_landing_page_table(data)
