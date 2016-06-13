#!/usr/bin/env python3
# coding=utf8

import json
import datetime, time
from pprint import pprint
import sys
import operator

from bts import BTS

quote_precision = 0
quote_supply = 0
collected_fees  = 0.0

quote_symbol = "USD"
if len(sys.argv) > 1:
  quote_symbol=sys.argv[1]

## Loading Config
config_file = open("config.json")
config = json.load(config_file)
config_file.close()

## Opening RPC to wallet
client = BTS(
    config["client"]["rpc_user"],
    config["client"]["rpc_password"],
    config["client"]["rpc_host"],
    config["client"]["rpc_port"]
)

def get_asset_info():
  global quote_precision, collected_fees, quote_supply

  response = client.request("blockchain_get_asset", [quote_symbol])
  asset_info = response.json()["result"]
  quote_precision = asset_info["precision"]
  quote_supply = asset_info["current_supply"] / quote_precision
  collected_fees = asset_info["collected_fees"] / quote_precision

def get_covers():
  response = client.request("blockchain_market_list_covers", [quote_symbol, "BTS"])
  cover_list = response.json()["result"]
  cover_list.sort(key= operator.itemgetter("expiration"))
  cover_expiration= []
  expiration_day_last = 0
  interest_sum = collected_fees
  for order in cover_list:
    balance = float(order["state"]["balance"] / quote_precision)
    interest_rate = float(order["interest_rate"]["ratio"])
    print(order["expiration"], '{: >15}'.format("%.2f"% balance), quote_symbol, '{: >8}'.format("%.3f%%"%(interest_rate*100)),
      '{: >10}'.format("%.2f"%(balance*interest_rate)))
    expiration_day = time.strftime("%Y-%m-%d",time.strptime(order["expiration"], "%Y-%m-%dT%H:%M:%S"))
    if expiration_day == expiration_day_last:
      cover_expiration[-1][1] = cover_expiration[-1][1] + balance
      cover_expiration[-1][2] = cover_expiration[-1][2] + balance * interest_rate
    else:
      cover_expiration.append([expiration_day, balance, balance * interest_rate])
      expiration_day_last = expiration_day
    interest_sum += balance * interest_rate
  for order in cover_expiration:
    print(order[0], '{: >15}'.format("%.2f"% order[1]), quote_symbol, '{: >10}'.format("%.2f"%order[2]))
  print("total interest is %.2f, rate is %.3f%%" %(interest_sum, interest_sum/quote_supply*100))


get_asset_info()
get_covers()
