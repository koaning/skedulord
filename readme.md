![](docs/full-logo.png)

Skedulord is a tool that automates scheduling and logging of jobs. It's a 
layer on top of cron meant for python users. 

## Installation 

```python
> pip install skedulord
```

## Usage 

These are all the commands available: 

```
> python -m skedulord
Usage: __main__.py [OPTIONS] COMMAND [ARGS]...

  SKEDULORD: helps with cronjobs and logs.

Options:
  --help  Show this message and exit.

Commands:
  schedule  Set (or reset) cron jobs based on config.
  run       Run a single command, which is logged by skedulord.
  history   Shows a table with job status.
  summary   Shows a summary of all jobs.``
  build     Builds static html files so you may view a dashboard.
  serve     Opens the dashboard in a browser.
  wipe      Wipe the disk or schedule state.
  version   Show the version.
```
