#!/usr/bin/env python
# coding=utf8

import requests
import json
import datetime, time
from pprint import pprint
import sys

######### config ################
auth = ("alt","alt")
url = "http://localhost:9989/rpc"

quote_symbol="USD"
base_symbol="BTSX"
################################
headers = {'content-type': 'application/json'}
short_enable = False
ave_price = 0
volume_short_bta = 0
order_ask = []
order_bid = []
order_cover = []
order_short = []
base_precision = quote_precision = 1

def market_status():
  global ave_price, short_enable
  global base_precision , quote_precision


  request = {
      "method": "blockchain_get_asset",
      "params": [quote_symbol],
      "jsonrpc": "2.0",
      "id": 1
      }
  responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
  asset_info = json.loads(vars(responce)["_content"])["result"]
  quote_precision = float(asset_info["precision"])
  quote_id = asset_info["id"]

  request = {
      "method": "blockchain_get_asset",
      "params": [base_symbol],
      "jsonrpc": "2.0",
      "id": 1
      }
  responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
  asset_info = json.loads(vars(responce)["_content"])["result"]
  base_precision = float(asset_info["precision"])
  base_id = asset_info["id"]

  if base_id == 0 and quote_id <= 22:
    short_enable = True
  else:
    return

  request = {
      "method": "blockchain_market_status",
      "params": [quote_symbol, base_symbol],
      "jsonrpc": "2.0",
      "id": 1
      }
  responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
  market_status = json.loads(vars(responce)["_content"])["result"]
  ave_price = float(market_status["current_feed_price"])

def list_shorts():
  global volume_short_bta
  request = {
      "method": "blockchain_market_list_shorts",
      "params": [quote_symbol],
      "jsonrpc": "2.0",
      "id": 1
      }
  responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
  order_book_json = json.loads(vars(responce)["_content"])["result"]
  for order in order_book_json:
    order_info = {}
    order_info["type"] = order["type"]
    price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
    order_info["price"] =  price
    order_info["volume_bts"] = order["state"]["balance"] / base_precision
    order_info["volume_bta"] = order_info["volume_bts"] * ave_price /2
    price_limit = order["state"]["short_price_limit"]
    if price_limit == None:
      order_short.append(order_info)
    elif float(price_limit["ratio"]) * base_precision/quote_precision >= ave_price:
      order_short.append(order_info)
    else:
      continue
    volume_short_bta += order_info["volume_bta"]

def order_book():
  request = {
      "method": "blockchain_market_order_book",
      "params": [quote_symbol, base_symbol, -1],
      "jsonrpc": "2.0",
      "id": 1
      }
  responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
  order_book_json = json.loads(vars(responce)["_content"])["result"]
  for order in order_book_json[0]:
    order_info = {}
    order_info["type"] = order["type"]
    price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
    order_info["price"] =  price
    order_info["volume_bta"] = order["state"]["balance"] / quote_precision
    order_info["volume_bts"] = order_info["volume_bta"] / price
    order_bid.append(order_info)

  for order in order_book_json[1]:
    order_info = {}
    order_info["type"] = order["type"]
    price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
    order_info["price"] = price
    if order["type"] == "ask_order":
      order_info["volume_bts"] = order["state"]["balance"] / base_precision
      order_info["volume_bta"] = order_info["volume_bts"] * price
      order_ask.append(order_info)
    elif short_enable == True:
      order_info["volume_bta"] = order["state"]["balance"] / quote_precision
      order_info["volume_bts"] = order_info["volume_bta"] / price
      order_cover.insert(0,order_info)


  sum= 0
  for order in order_bid:
    sum = sum + order["volume_bta"]
    order["depth_bta"] = sum
    order["depth_bts"] = sum/order["price"]

  sum = 0
  for order in order_ask:
    sum = sum + order["volume_bts"]
    order["depth_bts"] = sum
    order["depth_bta"] = sum * order["price"]

  sum = 0
  for order in order_cover:
    sum = sum + order["volume_bta"]
    order["depth_bta"] = sum
    order["depth_bts"] = sum/order["price"]

