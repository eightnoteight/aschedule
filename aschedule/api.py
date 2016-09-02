# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime, timedelta as _timedelta_cls
from math import ceil
from functools import partial
import itertools
import asyncio

from .helpers import WaitAsyncIterator


class JobSchedule(object):
    def __init__(self, get_coro_or_fut, intervals, loop=None):
        """
        :param get_coro_or_fut: a callable which returns a co-routine object or a future
                                or an awaitable.
         :param intervals: an iterator which gives interval times between consecutive
                           jobs.
        :param loop: loop passed to asyncio loop
        """
        self.uuid = uuid4()
        self.job = get_coro_or_fut
        self.intervals = intervals
        self.loop = loop
        self.running_jobs = set()
        self.wait_iter = WaitAsyncIterator(intervals, loop=loop)
        self.future = asyncio.ensure_future(self._run(), loop=loop)

    def _job_future_done_callback(self, future: asyncio.Future):
        self.running_jobs.remove(future)

    async def _run(self):
        async for _ in self.wait_iter:
            future = asyncio.ensure_future(self.job(), loop=self.loop)
            self.running_jobs.add(future)
            future.add_done_callback(self._job_future_done_callback)
        await asyncio.gather(*list(self.running_jobs), loop=self.loop)

    def cancel(self, running_jobs=False):
        self.future.cancel()
        if running_jobs:
            running_jobs = list(self.running_jobs)
            for job_future in running_jobs:
                job_future.cancel()

    def __hash__(self):
        return hash(self.uuid)


class ScheduleManager(object):

    def __init__(self):
        self.schedules = set()

    def _schedule_done_callback(self, schedule, _):
        self.schedules.remove(schedule)  # this must never give KeyError as

    def every(self, get_coro_or_fut, interval: _timedelta_cls, start_at: datetime,
              count=float('inf'), loop=None):
        diff = start_at - datetime.now()
        if round(diff.total_seconds()) < 0:
            start_at += interval * ceil((-diff) / interval)
        intervals = itertools.chain(
            iter([round((start_at - datetime.now()).total_seconds())]),
            map(lambda x: x[1], itertools.takewhile(lambda x: x[0] < count,
                                                    enumerate(itertools.repeat(round(interval.total_seconds()))))))
        schedule = JobSchedule(get_coro_or_fut, intervals, loop=loop)
        self.schedules.add(schedule)
        schedule.future.add_done_callback(
            partial(self._schedule_done_callback, schedule))
        return schedule

    def once_at(self, get_coro_or_fut, run_at: datetime, strict=False, loop=None):
        diff = run_at - datetime.now()
        if round(diff.total_seconds()) >= 0 or not strict:
            intervals = iter([max(round(diff.total_seconds()), 0)])
            schedule = JobSchedule(get_coro_or_fut, intervals, loop=loop)
            self.schedules.add(schedule)
            schedule.future.add_done_callback(self._schedule_done_callback)
            return schedule
        else:
            raise AScheduleException(
                "the given time({given}) is in past. "
                "current time is {now}. ".format(given=run_at, now=datetime.now()))

    def cancel(self, schedule: JobSchedule, running_jobs=True):
        if schedule not in self.schedules:
            raise AScheduleException("given schedule doesn't belong to this "
                                     "ScheduleManager instance")
        schedule.cancel(running_jobs)

    def shutdown(self):
        for schedule in self.schedules:
            schedule.cancel()


class AScheduleException(Exception):
    pass


default_schedule_manager = ScheduleManager()


def cancel(schedule: JobSchedule, running_jobs=False):
    default_schedule_manager.cancel(schedule, running_jobs)


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
    :param seconds: number of seconds, 0...59
    :param minutes: number of minutes, 0...59
    :param hours: number of hours, 0...23
    :param days: number of days, 0...x
    :param weeks: number of weeks, 0...x
    :param timedelta: the interval can also be given in the format of datetime.timedelta,
                      then seconds, minutes, hours, days, weeks parameters are ignored.
    :param start_at: datetime at which the schedule starts if not
                     provided schedule starts at (now).
    :param loop: io loop if the provided job is a custom future linked up
                 with a different event loop.
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    if timedelta is None:
        timedelta = _timedelta_cls(seconds=seconds, minutes=minutes, hours=hours,
                                   days=days, weeks=weeks)
    if round(timedelta.total_seconds()) <= 0:
        raise AScheduleException("given interval is invalid i.e "
                                 "one of seconds, minutes, hours, days, weeks is invalid")
    if start_at is None:
        start_at = datetime.now()
    return default_schedule_manager.every(job, timedelta, start_at, loop=loop)


def once_at(job, run_at: datetime, loop=None, strict=False):
    """
    schedules a job at the given time
    :param job: a callable(co-routine function) which returns
                a co-routine or a future or an awaitable
    :param run_at: datetime object at which the job should be executed once
               even if it is past it will be executed.
    :param loop: event loop if provided will be given to asyncio helper methods
    :param strict: if the run_at is in the past this will raise an exception if strict
                   is True, if strict is False it will assume it to be a pending job
                   and will schedule it to execute asap.
    :return: future of the schedule, so it could be cancelled at will of the user
    """
    return default_schedule_manager.once_at(job, run_at, strict=strict, loop=loop)
