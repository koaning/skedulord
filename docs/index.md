# Documentation

![](images/skedulord.png)

The goal of this project is to offer a lightweight method
of organising log files for jobs that re-occur. It offers
a command line app that can integrate nicely with cron as
well as a small visualisation server. 

## Quick Start 

Suppose that we have a python file on our system that 
contains some logic. 

```python
# job.py
import time
for i in range(5):
    time.sleep(1)
    print(f"i am at iteration {i}")
```

Then we can run this job by using the `lord` commandline. 
First we need to call setup such that skedulord put folders
and settings in the right places.

```bash
lord setup
```

You should now see some new files; 

```bash
ls ~/.skedulord
```

Next we can run the job from the command line. If we wrap
it with `lord run` then the logs will automatically be placed
in the correct spot. We'll run it twice now. 

```bash
lord run --help
lord run pyjob "python job.py"
lord run pyjob "python job.py"
```

You can confirm that the logfiles have now been placed. 

```bash
ls ~/.skedulord/pyjob/*
```

Let's also demonstrate what will happen when a job is ran
that fails. Let's consider this jobfile. 

```python
assert 41 == 42
```

When you run this you should see bad output. 

```bash
lord run badpyjob "python job.py"
```

One thing you can do is apply add retry behavior. 

```bash
lord run badpyjob "python job.py" --retry 5 --wait 1
```

But a better idea would be to look at the logs. You can
go to the file yourself but you can also use the server
to view the status of the log files.

```bash
lord serve
```
