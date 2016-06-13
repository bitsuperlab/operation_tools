#!/usr/bin/env python3
# coding=utf8 sw=1 expandtab ft=python

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import sleep
from autobahn.wamp import auth
from autobahn.wamp.types import CallResult
from asyncio import coroutine

import json
from bts import BTS

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
      while True:
        try:
          block_info = client.request("get_info", []).json()["result"]
          height = int(block_info["blockchain_head_block_num"])
          self.mypublish(u'btsbots.demo.height', height)
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

