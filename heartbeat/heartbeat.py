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

print "node typ is " + node_type

config_data = open('config.json')
config = json.load(config_data)
config_data.close()
node_state = {'master':{'connect_num':100,'block_num':100000000}, 'slave':{'connect_num':0,'block_num':0}}

#pprint(config)

## -----------------------------------------------------------------------
## function about bts rpc
## -----------------------------------------------------------------------
auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
url = config["bts_rpc"]["url"]

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
    node_state[node_type]["wallet_next_block_production_timestamp"] = info_json["result"]["wallet_next_block_production_timestamp"]

def is_active():
    global node_state
    return node_state[node_type]["wallet_next_block_production_timestamp"] != None

# unlock the delegate first in nodes
def set_delegate_production(enable):
    if is_active() == enable:
        return
    headers = {'content-type': 'application/json'}
    set_delegate = {
        "method": "wallet_delegate_set_block_production",
        "params": ["ALL", enable],
        "jsonrpc": "2.0",
        "id": 1
        }

    set_res = requests.post(url, data=json.dumps(set_delegate), headers=headers, auth=auth)
    set_json = json.loads(vars(set_res)["_content"])
    print 'set_delegate_production', enable, 'result:',set_json

def switch_active(type):
    #print "switch active to", type
    if node_type ==  type:
        set_delegate_production(True)
    else:
        set_delegate_production(False)

def select_active():
    # TODO check the next bock production timestamp of antoher node, require enough time (at least 2 min) for switch
    if node_state["master"]["connect_num"] < 20 and node_state["slave"]["connect_num"] > 22:
        switch_active("slave")
    elif node_state["master"]["block_num"] + 2 < node_state["slave"]["block_num"]:
        switch_active("slave")
    else:
        switch_active("master")



## -----------------------------------------------------------------------
## function about pubnub
## -----------------------------------------------------------------------
# Asynchronous usage
def callback(message, channel):
    global node_state
    node_state[node_type_other] = message
    print datetime.datetime.now(), 'receive', node_state[node_type_other]

def error(message):
    print("ERROR : " + str(message))

def state_publish():
    global node_state
    global next_call
    get_state()
    print datetime.datetime.now(), 'publish', node_state[node_type]
    pubnub.publish(node_type, node_state[node_type])
    select_active()

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

pubnub.subscribe(node_type_other, callback=callback, error=error)

next_call = (int (time.time() / 10)) * 10 + 5
state_publish()
