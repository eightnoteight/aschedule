# -*- coding: utf-8 -*-
from unittest.mock import patch
from datetime import timedelta
import unittest
import asyncio

import aschedule


class TestingExt(unittest.TestCase):
    _multiprocess_shared_ = True

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    async def get_coro(self):
        pass

    def test_every_day(self):
        self.every_patcher = patch('aschedule.ext.every')
        self.addCleanup(self.every_patcher.stop)
        self.every_mock = self.every_patcher.start()
        from aschedule.ext import every_day

        schedule1 = every_day(self.get_coro)
        self.every_mock.assert_called_with(self.get_coro, timedelta=timedelta(days=1), loop=None)
        schedule2 = every_day(self.get_coro, loop=self.loop)
        self.every_mock.assert_called_with(self.get_coro, timedelta=timedelta(days=1), loop=self.loop)
        self.loop.run_until_complete(asyncio.sleep(1))
        schedule1._cancel(running_jobs=True)
        schedule2._cancel(running_jobs=True)
        self.loop.run_until_complete(asyncio.sleep(1))
        self.assertEqual(2, self.every_mock.call_count)

    def test_every_week(self):
        self.every_patcher = patch('aschedule.ext.every')
        self.addCleanup(self.every_patcher.stop)
        self.every_mock = self.every_patcher.start()
        from aschedule.ext import every_week

        schedule1 = every_week(self.get_coro)
        self.every_mock.assert_called_with(self.get_coro, timedelta=timedelta(days=7), loop=None)
        schedule2 = every_week(self.get_coro, loop=self.loop)
        self.every_mock.assert_called_with(self.get_coro, timedelta=timedelta(days=7), loop=self.loop)
        self.loop.run_until_complete(asyncio.sleep(1))
        schedule1._cancel(running_jobs=True)
        schedule2._cancel(running_jobs=True)
        self.loop.run_until_complete(asyncio.sleep(1))
        self.assertEqual(2, self.every_mock.call_count)

    def test_every_random_interval(self):
        from aschedule.ext import every_random_interval

        # scheduled executions: randrange(0, 5), randrange(5, 10), randrange(10, 15)
        times = []
        start = self.loop.time()
        cancel_in_seconds = 16
        # set the seed to avoid a scheduled execution on 16th second.
        __import__('random').seed(38042)
        async def record_times():
            times.append(round(self.loop.time() - start))
        schedule = every_random_interval(record_times, timedelta(seconds=5))

        async def schedule_canceller():
            await asyncio.sleep(cancel_in_seconds)
            aschedule.cancel(schedule)

        try:
            self.loop.run_until_complete(
                asyncio.gather(schedule_canceller(), schedule.future))
        except asyncio.CancelledError:
            pass

        self.assertEqual(3, len(times))
        for i, x in enumerate(times):
            self.assertTrue(i * 5 <= x < (i + 1) * 5)

    def tearDown(self):
        asyncio.set_event_loop(self.loop)
