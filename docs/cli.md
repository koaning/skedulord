##  run       

Run a single command, which is logged by skedulord.

```text
Arguments:
  NAME     The name you want to assign to the run.  [required]
  COMMAND  The command you want to run (in parentheses).  [required]

Options:
  --retry INTEGER  The number of re-tries, should a job fail.  [default: 1]
  --wait INTEGER   The number of seconds between tries.  [default: 60]
  --help           Show this message and exit.
```

##  schedule  

Set (or reset) cron jobs based on config.

```text
Arguments:
  CONFIG  The config file containing the schedule.  [required]

Options:
  --help  Show this message and exit.
```

##  history   

Shows a table with job status.

```
Options:
  --n INTEGER                     How many rows should the table show.
                                  [default: 10]

  --only-failures / --no-only-failures
                                  Only show failures.  [default: False]
  --date TEXT                     Only show specific date.
  --jobname TEXT                  Only show jobs with specific name.
  --help                          Show this message and exit.
```

## build     

Builds static html files so you may view a dashboard.

```text
Options:
  --help  Show this message and exit.
```

##  serve     

Opens the dashboard in a browser.

```text
Options:
  --build / --no-build  Build the dashboard before opening it.  [default:
                        True]
```
##  wipe      

Wipe the disk or schedule state.

```text
Arguments:
  WHAT  What to wipe. Either `disk` or `schedule`.  [required]

Options:
  --yes / --no-yes        Are you sure?  [default: False]
  --really / --no-really  Really sure?  [default: False]
  --user TEXT             The name of the user. Default: curent user.
  --help                  Show this message and exit.
```

##  version   

Show the version.

```text
Options:
  --help  Show this message and exit.
```