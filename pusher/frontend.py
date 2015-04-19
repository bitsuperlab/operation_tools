#!/usr/bin/env python3
# coding=utf8 sw=1 expandtab ft=python

import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import sleep
from autobahn.wamp import auth
from autobahn.wamp.types import CallResult
from asyncio import coroutine

class MyComponent(ApplicationSession):

    @asyncio.coroutine
    def onJoin(self, details):

        self.received = 0

        def on_height(height, c=None):
            print("height is {}".format(height))

        yield from self.subscribe(on_height, 'btsbots.demo.height')

        res = yield from self.call('btsbots.get_last', 'btsbots.demo.height')
        print("height is {}".format(res))

    def onDisconnect(self):
        asyncio.get_event_loop().stop()

runner = ApplicationRunner(url = u"ws://pusher.btsbots.com:8080/ws", realm = u"realm1")
runner.run(MyComponent)
