# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
import asyncio


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

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current == self.count:
            raise StopAsyncIteration
        self.current += 1
        await asyncio.sleep(self.interval, loop=self.loop)

    async def run(self, job):
        if self.start_at is not None:
            td = self.start_at - datetime.now()
            if td > timedelta.resolution and td.seconds > 0:
                await asyncio.sleep(td.seconds, loop=self.loop)
            asyncio.ensure_future(job(), loop=self.loop)
            self.current += 1
        async for _ in self:
            asyncio.ensure_future(job(), loop=self.loop)


class BadOptions(BaseException):
    """
    exception for bad function params
    """
    pass


def every(job, seconds=0, minutes=0, hours=0,
          days=0, weeks=0, start_at=None, loop=None):
    """
    default execution schedule is (now + interval, now + 2 * interval, ....)
    if start_at is provided (start, start + interval, start + 2 * interval, ....)
    if start_at is less than now then (now, now + interval, now + 2 * interval, ....)
    example:
        async def job():
            asyncio.sleep(10)
        schedule.every(job, seconds=5)
    :param job: a callable(co-routine function) which returns a co-routine or a future or an awaitable
    :param seconds: number of seconds, 0...x
    :param minutes: number of minutes, 0...x
    :param hours: number of hours, 0...x
    :param days: number of days, 0...x
    :param weeks: number of weeks, 0...x
    :param start_at: datetime at which the schedule starts
    :param loop: io loop if the provided job is a custom future
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    minutes, seconds = minutes + (seconds // 60), seconds % 60
    hours, minutes = hours + (minutes // 60), minutes % 60
    days, hours = days + (hours // 24), hours % 24
    interval = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks).seconds
    if interval == 0:
        raise BadOptions('given interval(0 seconds) is invalid')
    plan = AsyncSchedulePlan(interval, loop=loop, start_at=start_at)
    return asyncio.ensure_future(plan.run(job), loop=loop)


def at(job, dt: datetime, loop=None):
    """
    schedules a job at the given time
    :param job: a callable(co-routine function) which returns a co-routine or a future or an awaitable
    :param dt: datetime object at which the job should be executed once
    :param loop: event loop if provided will be given to asyncio helper methods
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    plan = AsyncSchedulePlan(1, loop=loop, count=1, start_at=dt)
    return asyncio.ensure_future(plan.run(job), loop=loop)
