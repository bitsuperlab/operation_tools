## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

#### required:
#### aptitude install python-pip
#### pip install pubnub==3.5.2

import json
from Pubnub import Pubnub
import datetime, threading, time

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

## -----------------------------------------------------------------------
## function about pubnub
## -----------------------------------------------------------------------
# Asynchronous usage
def callback(message, channel):
    print datetime.datetime.now(), 'receive', message

def error(message):
    print("ERROR : " + str(message))

## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
publish_key = config["pubnub_auth"]["publish_key"]
subscribe_key = config["pubnub_auth"]["subscribe_key"]
secret_key = config["pubnub_auth"]["secret_key"]
cipher_key = config["pubnub_auth"]["cipher_key"]
ssl_on = False
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
    secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)

pubnub.subscribe("blockchain_list_blocks", callback=callback, error=error)
pubnub.subscribe("blockchain_list_delegate", callback=callback, error=error)
