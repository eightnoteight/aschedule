# -*- coding: utf-8 -*-

import unittest
import asyncio
import datetime

import aschedule


class TestEveryFunction(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.schedule = None
        self.count = 0
        self.count_max = 5
        self.interval_in_seconds = 2

    async def sample_job(self):
        self.count += 1
        if self.count == self.count_max:
            self.schedule.cancel()

    def test_seconds(self):
        self.schedule = aschedule.every(self.sample_job,
                                        seconds=self.interval_in_seconds)
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.schedule.future)
        end_time = self.loop.time()

        self.assertAlmostEqual(start_time + self.interval_in_seconds * (self.count_max - 1),
                               end_time, delta=0.1)

    def test_start_at_now(self):
        self.schedule = aschedule.every(self.sample_job,
                                        seconds=self.interval_in_seconds,
                                        start_at=datetime.datetime.now())
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.schedule.future)
        end_time = self.loop.time()

        # error if: given start_at, the job doesn't execute 5 times within 8 seconds.
        self.assertAlmostEqual(start_time +
                               self.interval_in_seconds * (self.count_max - 1),
                               end_time, delta=0.1)

    # should behave the same as test_start_at
    def test_start_at_after(self):
        after_in_seconds = 10
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=after_in_seconds)

        self.schedule = aschedule.every(self.sample_job,
                                        seconds=self.interval_in_seconds,
                                        start_at=start_at)
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.schedule.future)
        end_time = self.loop.time()

        # error if: given start_at, the job doesn't execute 5 times within 8 seconds.
        expected_end_time = (start_time +
                             self.interval_in_seconds * (self.count_max - 1) +
                             after_in_seconds)
        self.assertAlmostEqual(expected_end_time,
                               end_time, delta=0.1)

    def test_timedelta(self):
        self.schedule = aschedule.every(self.sample_job,
                                        timedelta=datetime.timedelta(
                                            seconds=self.interval_in_seconds))
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.schedule.future)
        end_time = self.loop.time()

        self.assertAlmostEqual(start_time + self.interval_in_seconds * (self.count_max - 1),
                               end_time, delta=0.1)

    def test_bad_options(self):
        with self.assertRaises(aschedule.api.AScheduleException):
            aschedule.every(self.sample_job, timedelta=datetime.timedelta(seconds=0))
        with self.assertRaises(aschedule.api.AScheduleException):
            aschedule.every(self.sample_job, timedelta=datetime.timedelta(minutes=-10))

    def test_loop(self):
        asyncio.set_event_loop(None)
        self.schedule = aschedule.every(self.sample_job,
                                        seconds=self.interval_in_seconds, loop=self.loop)
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.schedule.future)
        end_time = self.loop.time()

        self.assertAlmostEqual(start_time + self.interval_in_seconds * (self.count_max - 1),
                               end_time, delta=0.1)

        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop = None
