# -*- coding: utf-8 -*-

import unittest
import asyncio
from datetime import datetime, timedelta

import aschedule


class TestOnceAt(unittest.TestCase):
    _multiprocess_shared_ = True

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.future = None
        self.trigger_time = 0
        self.count = 0
        self.schedule = None

    async def sample_job(self):
        self.trigger_time = self.loop.time()
        if self.count >= 1:
            self.schedule._cancel(running_jobs=True)
        self.count += 1

    def _test_util(self, td, delay):
        scheduled_time = self.loop.time()
        self.schedule = aschedule.once_at(self.sample_job,
                                          datetime.now() + td)
        self.loop.run_until_complete(self.schedule.future)
        expected_time = scheduled_time + delay
        self.assertAlmostEqual(expected_time, self.trigger_time, delta=0.1)

    def test_once_at_after(self):
        self._test_util(timedelta(seconds=10), 10)

    def test_once_at_now(self):
        self._test_util(timedelta(seconds=0), 0)

    def test_once_at_before(self):
        self._test_util(timedelta(minutes=-10), 0)

    def tearDown(self):
        self.loop = None
        self.trigger_time = 0
        self.count = 0
