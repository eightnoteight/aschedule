# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
import asyncio
import random
from .api import every, once_at, JobSchedule, default_schedule_manager

__all__ = ['every_day', 'every_week', 'every_monday', 'every_tuesday', 'every_wednesday',
           'every_thursday', 'every_friday', 'every_saturday', 'every_sunday',
           'once_at_next_monday', 'once_at_next_tuesday', 'once_at_next_wednesday',
           'once_at_next_thursday', 'once_at_next_friday', 'once_at_next_saturday',
           'once_at_next_sunday', 'every_random_interval']


def every_random_interval(job, interval: timedelta, loop=None):
    """
    executes the job randomly once in the specified interval.
    example:
            run a job every day at random time
            run a job every hour at random time
    :param job: a callable(co-routine function) which returns
                a co-routine or a future or an awaitable
    :param interval: the interval can also be given in the format of datetime.timedelta,
                      then seconds, minutes, hours, days, weeks parameters are ignored.
    :param loop: io loop if the provided job is a custom future linked up
                 with a different event loop.
    :return: schedule object, so it could be cancelled at will of the user by
             aschedule.cancel(schedule)
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    start = loop.time()

    def wait_time_gen():
        count = 0
        while True:
            rand = random.randrange(round(interval.total_seconds()))
            tmp = round(start + interval.total_seconds() * count + rand - loop.time())
            yield tmp
            count += 1

    schedule = JobSchedule(job, wait_time_gen(), loop=loop)
    # add it to default_schedule_manager, so that user can aschedule.cancel it
    default_schedule_manager.add_schedule(schedule)
    return schedule


def every_day(job, loop=None):
    return every(job, timedelta=timedelta(days=1), loop=loop)


def every_week(job, loop=None):
    return every(job, timedelta=timedelta(days=7), loop=loop)

every_monday = lambda job, loop=None: _every_weekday(job, 0, loop=loop)
every_tuesday = lambda job, loop=None: _every_weekday(job, 1, loop=loop)
every_wednesday = lambda job, loop=None: _every_weekday(job, 2, loop=loop)
every_thursday = lambda job, loop=None: _every_weekday(job, 3, loop=loop)
every_friday = lambda job, loop=None: _every_weekday(job, 4, loop=loop)
every_saturday = lambda job, loop=None: _every_weekday(job, 5, loop=loop)
every_sunday = lambda job, loop=None: _every_weekday(job, 6, loop=loop)

once_at_next_monday = lambda job, loop=None: _once_at_weekday(job, 0, loop=loop)
once_at_next_tuesday = lambda job, loop=None: _once_at_weekday(job, 1, loop=loop)
once_at_next_wednesday = lambda job, loop=None: _once_at_weekday(job, 2, loop=loop)
once_at_next_thursday = lambda job, loop=None: _once_at_weekday(job, 3, loop=loop)
once_at_next_friday = lambda job, loop=None: _once_at_weekday(job, 4, loop=loop)
once_at_next_saturday = lambda job, loop=None: _once_at_weekday(job, 5, loop=loop)
once_at_next_sunday = lambda job, loop=None: _once_at_weekday(job, 6, loop=loop)


def _nearest_weekday(weekday):
    return datetime.now() + timedelta(days=(weekday - datetime.now().weekday()) % 7)


def _every_weekday(job, weekday, loop=None):
    return every(job, timedelta=timedelta(days=7), start_at=_nearest_weekday(weekday), loop=loop)


def _once_at_weekday(job, weekday, loop=None):
    return once_at(job, _nearest_weekday(weekday), loop=loop)
