# -*- coding: utf-8 -*-

import unittest
import asyncio
import datetime

import aschedule

_count = 0


class TestEveryFunction(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.future = None

    async def sample_job(self):
        self.count += 1
        if self.count == self.count_max:
            self.future.cancel()

    def test_seconds(self):
        self.count = 0
        self.count_max = 5
        interval_in_seconds = 2

        self.future = aschedule.every(self.sample_job,
                                      seconds=interval_in_seconds)
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.future)
        end_time = self.loop.time()

        self.assertAlmostEqual(start_time + interval_in_seconds * self.count_max,
                               end_time, delta=0.1)

    def test_start_at(self):
        self.count = 0
        self.count_max = 5
        interval_in_seconds = 2

        self.future = aschedule.every(self.sample_job,
                                      seconds=interval_in_seconds,
                                      start_at=datetime.datetime.now())
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.future)
        end_time = self.loop.time()

        # error if: given start_at, the job doesn't execute 5 times within 8 seconds.
        self.assertAlmostEqual(start_time + interval_in_seconds * self.count_max - interval_in_seconds,
                               end_time, delta=0.1)

    def test_loop(self):
        asyncio.set_event_loop(None)

        self.count = 0
        self.count_max = 5
        interval_in_seconds = 2

        self.future = aschedule.every(self.sample_job,
                                      seconds=interval_in_seconds, loop=self.loop)
        start_time = self.loop.time()
        # error if: the future doesn't exit or produces other than CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(future=self.future)
        end_time = self.loop.time()

        self.assertAlmostEqual(start_time + interval_in_seconds * self.count_max,
                               end_time, delta=0.1)

        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop = None
