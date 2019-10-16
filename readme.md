![](skedulord/web/templates/logo.png)

## installation 

Install `skedulord` in the virtual environment via:

```bash
$ make develop
```

You can run the entire stack by running

```bash
$ make dev
```

## cron settings 

If you need help setting your crontab then you might enjoy the `python-crontab` package.


export PATH="$PATH:/home/vincentwarmerdam/.local/bin"

```python
from crontab import CronTab

cron = CronTab(user=True)
# make sure we overwrite other settings
cron.remove_all()

job1 = (cron
  .new(command='lord run 5mins "echo running"')
  .minute.every(5))
  
job2 = (cron
  .new(command='lord run 2days "echo running"')
  .dom.every(2))
  
job3 = (cron
  .new(command='lord run 4hrs "echo running"')
  .minute.every(4))

# show the current settings
print(cron.render())
# commit them to cron
cron.write()
```

```txt
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/home/vincentwarmerdam/.local/bin
* * * * * lord run j1 "echo running" # yolo
* * * * * lord run j2 "echo running" # boyo
* * * * * lord run j3 "/usr/bin/python3 /home/vincentwarmerdam/demo.py" # foyo
```
