#!/usr/bin/env python3
# coding=utf8 sw=1 expandtab ft=python

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from asyncio import sleep
from autobahn.wamp import auth
from autobahn.wamp.types import CallResult
from asyncio import coroutine

USER = u'demo'
PASSWORDS = u'demo'

from bts import BTS
rpc_user, rpc_password, rpc_host, rpc_port = ["alt","alt","localhost",9988]
client = BTS(rpc_user, rpc_password, rpc_host, rpc_port)


class MyComponent(ApplicationSession):
   IsConnect = True

   def onConnect(self):
      self.IsConnect = True
      self.join(self.config.realm, [u"wampcra"], USER)

   def onChallenge(self, challenge):
      key = PASSWORDS.encode('utf8')
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

runner = ApplicationRunner(url = u"ws://btsbots.com:8080/ws", realm = u"realm1")
runner.run(MyComponent)

