#!/usr/bin/env python
# coding=utf8

# This is a watchdog script which connects to a delegate periodically to verify that it is up and running,
# and to do some basic maintenance tasks if the delegate is not ready to sign blocks and report if it is
# unhealthy

import requests
import sys
import os
import json
import getpass
import time
import datetime
from pprint import pprint

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
url = config["bts_rpc"]["url"]

WALLET_NAME = config["wallet_name"]

MAX_ALLOWABLE_HEAD_BLOCK_AGE = datetime.timedelta(minutes=2)

passphrase = getpass.getpass("Please enter your delegate's wallet passphrase: ")

def parse_date(date):
  return datetime.datetime.strptime(date, "%Y%m%dT%H%M%S")

def call(method, params=[]):
  headers = {'content-type': 'application/json'}
  request = {
          "method": method,
          "params": params,
          "jsonrpc": "2.0",
          "id": 1
          }

  while True:
    try:
      response = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
      result = json.loads(vars(response)["_content"])
      print "Method:", method
      print "Result:", result
      return result
    except:
      print "Warnning: rpc call error, retry 5 seconds later"
      time.sleep(5)
      continue
    break  
  return None

result = call("login", [RPC_USERNAME, RPC_PASSWORD])
if "error" in result or not result["result"]:
  print("Failed to login to RPC server:")
  print(result["error"])
  exit(1)

while True:
  try:
    print("\n\nRunning Watchdog")
 
    response = call("get_info")
    if "error" in response:
      print("FATAL: Failed to get info:")
      print(result["error"])
      exit(1)
    response = response["result"]
    
    if "wallet_open" not in response or not response["wallet_open"]:
      print("Opening wallet.")
      result = call("open", [WALLET_NAME])
      if "error" in result:
        print("Failed to open wallet:")
        print(result["error"])
 
    if "wallet_unlocked" not in response or not response["wallet_unlocked"]:
      print("Unlocking wallet.")
      result = call("unlock", [99999999, passphrase])
      if "error" in result:
        print("Failed to unlock wallet:")
        print(result["error"])
        passphrase = getpass.getpass("Please enter your delegate's wallet passphrase: ")
        continue
    
    if "wallet_block_production_enabled" not in response or not response["wallet_block_production_enabled"]:
      print("Enabling block production for all delegates.")
      result = call("wallet_delegate_set_block_production", ["ALL", True])
      if "error" in result:
        print("Failed to enable block production:")
        print(result["error"])
 
    response = call("get_info")["result"]
 
    if "wallet_next_block_production_time" not in response or not response["wallet_next_block_production_time"]:
      print("Next production time is unset... Are there active delegates here?")
    if parse_date(response["ntp_time"]) - parse_date(response["blockchain_head_block_timestamp"]) > MAX_ALLOWABLE_HEAD_BLOCK_AGE:
      print("Head block is too old: %s" % (response["blockchain_head_block_age"]))
    if int(response["network_num_connections"]) < 1:
      print("No connections to delegate")
 
    time.sleep(10)
  except:
    try:
      call("login", [RPC_USERNAME, RPC_PASSWORD])
    except:
      pass
    time.sleep(10)
