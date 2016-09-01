# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
import unittest
import asyncio

import aschedule


class TestCancel(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.count = 0
        self.schedule = None
        self.schedule_manager = None

    async def sample_job1(self):
        await asyncio.sleep(10)
        self.count += 1
        aschedule.cancel(self.schedule, running_jobs=True)

    async def sample_job2(self):
        await asyncio.sleep(10)
        self.count += 1
        try:
            aschedule.cancel(self.schedule, running_jobs=False)
        except aschedule.AScheduleException:
            pass

    def test_cancel_by_sleep_including_jobs(self):
        self.schedule = aschedule.every(self.sample_job1, seconds=2)
        self.loop.run_until_complete(asyncio.sleep(15))

        # just to makes sure that the jobs are indeed cancelled.
        self.loop.run_until_complete(asyncio.sleep(20))
        self.assertEqual(1, self.count, "more than 1 job got executed")

    def test_cancel_including_jobs(self):
        self.cancel_running_jobs = True
        self.schedule = aschedule.every(self.sample_job1, seconds=2)
        try:
            self.loop.run_until_complete(self.schedule.future)
        except asyncio.CancelledError:
            pass

        # just to makes sure that the jobs are indeed cancelled.
        self.loop.run_until_complete(asyncio.sleep(20))
        self.assertEqual(1, self.count, "more than 1 job got executed")

    def test_cancel_just_schedule(self):
        self.cancel_running_jobs = False
        self.schedule = aschedule.every(self.sample_job2, seconds=2)
        try:
            self.loop.run_until_complete(self.schedule.future)
        except asyncio.CancelledError:
            pass

        self.loop.run_until_complete(asyncio.sleep(20))
        self.assertEqual(5, self.count)

    async def _dummy_job(self):
        self.schedule_manager.cancel(self.schedule, running_jobs=True)

    def test_unknown_cancel(self):
        self.schedule_manager = aschedule.ScheduleManager()
        self.schedule = self.schedule_manager.every(self._dummy_job, timedelta(seconds=1), datetime.now())
        with self.assertRaises(aschedule.AScheduleException):
            aschedule.cancel(self.schedule)
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(self.schedule.future)


if __name__ == '__main__':
    unittest.main()
