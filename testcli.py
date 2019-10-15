from crontab import CronTab

cron = CronTab(user=True)

job  = cron.new(command='/usr/bin/echo')
job.minute.every(1)

print(cron.lines)