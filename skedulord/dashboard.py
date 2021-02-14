import io

from clumper import Clumper
from rich.table import Table
from rich.console import Console
from rich.markdown import Markdown

from skedulord.common import heartbeat_path


def generate_color_link_to_log(jobdata):
    result = "x" if jobdata["status"] == "fail" else "o"
    result = f"[link={heartbeat_path() / jobdata['logpath'].replace('txt', 'html')}]{result}[/link]"
    result = (
        f"[red]{result}[/red]"
        if jobdata["status"] == "fail"
        else f"[green]{result}[/green]"
    )
    return result


def generate_link_to_log(jobdata):
    result = "html"
    result = f"[link={heartbeat_path() / jobdata['logpath'].replace('txt', 'html')}]{result}[/link]"
    result = f"{result}/[link={heartbeat_path() / jobdata['logpath']}]txt[/link]"
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
        self.build_index_page(clump=clump)
        for job in clump.select("name").drop_duplicates():
            self.make_job_overview_page(jobname=job["name"])

    def build_index_page(self, clump):
        """
        Build the index page.
        """
        summary = (
            clump.group_by("name")
            .mutate(fail=lambda _: _["status"] == "fail")
            .agg(n_total=("id", "count"), n_fail=("fail", "sum"))
            .mutate(n_succes=lambda _: _["n_total"] - _["n_fail"])
        )
        table = Table(title=None, width=self.width)
        table.add_column("name")
        table.add_column("recent runs")
        table.add_column("total")
        table.add_column("overview")
        for d in summary:
            job_data = clump.keep(lambda _: _["name"] == d["name"]).head(10).collect()
            recent = " ".join([generate_color_link_to_log(_) for _ in job_data])
            table.add_row(
                d["name"],
                recent,
                str(d["n_total"]),
                f"[link={heartbeat_path().parent / d['name']}.html]link[/link]",
            )
        console = Console(record=True, width=self.width, file=io.StringIO())
        img = """
                    _            _       _               _ 
                   | |          | |     | |             | |
                ___| | _____  __| |_   _| | ___  _ __ __| |
               / __| |/ / _ \/ _` | | | | |/ _ \| '__/ _` |
               \__ \   <  __/ (_| | |_| | | (_) | | | (_| |
               |___/_|\_\___|\__,_|\__,_|_|\___/|_|  \__,_|
        """
        console.print(img)
        console.print(
            Markdown("<img src='/Users/vincent/Development/skedulord/docs/logo.png)'/>")
        )
        console.print(
            Markdown(
                "### You can find an overview of all jobs below. Feel free to click links!"
            )
        )
        console.print(table)
        console.save_html(heartbeat_path().parent / "index.html")

    def make_job_overview_page(self, jobname):
        """
        Generate a page for a single job overview.
        """
        data = (
            Clumper(self.heartbeat_data)
            .sort(lambda _: _["start"], reverse=True)
            .keep(lambda _: _["name"] == jobname)
            .collect()
        )
        table = Table(title=None, width=self.width)
        table.add_column("id")
        table.add_column("status")
        table.add_column("start")
        table.add_column("end")
        table.add_column("logs")
        for d in data:
            table.add_row(
                d["id"],
                color_status(d["status"]),
                d["start"],
                d["end"],
                generate_link_to_log(d),
            )

        console = Console(record=True, width=self.width, file=io.StringIO())
        console.print(
            f"[link={heartbeat_path().parent / 'index.html'}]Back to index.[/link]"
        )
        console.print(Markdown(f"# Overview for **{jobname}**"))
        console.print(
            Markdown("### You can find an overview below. Feel free to click links!")
        )
        console.print(table)
        console.save_html(heartbeat_path().parent / f"{jobname}.html")


if __name__ == "__main__":
    data = Clumper.read_jsonl(heartbeat_path()).collect()
    Dashboard(data).build()
