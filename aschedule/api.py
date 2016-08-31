# -*- coding: utf-8 -*-

from datetime import datetime, timedelta as _timedelta_cls
import asyncio

all_schedules = {}


class AsyncSchedulePlan(object):
    def __init__(self, interval, count=float('inf'), loop=None, start_at=None):
        """
        :param interval: the repeating interval in seconds
        :param count: number of times to execute this task
        """
        self.interval = interval
        self.count = count
        self.current = 0
        self.loop = loop
        self.start_at = start_at
        self.running_jobs = set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current == self.count:
            raise StopAsyncIteration
        self.current += 1
        await asyncio.sleep(self.interval, loop=self.loop)

    def job_future_done_callback(self, future: asyncio.Future):
        self.running_jobs.remove(future)

    async def run(self, job):
        if self.start_at is not None:
            td = self.start_at - datetime.now()
            if round(td.total_seconds()) > 0:
                await asyncio.sleep(round(td.total_seconds()), loop=self.loop)
            fut = asyncio.ensure_future(job(), loop=self.loop)
            self.running_jobs.add(fut)
            fut.add_done_callback(self.job_future_done_callback)
            self.current += 1
        async for _ in self:
            fut = asyncio.ensure_future(job(), loop=self.loop)
            self.running_jobs.add(fut)
            fut.add_done_callback(self.job_future_done_callback)

    def cancel(self):
        # if not converted to list might give concurrent modification error on set's iteration.
        running_jobs = list(self.running_jobs)
        for fut in running_jobs:
            fut.cancel()


class BadOptions(BaseException):
    """
    exception for bad function params.
    """
    pass


class ScheduleNotFound(BaseException):
    """
    exception if schedule is not found.
    """
    pass


def cancel(future: asyncio.Future):
    """
    cancel's the schedule and all the currently running jobs of this schedule.
    usage:
        async def job():
            asyncio.sleep(10)
            print('hi')
            aschedule.cancel(schedule_future)
        schedule_future = aschedule.every(job, seconds=2)
        loop.run_until_complete(schedule_future)
    :raises ScheduleNotFound
    :param future: the schedule future created by aschedule.every or aschedule.once_at
    :return: None
    """
    if future in all_schedules:
        all_schedules[future].cancel()
        all_schedules.pop(future)
        future.cancel()
    else:
        raise ScheduleNotFound("Given future doesn't belong to any schedule of aschedule")


def every(job, seconds=0, minutes=0, hours=0, days=0, weeks=0,
          timedelta=None, start_at=None, loop=None):
    """
    default execution schedule is (now + interval, now + 2 * interval, ....)
    if start_at is provided (start, start + interval, start + 2 * interval, ....)
    if start_at is less than now then (now, now + interval, now + 2 * interval, ....)
    example:
        async def job():
            asyncio.sleep(10)
        aschedule.every(job, seconds=5)
    :param job: a callable(co-routine function) which returns
                a co-routine or a future or an awaitable
    :param seconds: number of seconds, 0...x
    :param minutes: number of minutes, 0...x
    :param hours: number of hours, 0...x
    :param days: number of days, 0...x
    :param weeks: number of weeks, 0...x
    :param timedelta: the interval can also be given in the format of datetime.timedelta,
                      then seconds, minutes, hours, days, weeks parameters are ignored.
    :param start_at: datetime at which the schedule starts if not
                     provided schedule starts at (now + interval)
    :param loop: io loop if the provided job is a custom future linked up
                 with a different event loop.
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    if timedelta is None:
        minutes, seconds = minutes + (seconds // 60), seconds % 60
        hours, minutes = hours + (minutes // 60), minutes % 60
        days, hours = days + (hours // 24), hours % 24
        weeks, days = weeks + (days // 7), days % 7
        timedelta = _timedelta_cls(seconds=seconds, minutes=minutes, hours=hours,
                                   days=days, weeks=weeks)
    interval = round(timedelta.total_seconds())
    if interval <= 0:
        raise BadOptions('given interval is invalid')
    plan = AsyncSchedulePlan(interval, loop=loop, start_at=start_at)
    fut = asyncio.ensure_future(plan.run(job), loop=loop)
    all_schedules[fut] = plan
    return fut


def once_at(job, dt: datetime, loop=None):
    """
    schedules a job at the given time
    :param job: a callable(co-routine function) which returns
                a co-routine or a future or an awaitable
    :param dt: datetime object at which the job should be executed once
               even if it is past it will be executed.
    :param loop: event loop if provided will be given to asyncio helper methods
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    plan = AsyncSchedulePlan(1, loop=loop, count=1, start_at=dt)
    return asyncio.ensure_future(plan.run(job), loop=loop)
