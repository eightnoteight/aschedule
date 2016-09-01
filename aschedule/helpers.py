# -*- coding: utf-8 -*-
import asyncio
import itertools


class WaitAsyncIterator(object):
    def __init__(self, wait_times, results=None, loop=None):
        self.wait_times = wait_times
        self.results = results
        if self.results is None:
            self.results = itertools.repeat(None)
        self.loop = loop

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await asyncio.sleep(next(self.wait_times),
                                       result=next(self.results, None),
                                       loop=self.loop)
        except StopIteration:
            raise StopAsyncIteration
