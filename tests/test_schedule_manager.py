# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
from functools import partial
import asyncio
import unittest

import aschedule


class TestScheduleManager(unittest.TestCase):
    _multiprocess_shared_ = True

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.count = 0
        self.schedule = None
        self.schedule_manager = aschedule.ScheduleManager()
        self.cancel_in_seconds = 10

    async def schedule_canceller(self):
        await asyncio.sleep(self.cancel_in_seconds)
        self.schedule_manager.cancel(self.schedule, running_jobs=True)

    async def get_coroutine(self):
        self.count += 1

    async def get_future(self):
        async def task(_future):
            self.count += 1
            _future.set_result(None)
        future = asyncio.Future()
        asyncio.ensure_future(task(future), loop=self.loop)
        return future

    def test_every_param_coroutine(self):
        # scheduled executions 1, 3, 5, 7, 9
        self.schedule = self.schedule_manager.every(self.get_coroutine,
                                                    timedelta(seconds=2),
                                                    datetime.now() + timedelta(seconds=1))
        # will be cancelled at
        self.cancel_in_seconds = 10
        try:
            self.loop.run_until_complete(
                asyncio.gather(self.schedule_canceller(), self.schedule.future))
        except asyncio.CancelledError:
            pass
        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual(5, self.count)

    def test_every_param_future(self):
        # scheduled executions 1, 3, 5, 7, 9
        self.schedule = self.schedule_manager.every(self.get_future,
                                                    timedelta(seconds=2),
                                                    datetime.now() + timedelta(seconds=1))
        # will be cancelled at
        self.cancel_in_seconds = 10
        try:
            self.loop.run_until_complete(
                asyncio.gather(self.schedule_canceller(), self.schedule.future))
        except asyncio.CancelledError:
            pass
        # making sure that all running jobs and the schedules are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual(5, self.count)

    def test_every_param_interval(self):
        # scheduled executions for schedule1, 0, 3, 6, 9
        # scheduled executions for schedule1, 0, 4, 8
        times1, times2 = [], []
        cancel_in_seconds = 10
        start = self.loop.time()

        async def record_times(times):
            times.append(round(self.loop.time() - start))

        async def cancel_schedules():
            await asyncio.sleep(cancel_in_seconds)
            self.schedule_manager.cancel(schedule1, running_jobs=True)
            self.schedule_manager.cancel(schedule2, running_jobs=True)

        schedule1 = self.schedule_manager.every(partial(record_times, times1),
                                                timedelta(seconds=3),
                                                datetime.now())
        schedule2 = self.schedule_manager.every(partial(record_times, times2),
                                                timedelta(seconds=4),
                                                datetime.now())
        try:
            self.loop.run_until_complete(
                asyncio.gather(schedule1.future, schedule2.future, cancel_schedules()))
        except asyncio.CancelledError:
            pass
        # making sure that all running jobs and the schedules are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))

        self.assertEqual([0, 3, 6, 9], times1)
        self.assertEqual([0, 4, 8], times2)

        with self.assertRaises(aschedule.AScheduleException):
            self.schedule_manager.every(self.get_coroutine,
                                        timedelta(seconds=-2),
                                        datetime.now())

    def test_every_param_start_at(self):
        # scheduled executions 2, 4, 6, 8; 1, 4, 7
        times1 = []
        times2 = []
        start = self.loop.time()
        cancel_in_seconds = 9

        async def record_times(times):
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            self.schedule_manager.cancel(schedule1, running_jobs=True)
            self.schedule_manager.cancel(schedule2, running_jobs=True)

        schedule1 = self.schedule_manager.every(partial(record_times, times1),
                                                interval=timedelta(seconds=2),
                                                start_at=datetime.now() + timedelta(seconds=2))
        schedule2 = self.schedule_manager.every(partial(record_times, times2),
                                                interval=timedelta(seconds=3),
                                                start_at=datetime.now() + timedelta(seconds=-2))
        try:
            self.loop.run_until_complete(
                asyncio.gather(schedule2.future, schedule1.future, cancel_schedule()))
        except asyncio.CancelledError:
            pass
        # making sure that all running jobs and the schedules are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))

        self.assertEqual([2, 4, 6, 8], times1)
        self.assertEqual([1, 4, 7], times2)

    def test_every_param_count(self):
        # scheduled executions 0, 2, 4, 6, 8; without cancelling the future
        times = []
        start = self.loop.time()
        cancel_in_seconds = 16

        async def record_times():
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule, running_jobs=True)

        schedule = self.schedule_manager.every(record_times, interval=timedelta(seconds=2),
                                               start_at=datetime.now(), count=5)

        self.loop.run_until_complete(
            asyncio.gather(schedule.future, cancel_schedule()))
        # making sure that all running jobs and the schedules are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))

        self.assertEqual([0, 2, 4, 6, 8], times)
        with self.assertRaises(aschedule.AScheduleException):
            self.schedule_manager.every(self.get_coroutine,
                                        timedelta(seconds=2),
                                        datetime.now(), count=0)
        with self.assertRaises(aschedule.AScheduleException):
            self.schedule_manager.every(self.get_coroutine,
                                        timedelta(seconds=2),
                                        datetime.now(), count=-1)

    def test_every_param_loop(self):
        asyncio.set_event_loop(None)
        # scheduled executions 1, 3, 5, 7, 9
        schedule = self.schedule_manager.every(self.get_coroutine,
                                               timedelta(seconds=2),
                                               datetime.now() + timedelta(seconds=1),
                                               loop=self.loop)
        # will be cancelled at
        cancel_in_seconds = 10

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds, loop=self.loop)
            self.schedule_manager.cancel(schedule, running_jobs=True)

        try:
            self.loop.run_until_complete(
                asyncio.gather(cancel_schedule(), schedule.future, loop=self.loop))
        except asyncio.CancelledError:
            pass

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10, loop=self.loop))
        self.assertEqual(5, self.count)
        asyncio.set_event_loop(self.loop)

    def test_once_at_param_coroutine(self):
        start = self.loop.time()
        times = []
        cancel_in_seconds = 10
        async def record_times():
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule, running_jobs=True)

        schedule = self.schedule_manager.once_at(record_times,
                                                 datetime.now() + timedelta(seconds=5))
        self.loop.run_until_complete(
            asyncio.gather(cancel_schedule(), schedule.future))

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual([5], times)

    def test_once_at_param_future(self):
        start = self.loop.time()
        cancel_in_seconds = 10
        times = []

        def record_times():
            async def task(_future1):
                times.append(round(self.loop.time() - start))
                _future1.set_result(None)
            _future = asyncio.Future()
            asyncio.ensure_future(task(_future))
            return _future

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule, running_jobs=True)

        schedule = self.schedule_manager.once_at(record_times,
                                                 datetime.now() + timedelta(seconds=5))
        self.loop.run_until_complete(
            asyncio.gather(cancel_schedule(), schedule.future))

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual([5], times)

    def test_once_at_param_run_at(self):
        # scheduled executions 5, 7, 3
        start = self.loop.time()
        times = []
        cancel_in_seconds = 10
        async def record_times():
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule1, running_jobs=True)
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule2, running_jobs=True)
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule3, running_jobs=True)

        schedule1 = self.schedule_manager.once_at(record_times,
                                                  datetime.now() + timedelta(seconds=5))
        schedule2 = self.schedule_manager.once_at(record_times,
                                                  datetime.now() + timedelta(seconds=7))
        schedule3 = self.schedule_manager.once_at(record_times,
                                                  datetime.now() + timedelta(seconds=3))
        self.loop.run_until_complete(
            asyncio.gather(cancel_schedule(), schedule1.future,
                           schedule2.future, schedule3.future))

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual([3, 5, 7], times)

    def test_once_at_param_strict(self):
        # scheduled executions 0
        start = self.loop.time()
        times = []
        cancel_in_seconds = 2
        async def record_times():
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule, running_jobs=True)

        with self.assertRaises(aschedule.AScheduleException):
            self.schedule_manager.once_at(record_times,
                                          datetime.now() + timedelta(seconds=-10),
                                          strict=True)

        schedule = self.schedule_manager.once_at(record_times,
                                                 datetime.now() + timedelta(seconds=-10),
                                                 strict=False)
        self.loop.run_until_complete(asyncio.gather(cancel_schedule(), schedule.future))

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual([0], times)

    def test_once_at_param_loop(self):
        asyncio.set_event_loop(None)
        start = self.loop.time()
        times = []
        cancel_in_seconds = 10
        async def record_times():
            times.append(round(self.loop.time() - start))

        async def cancel_schedule():
            await asyncio.sleep(cancel_in_seconds, loop=self.loop)
            # should report an error that the given schedule doesn't belong to this schedule manager
            # as the schedule is completed before this arises
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule, running_jobs=True)

        schedule = self.schedule_manager.once_at(record_times,
                                                 datetime.now() + timedelta(seconds=5),
                                                 loop=self.loop)
        self.loop.run_until_complete(
            asyncio.gather(cancel_schedule(), schedule.future, loop=self.loop))

        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10, loop=self.loop))
        self.assertEqual([5], times)
        asyncio.set_event_loop(self.loop)

    def test_cancel(self):
        start = self.loop.time()
        times = []
        cancel_in_seconds1 = 5
        cancel_in_seconds2 = 5

        async def record_times():
            await asyncio.sleep(4)
            times.append(round(self.loop.time() - start))

        async def cancel_schedule1():
            await asyncio.sleep(cancel_in_seconds1)
            # should report an error that the given schedule doesn't belong to this
            # schedule manager as the schedule is created by a new schedule manager instance
            with self.assertRaises(aschedule.AScheduleException):
                self.schedule_manager.cancel(schedule1, running_jobs=True)
            schedule1._cancel(running_jobs=True)

        async def cancel_schedule2():
            await asyncio.sleep(cancel_in_seconds2)
            # should report an error that the given schedule doesn't belong to this
            # schedule manager as the schedule is created by a new schedule manager instance
            self.schedule_manager.cancel(schedule2, running_jobs=True)

        schedule1 = aschedule.ScheduleManager().every(record_times,
                                                      timedelta(seconds=2), datetime.now())
        schedule2 = self.schedule_manager.every(record_times,
                                                timedelta(seconds=3), datetime.now())
        # cancellation of schedule1 will give out CancelledError
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(
                asyncio.gather(cancel_schedule1(), cancel_schedule2(),
                               schedule1.future, schedule2.future))
        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))

        self.assertEqual([4, 4], times)

    def test_shutdown(self):
        start = self.loop.time()
        times = []

        async def record_times():
            times.append(round(self.loop.time() - start))

        schedules = [
            self.schedule_manager.every(record_times,
                                        timedelta(seconds=5),
                                        datetime.now() + timedelta(seconds=x))
            for x in range(0, 5, 2)
        ]
        schedules.append(
            self.schedule_manager.once_at(record_times,
                                          datetime.now() + timedelta(seconds=3))
        )
        async def cancel_schedules():
            await asyncio.sleep(11)
            self.schedule_manager.shutdown()
        futures = [schedule.future for schedule in schedules]
        try:
            self.loop.run_until_complete(asyncio.gather(*(futures + [cancel_schedules()])))
        except asyncio.CancelledError:
            pass
        # making sure that all running jobs and the schedule are cancelled
        self.loop.run_until_complete(asyncio.sleep(10))
        self.assertEqual([0, 2, 3, 4, 5, 7, 9, 10], times)

    def tearDown(self):
        asyncio.set_event_loop(self.loop)
