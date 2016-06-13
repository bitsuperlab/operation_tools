#!/usr/bin/env python3
# coding=utf8 sw=1 expandtab ft=python

import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import sleep
from autobahn.wamp import auth
from autobahn.wamp.types import CallResult
from asyncio import coroutine

import json

config_file = open("config.json")
config = json.load(config_file)
config_file.close()

config_wamp = config["wamp_client"]

class MyComponent(ApplicationSession):

    @asyncio.coroutine
    def onJoin(self, details):
        quote = "CNY"
        base = "BTS"
        def print_order_book(order_book):
          print("order_bid:")
          for order in order_book["bid"]:
            print(order["price"], order["volume"], order["balance"])
          print("order_ask:")
          for order in order_book["ask"]:
            print(order["price"], order["volume"], order["balance"])
        def on_order_book(order_book, c=None):
          print_order_book(order_book)

        yield from self.subscribe(on_order_book, 'btsbots.demo.order_book_%s_%s'%(quote,base))

        res = yield from self.call('btsbots.get_last', 'btsbots.demo.order_book_%s_%s'%(quote,base))
        print_order_book(res)

    def onDisconnect(self):
        asyncio.get_event_loop().stop()

runner = ApplicationRunner(url = config_wamp["url"], realm = config_wamp["realm"])
runner.run(MyComponent)
