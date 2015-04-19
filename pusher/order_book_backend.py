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

      asset_info = {}
      def get_asset_info():
        asset_list_all = ["BTS", "KRW", "BTC", "SILVER", "GOLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]
        asset_list_all.extend(["BOTSCNY", "BTSBOTS.PLS", "BDR.AAPL"])
        for asset in asset_list_all:
          asset_info[asset] = client.request("blockchain_get_asset", [asset]).json()["result"]
          if asset == "BTS":
            asset_info[asset]["current_feed_price"] = 1
          elif asset_info[asset]["id"] <= 22:
            market_status = client.request("blockchain_market_status", [asset, "BTS"]).json()["result"]
            asset_info[asset]["current_feed_price"] = float(market_status["current_feed_price"])
          else:
            asset_info[asset]["current_feed_price"] = None

      get_asset_info()

      def get_order_book(quote,base):
        short_enable = False
        quote_precision = asset_info[quote]["precision"]
        base_precision = asset_info[base]["precision"]

        if asset_info[base]["id"] == 0 and asset_info[quote]["id"] <= 22:
          short_enable = True

        order_book = {"bid":[],"ask":[],"cover":[]}
        order_book_json = client.request("blockchain_market_order_book", [quote,base]).json()["result"]
        for order in order_book_json[0]:
          order_info = {}
          price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          order_info["price"] =  price
          balance = order["state"]["balance"] / quote_precision
          order_info["volume"] = balance / price
          order_book["bid"].append(order_info)
        for order in order_book_json[1]:
          order_type = order["type"]
          price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          order_info = {}
          order_info["price"] =  price
          if order["type"] == "ask_order":
            order_info["volume"] = order["state"]["balance"] / base_precision
            order_book["ask"].append(order_info)
          #elif order["type"] == "cover_order":
          #  order_info["balance"] = order["state"]["balance"] / quote_precision
          #  order_info["volume"] = order_info["balance"] / price
          #  order_cover.insert(0,order_info)
        if short_enable == True:
          feed_price = asset_info[quote]["current_feed_price"]
          order_short = client.request("blockchain_market_list_shorts", [quote]).json()["result"]
          volume_at_feed_price = 0
          for order in order_short:
            volume = order["state"]["balance"] / base_precision / 2
            price_limit = order["state"]["limit_price"]
            if price_limit == None or float(price_limit["ratio"]) * base_precision/quote_precision >= feed_price:
              volume_at_feed_price += volume
            else:
              order_info = {}
              order_info["price"] = float(price_limit["ratio"]) * base_precision/quote_precision
              order_info["volume"] = volume
              order_book["bid"].append(order_info)
          if volume_at_feed_price != 0:
              order_info = {}
              order_info["volume"] = volume_at_feed_price
              order_info["price"] = feed_price
              order_book["bid"].append(order_info)
          order_book["bid"] = sorted(order_book["bid"], key=lambda item:item["price"], reverse=True)[-10:]
        return order_book

      quote = "CNY"
      base = "BTS"
      order_book_last = {}
      while True:
        try:
          order_book = get_order_book(quote,base)
          if (order_book_last != order_book):
            order_book_last = order_book
            #print("update now")
            pprint(order_book)
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

