#!/usr/bin/env python
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
from pprint import pprint

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

last_block = 0
delegate_dict = {}
delegate_dict_old = {}

## -----------------------------------------------------------------------
## function about bts rpc
## -----------------------------------------------------------------------
auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
url = config["bts_rpc"]["url"]

def blockchain_list_delegate():
    global delegate_dict, delegate_dict_old
    headers = {'content-type': 'application/json'}
    request = {
        "method": "blockchain_list_delegates",
        "params": [0, 150],
        "jsonrpc": "2.0",
        "id": 1
        }
    try:
      responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
      delegate_lists_json = json.loads(vars(responce)["_content"])["result"]
    except:
      print "Can't connect to rpc server"
      return

    for account_info in delegate_lists_json:
      delegate_info = account_info["delegate_info"]

      id = account_info["id"]
      name = account_info["name"]
      approval = float('%.2f'% (delegate_info["votes_for"]/2000000000000.0))
      produced = delegate_info["blocks_produced"]
      missed = delegate_info["blocks_missed"]
      if produced+missed == 0:
        reliability = "N/A"
      else:
        reliability = float('%.2f'%(produced*100.0/(produced+missed)))
      pay_rate = delegate_info["pay_rate"]
      pay_balance = float('%.2f'%(delegate_info["pay_balance"]/100000.0))
      last_block = delegate_info["last_block_num_produced"]

      delegate_dict[id] = [id, name, approval, produced, missed, reliability, pay_rate, pay_balance, last_block]
      if delegate_dict_old.get(id) != delegate_dict[id]:
         pubnub.publish("blockchain_list_delegate", delegate_dict[id])
         print "publish", delegate_dict[id]
         delegate_dict_old[id] = delegate_dict[id]

def blockchain_list_blocks():
    global last_block
    headers = {'content-type': 'application/json'}
    request = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
        }

    try:
      responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
      info_json = json.loads(vars(responce)["_content"])
    except:
      print "Can't connect to rpc server"
      return None

    ## 2 blocks delay, avoid fork
    block_header_num = info_json["result"]["blockchain_head_block_num"] - 1
    if last_block == 0:
       last_block = block_header_num - 1;
    if last_block == block_header_num:
        return None
    request = {
        "method": "execute_command_line",
        "params": ["blockchain_list_blocks " +  str(last_block) + " " + str(block_header_num - last_block + 1)],
        "jsonrpc": "2.0",
        "id": 1
        }
    try:
      responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
      command_output = json.loads(vars(responce)["_content"])["result"]
    except:
      print "Can't connect to rpc server"
      return None
    pos = 0
    ### ignore first 3 lines
    for x in range(0,3):
       pos = command_output.find("\n",pos+1)
    while True:
       posnext = command_output.find("\n", pos+1)
       if posnext != -1:
          print "publish:" + command_output[pos+1:posnext]
          block_info = command_output[pos+1:posnext].replace(" BTSX","BTSX ").split()
          pos = posnext
          pubnub.publish("blockchain_list_blocks", block_info)
          if block_info[0] != "MISSED":
            blockchain_list_transactions(block_info[0], block_info[1])
          #print(block_info[2])
       else:
          break
    last_block = block_header_num
    return

def blockchain_list_transactions(blockID, time_stamp):
    headers = {'content-type': 'application/json'}
    request = {
        "method": "blockchain_get_block_transactions",
        "params": [blockID],
        "jsonrpc": "2.0",
        "id": 1
        }
    try:
      responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
      info_json = json.loads(vars(responce)["_content"])
    except:
      print "Can't connect to rpc server"
      return None
    transaction_lists = json.loads(vars(responce)["_content"])["result"]
    for transaction in transaction_lists:
       transaction_info = {};
       withdraws = deposits = fees = 0.0
       register_name = ""
       type = "transfer"
       id = transaction[0][0:8]
       transaction_json = transaction[1]
       location = str(transaction_json["chain_location"]["block_num"]) + '.' + str(transaction_json["chain_location"]["trx_num"])

       for operation in transaction_json["trx"]["operations"]:
         if operation["type"] == "register_account_op_type":
           type = "register"
           register_name = operation["data"]["name"]
         elif operation["type"] == "create_asset_op_type":
           type = "asset"
           register_name = operation["data"]["symbol"]
         elif operation["type"] == "withdraw_op_type":
           withdraws = withdraws + operation["data"]["amount"]
         elif operation["type"] == "withdraw_pay_op_type":
           withdraws = withdraws + operation["data"]["amount"]
         elif operation["type"] == "deposit_op_type":
           deposits = deposits + operation["data"]["amount"]

       withdraws = float('%.2f '% (withdraws / 100000.0))
       deposits = float('%.2f'%(deposits / 100000.0))
       fees = float('%.2f'%(withdraws - deposits))

       transaction_info = [location, time_stamp, type, register_name, deposits, fees ,id]
       pubnub.publish("blockchain_list_trx4", transaction_info)
       print(transaction_info)



## -----------------------------------------------------------------------
## function about pubnub
## -----------------------------------------------------------------------
def publish_block():
    global next_call
    blockchain_list_blocks()

    next_call = next_call + 5
    threading.Timer( next_call - time.time(), publish_block).start()

def publish_delegate():
    global next_call2
    blockchain_list_delegate()
    next_call2 = next_call2 + 10
    threading.Timer( next_call2 - time.time(), publish_delegate).start()

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

next_call = (int (time.time() / 10)) * 10 + 1
next_call2 = next_call
publish_block()
publish_delegate()