def format_output():
  if short_enable == True:
    print '{: <18}'.format("market %s/%s"%(quote_symbol,base_symbol)),"average price:", '{: <20}'.format(ave_price),"min cover:",'{: <20}'.format(ave_price*0.9),"short amount:",'{: <40}'.format('%s %s(%s %s)'%(volume_short_bta,quote_symbol, volume_short_bta/ave_price, base_symbol)),'{: >17}'.format(time.strftime("%H:%M:%S", time.localtime(time.time())))
  else:
    print '{: <140}'.format("market %s/%s"%(quote_symbol,base_symbol)), '{: >17}'.format(time.strftime("%H:%M:%S", time.localtime(time.time())))

  print '----------------------------------------------------------------------------------------------------------------------------------------------------------------------'
  sys.stdout.write('{: >13} '.format("Bid Price"))
  sys.stdout.write('{: >11} '.format("Vol("+quote_symbol+")"))
  sys.stdout.write('{: >11} '.format("Depth("+quote_symbol+")"))
  sys.stdout.write('{: >11} | '.format("Depth("+base_symbol+")"))
  sys.stdout.write('{: >13} '.format("Ask Price"))
  sys.stdout.write('{: >11} '.format("Vol("+quote_symbol+")"))
  sys.stdout.write('{: >11} '.format("Depth("+quote_symbol+")"))
  sys.stdout.write('{: >11} | '.format("Depth("+base_symbol+")"))
  sys.stdout.write('{: >13} '.format("Cover Price"))
  sys.stdout.write('{: >11} '.format("Vol("+quote_symbol+")"))
  sys.stdout.write('{: >11} '.format("Depth("+quote_symbol+")"))
  sys.stdout.write('{: >11} '.format("Depth("+base_symbol+")"))
  sys.stdout.write('{: >11}'.format("Warnning"))
  print
  print '----------------------------------------------------------------------------------------------------------------------------------------------------------------------'
  total = max(len(order_bid), len(order_ask), len(order_cover))
  #total = min(total, 50)
  for i in range(0,total):
    str_price = str_volume_bta = str_depth_bta = str_depth_bts = ""
    if i < len(order_bid):
      str_price = '%.8f'%order_bid[i]["price"]
      str_volume_bta = '%.2f'%order_bid[i]["volume_bta"]
      str_depth_bta = '%.2f'%order_bid[i]["depth_bta"]
      str_depth_bts = '%.2f'%order_bid[i]["depth_bts"]
    sys.stdout.write('{: >13} '.format(str_price))
    sys.stdout.write('{: >11} '.format(str_volume_bta))
    sys.stdout.write('{: >11} '.format(str_depth_bta))
    sys.stdout.write('{: >11} | '.format(str_depth_bts))
    str_price = str_volume_bta = str_depth_bta = str_depth_bts = ""
    if i < len(order_ask):
      str_price = '%.8f'%order_ask[i]["price"]
      str_volume_bta = '%.2f'%order_ask[i]["volume_bta"]
      str_depth_bta = '%.2f'%order_ask[i]["depth_bta"]
      str_depth_bts = '%.2f'%order_ask[i]["depth_bts"]
    sys.stdout.write('{: >13} '.format(str_price))
    sys.stdout.write('{: >11} '.format(str_volume_bta))
    sys.stdout.write('{: >11} '.format(str_depth_bta))
    sys.stdout.write('{: >11} | '.format(str_depth_bts))
    str_price_warn = str_price = str_volume_bta = str_depth_bta = str_depth_bts = ""
    if short_enable == True:
      if i < len(order_cover):
        str_price = '%.8f'%order_cover[i]["price"]
        str_volume_bta = '%.2f'%order_cover[i]["volume_bta"]
        str_depth_bta = '%.2f'%order_cover[i]["depth_bta"]
        str_depth_bts = '%.2f'%order_cover[i]["depth_bts"]
        str_price_warn = '%.8f'%(order_cover[i]["price"] * 10/9)
      sys.stdout.write('{: >13} '.format(str_price))
      sys.stdout.write('{: >11} '.format(str_volume_bta))
      sys.stdout.write('{: >11} '.format(str_depth_bta))
      sys.stdout.write('{: >11} '.format(str_depth_bts))
      sys.stdout.write('{: >11}'.format(str_price_warn))
    print ""

market_status()
list_shorts()
order_book()
format_output()
