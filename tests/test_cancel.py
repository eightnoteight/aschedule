# -*- coding: utf-8 -*-

import unittest
import asyncio

import aschedule


class TestCancel(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.count = 0
        self.schedule_future = None

    async def sample_job(self):
        await asyncio.sleep(10)
        self.count += 1
        aschedule.cancel(self.schedule_future)

    def test_cancel_by_sleep(self):
        self.schedule_future = aschedule.every(self.sample_job, seconds=2)
        self.loop.run_until_complete(asyncio.sleep(15))

        # just to makes sure that the jobs are indeed cancelled.
        self.loop.run_until_complete(asyncio.sleep(20))
        self.assertEqual(1, self.count, "more than 1 job got executed")

    def test_cancel(self):
        self.schedule_future = aschedule.every(self.sample_job, seconds=2)
        try:
            self.loop.run_until_complete(self.schedule_future)
        except asyncio.CancelledError:
            pass

        # just to makes sure that the jobs are indeed cancelled.
        self.loop.run_until_complete(asyncio.sleep(20))
        self.assertEqual(1, self.count, "more than 1 job got executed")

    def tearDown(self):
        self.loop = None
        self.count = 0
        self.schedule_future = None


if __name__ == '__main__':
    unittest.main()
