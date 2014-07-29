## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

#### required:
#### aptitude install python-pip
#### pip install pubnub==3.5.2

import requests
import json
import os

from pprint import pprint

import sys
from Pubnub import Pubnub
import datetime, threading, time

node_type = len(sys.argv) > 1 and sys.argv[1] or 'master'
if node_type == 'master':
  node_type_other = 'slave'
else:
  node_type =  'slave'
  node_type_other = 'master'

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

pprint(config)

### get these key from https://admin.pubnub.com
publish_key = config["publish_key"]
subscribe_key = config["subscribe_key"]
secret_key = config["secret_key"]
cipher_key = config["cipher_key"]
node_state = {node_type:{}, node_type_other:{}}
ssl_on = False

###
auth = ('alt', 'alt') ## user/pass for rpc service
url = "http://localhost:9989/rpc"  ## rpc url

def get_state():
    global node_state
    headers = {'content-type': 'application/json'}
    info = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
    }
    info_res = requests.post(url, data=json.dumps(info), headers=headers, auth=auth)
    info_json = json.loads(vars(info_res)["_content"])
    node_state[node_type]["block_num"]  = info_json["result"]["blockchain_head_block_num"]
    node_state[node_type]["connect_num"]  = info_json["result"]["network_num_connections"]
## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on)

# Asynchronous usage
def callback(message, channel):
    global node_state
    node_state[node_type_other] = message
    print node_state[node_type_other]

def switch_active():
  print 'todo...set rules to switch the active node'

def state_publish():
  global node_state
  global next_call
  get_state()
  print datetime.datetime.now()
  print node_state[node_type]
  next_call = next_call+10
  pubnub.publish(node_type, node_state[node_type])
  switch_active()
  threading.Timer( next_call - time.time(), state_publish).start()

pubnub.subscribe(node_type_other, callback=callback)

next_call = (int (time.time() / 10)) * 10 + 5
state_publish()
