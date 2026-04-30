from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import asyncio

class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.jobs = []
    
    def every(self, interval: int):
        return self._IntervalBuilder(self, interval)
    
    def cron(self, cron_string: str):
        def decorator(func):
            self.scheduler.add_job(func, CronTrigger.from_crontab(cron_string))
            return func
        return decorator
    
    def start(self):
        self.scheduler.start()
    
    def stop(self):
        self.scheduler.shutdown()
    
    class _IntervalBuilder:
        def __init__(self, scheduler, interval):
            self.scheduler = scheduler
            self.interval = interval
            self.unit = 'seconds'
        
        def seconds(self):
            self.unit = 'seconds'
            return self
        
        def minutes(self):
            self.unit = 'minutes'
            return self
        
        def hours(self):
            self.unit = 'hours'
            return self
        
        def days(self):
            self.unit = 'days'
            return self
        
        def at(self, time_str: str):
            def decorator(func):
                trigger_time = datetime.strptime(time_str, "%H:%M").time()
                def wrapper():
                    now = datetime.now()
                    target = datetime.combine(now.date(), trigger_time)
                    if now > target:
                        target += timedelta(days=1)
                    delay = (target - now).total_seconds()
                    asyncio.get_event_loop().call_later(delay, func)
                if self.unit == 'seconds':
                    interval_seconds = self.interval
                elif self.unit == 'minutes':
                    interval_seconds = self.interval * 60
                elif self.unit == 'hours':
                    interval_seconds = self.interval * 3600
                else:
                    interval_seconds = self.interval * 86400
                self.scheduler.scheduler.add_job(wrapper, 'interval', seconds=interval_seconds)
                return func
            return decorator