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
import sys

from Pubnub import Pubnub
import datetime, threading, time

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

last_block = 0

## -----------------------------------------------------------------------
## function about bts rpc
## -----------------------------------------------------------------------
auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
url = config["bts_rpc"]["url"]

def blockchain_list_blocks():
    global last_block
    headers = {'content-type': 'application/json'}
    request = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
        }
    responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)

    try:
      info_json = json.loads(vars(responce)["_content"])
    except ValueError, e:
      print "Can't connect to rpc server"
      sys.exit()
      return None

    ## 2 blocks delay, avoid fork
    block_header_num = info_json["result"]["blockchain_head_block_num"] - 2
    if last_block == block_header_num:
        return None
    last_block = block_header_num
    request = {
        "method": "execute_command_line",
        "params": ["blockchain_list_blocks " +  str(block_header_num) + " 2"],
        "jsonrpc": "2.0",
        "id": 1
        }
    responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
    command_output = json.loads(vars(responce)["_content"])["result"]
    pos = 0
    ### ignore first 3 lines
    for x in range(0,3):
       pos = command_output.find("\n",pos+1)
    while True:
       posnext = command_output.find("\n", pos+1)
       if posnext != -1:
          print "publish:" + command_output[pos+1:posnext]
          pubnub.publish("blockchain_list_blocks", command_output[pos+1:posnext])
          pos = posnext
       else:
          break
    return


## -----------------------------------------------------------------------
## function about pubnub
## -----------------------------------------------------------------------
def state_publish():
    global next_call
    blockchain_list_blocks()

    next_call = next_call + 10
    threading.Timer( next_call - time.time(), state_publish).start()

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

next_call = (int (time.time() / 10)) * 10 - 5
state_publish()
