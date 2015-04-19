#!/usr/bin/env python3
# coding=utf8 sw=1 expandtab ft=python

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import sleep
from autobahn.wamp import auth
from autobahn.wamp.types import CallResult
from asyncio import coroutine

import json
from bts import BTS
from pprint import pprint

config_file = open("config.json")
config = json.load(config_file)
config_file.close()

config_wamp = config["wamp_client"]
config_bts = config["bts_client"]

client = BTS(config_bts["user"],config_bts["password"],config_bts["host"],config_bts["port"])

class MyComponent(ApplicationSession):
   IsConnect = True

   def onConnect(self):
      self.IsConnect = True
      self.join(self.config.realm, [u"wampcra"], config_wamp["user"])

   def onChallenge(self, challenge):
      key = config_wamp["password"].encode('utf8')
      signature = auth.compute_wcs(key, challenge.extra['challenge'].encode('utf8'))
      return signature.decode('ascii')

   def mypublish(self, topic, event):
     try:
       if self.IsConnect:
         self.publish(topic, event, c=topic)
       else:
         print("lost connect")
     except Exception as e:
       print("can't connect to wamp server")

   @coroutine
   def onJoin(self, details):
      print("session ready")

      def get_order_book(quote,base):
        quote_precision = client.get_precision(quote)
        base_precision = client.get_precision(base)
        order_book = {"bid":[],"ask":[],"cover":[]}
        order_book_json = client.request("blockchain_market_order_book", [quote,base]).json()["result"]
        for order in order_book_json[0]:
          order_info = {}
          price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          order_info["price"] =  price
          order_info["balance"] = order["state"]["balance"] / quote_precision
          order_info["volume"] = order_info["balance"] / price
          order_book["bid"].append(order_info)
        for order in order_book_json[1]:
          order_type = order["type"]
          price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          order_info = {}
          order_info["price"] =  price
          if order["type"] == "ask_order":
            order_info["volume"] = order["state"]["balance"] / base_precision
            order_info["balance"] = order_info["volume"] * price
            order_book["ask"].append(order_info)
          #elif order["type"] == "cover_order":
          #  order_info["balance"] = order["state"]["balance"] / quote_precision
          #  order_info["volume"] = order_info["balance"] / price
          #  order_cover.insert(0,order_info)
        #order_short = client.request("blockchain_market_list_shorts", [quote]).json()["result"]
        #for order in order_short:
        #  price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
        #  order_info["price"] =  price
        #  order_info["volume_bts"] = order["state"]["balance"] / base_precision
        #  order_info["volume_bta"] = order_info["volume_bts"] * ave_price /2
        return order_book

      order_book_last = {}
      while True:
        try:
          quote = "CNY"
          base = "BTS"
          order_book = get_order_book(quote,base)
          if (order_book_last != order_book):
            order_book_last = order_book
            #print("update now")
            #pprint(order_book)
            self.mypublish(u'btsbots.demo.order_book_%s_%s'%(quote,base), order_book)
          #else:
            #print("don't need update")
        except Exception as e:
          print(e)
        yield from sleep(10)

   def onLeave(self, details):
      print("onLeave: {}".format(details))
      self.disconnect()

   def onDisconnect(self):
      self.IsConnect = False
      print("onDisconnect: {}".format(details))

runner = ApplicationRunner(url = config_wamp["url"], realm = config_wamp["realm"])
runner.run(MyComponent)

