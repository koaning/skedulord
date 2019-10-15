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


```python
from crontab import CronTab

cron = CronTab(user=True)

job1 = (cron
  .new(command='lord run 5mins "echo running"')
  .minute.every(5))
  
job2 = (cron
  .new(command='lord run 2days "echo running"')
  .dom.every(2))
  
job3 = (cron
  .new(command='lord run 4hrs "echo running"')
  .minute.every(4))

print(cron.render())
```