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

    def _cancel(self, running_jobs=False):
        self.future.cancel()
        if running_jobs:
            running_jobs = list(self.running_jobs)
            for job_future in running_jobs:
                job_future.cancel()

    def __hash__(self):
        return hash(self.uuid)


class ScheduleManager(object):

    def __init__(self):
        """
        :var self.schedules: set of active schedules managed by this
                             schedule manager
        """
        self.schedules = set()

    def _schedule_done_callback(self, schedule, _):
        self.schedules.remove(schedule)  # this must never give KeyError as

    def add_schedule(self, schedule):
        """
        add a schedule to this manager so to safely cancel it.
        :param schedule: the schedule to add to this manager
        :return: None
        """
        self.schedules.add(schedule)
        schedule.future.add_done_callback(
            partial(self._schedule_done_callback, schedule))

    def every(self, get_coro_or_fut, interval: _timedelta_cls, start_at: datetime,
              count=float('inf'), loop=None):
        """
        executes the given job at (start_at, start_at + interval, start_at + 2 * interval, ....)
        :param get_coro_or_fut: a callable which returns a co-routine or a future
        :param interval: a datetime.timedelta object denoting the interval between
                         consecutive job excutions
        :param start_at: a datetime.datetime object denoting the start time to start
                         this schedule
        :param count: the number of time to execute this job, by default the job will be executed
                      continously
        :param loop: loop: event loop if the given future by get_coro_or_fut is hooked up
                     with a custom event loop
        :return: JobSchedule object so that the user can control the schedule based
                 on it's future
        """
        if interval.total_seconds() < 0:
            raise AScheduleException("error: invalid interval ({} seconds).".format(
                interval.total_seconds()))
        if count <= 0:
            raise AScheduleException("error: invalid count({}).".format(count))
        diff = start_at - datetime.now()
        if round(diff.total_seconds()) < 0:
            start_at += interval * ceil((-diff) / interval)
        intervals = itertools.chain(
            iter([round((start_at - datetime.now()).total_seconds())]),
            map(lambda x: x[1], itertools.takewhile(
                lambda x: x[0] < (count - 1),
                enumerate(itertools.repeat(round(interval.total_seconds()))))))
        schedule = JobSchedule(get_coro_or_fut, intervals, loop=loop)
        self.add_schedule(schedule)
        return schedule

    def once_at(self, get_coro_or_fut, run_at: datetime, strict=False, loop=None):
        """
        executes the job at run_at datetime, if the run_at is in the past then
        it will raise an exception if strict is set to True else it will schedule
        it to execute immediately.
        :param get_coro_or_fut: a callable which returns a co-routine or a future
        :param run_at: datetime object specifying the time at which the job should be
                       executed
        :param strict: if this flag is set to True and if the run_at is in the past
                       the job is scheduled to execute immediately else if the flag
                       is False and the run_at is in the past then it will raise an
                       exception
        :param loop: event loop if the given future by get_coro_or_fut is hooked up
                     with a custom event loop
        :return: JobSchedule object so that the user can control the schedule based
                 on it's future
        """
        diff = run_at - datetime.now()
        if round(diff.total_seconds()) < 0 and strict:
            raise AScheduleException(
                "the given time({given}) is in past. "
                "current time is {now}. ".format(given=run_at, now=datetime.now()))
        intervals = iter([max(round(diff.total_seconds()), 0)])
        schedule = JobSchedule(get_coro_or_fut, intervals, loop=loop)
        self.add_schedule(schedule)
        return schedule

    def cancel(self, schedule: JobSchedule, running_jobs=False):
        """
        cancel's a schedule
        if running_jobs is set to true the currently scheduled jobs
        by this schedule are also cancelled else just the schedule is cancelled.
        :param schedule: the schedule (generated by self.every or self.once_at)
                         that needs to be cancelled.
        :param running_jobs: if this flag is set to true, the currently scheduled jobs
                             by this schedule are also cancelled
        :raises AScheduleException: if the given schedule is not generated by asyncio.every
                            but by another instance of ScheduleManager then
                            this will raise AScheduleException.
                            if the given schedule is already cancelled then too it
                            will raise the exception acting as if it doesn't know
                            about it.
        :return: None
        """
        if schedule not in self.schedules:
            raise AScheduleException("given schedule doesn't belong to this "
                                     "ScheduleManager instance")
        schedule._cancel(running_jobs)

    def shutdown(self):
        for schedule in self.schedules:
            schedule._cancel(running_jobs=True)


class AScheduleException(Exception):
    pass


default_schedule_manager = ScheduleManager()


def cancel(schedule: JobSchedule, running_jobs=False):
    """
    cancel's a schedule
    if running_jobs is set to true the currently scheduled jobs
    by this schedule are also cancelled else just the schedule is cancelled.
    :param schedule: the schedule(generated by aschedule.every or aschedule.once_at)
                     that needs to be cancelled.
    :param running_jobs: if this flag is set to true, the currently scheduled jobs
                         by this schedule are also cancelled
    :raises AScheduleException: if the given schedule is not generated by asyncio.every
                                but by another instance of ScheduleManager then
                                this will raise AScheduleException.
                                if the given schedule is already cancelled then too it
                                will raise the exception acting as if it doesn't know
                                about it.
    """
    default_schedule_manager.cancel(schedule, running_jobs)


def every(job, seconds=0, minutes=0, hours=0, days=0, weeks=0,
          count=float('inf'), timedelta=None, start_at=None, loop=None):
    """
    default execution schedule is (now, now + interval, now + 2 * interval, ....)
    if start_at is provided (start, start + interval, start + 2 * interval, ....)
    if start_at is less than now then the executions starts from
        start + interval * x such that it is greater than now.
        example: now = 2PM, start_at = 1PM, interval = 2 hr, then
                 execution will be 3PM, 5PM, 7PM, ...
    Usage:
        >>> import aschedule
        >>> import asyncio
        >>> loop = asyncio.get_event_loop()
        >>> start = loop.time()
        >>> async def job():
        >>>     print(round(loop.time()), round(loop.time() - start))
        >>> schedule = aschedule.every(job, seconds=5)
        >>> print(round(start), 0)
        >>> loop.run_forever()
        >>>
    :param job: a callable(co-routine function) which returns
                a co-routine or a future or an awaitable
    :param seconds: number of seconds, which will passed onto timedelta
    :param minutes: number of minutes, which will passed onto timedelta
    :param hours: number of hours, which will passed onto timedelta
    :param days: number of days, which will passed onto timedelta
    :param weeks: number of weeks, which will passed onto timedelta
    :param count: number of times to execute the job, by default it will be run infinite number of times.
    :param timedelta: the interval can also be given in the format of datetime.timedelta,
                      then seconds, minutes, hours, days, weeks parameters are ignored.
    :param start_at: datetime at which the schedule starts if not
                     provided schedule starts at (now).
    :param loop: io loop if the provided job is a custom future linked up
                 with a different event loop.
    :return: schedule object, so it could be cancelled at will of the user
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
