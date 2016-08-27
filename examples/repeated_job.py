# -*- coding: utf-8 -*-

import asyncio
import datetime
import aschedule


def main():
    async def job1():
        job1.counter += 1
        if job1.counter == 10:
            future1.cancel()
            return
        print('job1:', job1.counter, datetime.datetime.now())

    async def job2():
        job2.counter += 1
        if job2.counter == 10:
            future2.cancel()
            return
        print('job2:', job2.counter, datetime.datetime.now())

    job1.counter = 0
    job2.counter = -10
    loop = asyncio.get_event_loop()
    future1 = aschedule.every(job1, seconds=1)
    future2 = aschedule.every(job2, seconds=1)
    loop.run_until_complete(asyncio.gather(future1, future2, return_exceptions=True))

if __name__ == '__main__':
    main()
