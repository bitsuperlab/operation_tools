## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

#### required:
#### aptitude install python-pip
#### pip install pubnub==3.5.2

import json
import os
from Pubnub import Pubnub
import datetime, threading, time

from pprint import pprint

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

## -----------------------------------------------------------------------
## function about pubnub
## -----------------------------------------------------------------------
## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
publish_key = config["pubnub_auth"]["publish_key"]
subscribe_key = config["pubnub_auth"]["subscribe_key"]
secret_key = config["pubnub_auth"]["secret_key"]
cipher_key = config["pubnub_auth"]["cipher_key"]
channel1 = "blockchain_list_blocks"
channel2 = "blockchain_list_delegate"
ssl_on = False
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
    secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)


# Synchronous usage
def who_is_here_sync():
    os.system("/usr/bin/clear")
    print "Channel: " + channel1
    pprint(pubnub.here_now(channel1))
    print
    print "Channel: " + channel2
    pprint(pubnub.here_now(channel2))
    threading.Timer( 10, who_is_here_sync).start()

# Asynchronous usage
def callback1(message):
    print "Channel: " + channel1
    pprint(message)
    print

def callback2(message):
    print "Channel: " + channel1
    pprint(message)
    print

def who_is_here():
    os.system("/usr/bin/clear")
    pubnub.here_now(channel1, callback=callback1, error=callback1)
    pubnub.here_now(channel2, callback=callback2, error=callback2)

    threading.Timer( 10, who_is_here).start()



who_is_here_sync()
