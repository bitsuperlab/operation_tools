#!/usr/bin/env python
# coding=utf8

import requests
import json
import sys
from math import fabs

import datetime, threading, time
from pprint import pprint


headers = {'content-type': 'application/json',
   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}

config_data = open('config.json')
config = json.load(config_data)
config_data.close()

## -----------------------------------------------------------------------
## function about bts rpc
## -----------------------------------------------------------------------
auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
url = config["bts_rpc"]["url"]
change_min = config["price_limit"]["change_min"]
change_max = config["price_limit"]["change_max"]
max_update_hours = config["price_limit"]["max_update_hours"]
sample_timer = config["price_limit"]["sample_timer"]
median_length = config["price_limit"]["median_length"]

  asset_list_publish = sys.argv
  asset_list_publish.pop(0)
  asset_list_display = list(set(config["asset_list_display"] + asset_list_publish))
asset_list_all = ["PTS", "PPC", "LTC", "BTC", "WTI", "SLV", "GLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]

delegate_list = config["delegate_list"]
rate_cny = {}


def fetch_from_btc38():
  url="http://api.btc38.com/v1/ticker.php"
  try:
    params = { 'c': 'btsx', 'mk_type': 'btc' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = responce.json()
    price["BTC"].append(float(result["ticker"]["last"]))
    params = { 'c': 'btsx', 'mk_type': 'cny' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = responce.json()
    price_cny = float(result["ticker"]["last"])
    price["CNY"].append(price_cny)
    for asset in asset_list_display:
      if rate_cny[asset] != 0.0:
        price[asset].append(price_cny/rate_cny[asset])
  except:
    print "Warning: unknown error"
    return

def fetch_from_bter():
  try:
    url="http://data.bter.com/api/1/ticker/btsx_btc"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    price["BTC"].append(float(result["last"]))
    url="http://data.bter.com/api/1/ticker/btsx_cny"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    price_cny = float(result["last"])
    price["CNY"].append(price_cny)
    for asset in asset_list_display:
      if rate_cny[asset] != 0.0:
        price[asset].append(price_cny/rate_cny[asset])
  except:
    print "Warning: unknown error"
    return

def get_rate_from_yahoo():
  global headers
  global rate_cny
  params_s = ""
  try:
    url="http://download.finance.yahoo.com/d/quotes.csv"
    for asset in asset_list_display:
      if asset == "GLD":
        asset_yahoo = "XAU"
      elif asset == "SLV":
        asset_yahoo = "XAG"
      elif asset == "WTI":
        asset_yahoo = "TODO"
      else:
        asset_yahoo = asset
      params_s = params_s + asset_yahoo + "CNY=X,"
    #print "param is", params_s
    params = {'s':params_s,'f':'l1','e':'.csv'}
    responce = requests.get(url=url, headers=headers,params=params)
    pos = posnext = 0

    for asset in asset_list_display:
      posnext = responce.text.find("\n", pos)
      rate_cny[asset] = float(responce.text[pos:posnext])
      print "Fetch: rate ", asset, rate_cny[asset]
      pos = posnext + 1
    threading.Timer( 600, get_rate_from_yahoo).start()
  except:
    print "Warning: unknown error, try again after 1 seconds"
    threading.Timer( 1, get_rate_from_yahoo).start()

def update_feed(publish_feeds):
  global update_time
  for delegate in delegate_list:
     headers = {'content-type': 'application/json'}
     request = {
         "method": "wallet_publish_feeds",
         "params": [delegate, publish_feeds],
         "jsonrpc": "2.0",
         "id": 1
         }
     while True:
       try:
         responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
         result = json.loads(vars(responce)["_content"])
         print "Update:", delegate, publish_feeds
       except:
         print "Warnning: rpc call error, retry 5 seconds later"
         time.sleep(5)
         continue
       break
  update_time = time.time()

def fetch_price():
  global update_time
  print
  print '=================', time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time())), '=================='
  for asset in asset_list_all:
    price[asset] = []
  fetch_from_btc38()
  fetch_from_bter()
  need_update = False

  for asset in asset_list_display:
    if len(price[asset]) == 0:
      print "Warning: can't get price of", asset
      continue
    price_queue[asset].extend(price[asset])
    while len(price_queue[asset]) > median_length :
      price_queue[asset].pop(0)

    price_median[asset] = sorted(price_queue[asset])[len(price_queue[asset])/2]
    if price_median_last[asset] > 1e-20:
      change = 100.0 * (price_median[asset] - price_median_last[asset])/price_median_last[asset]
    else:
      change = 0.0
      price_median_last[asset] = price_median[asset]
    print 'Fetch:', asset, price[asset], ",median:", price_median[asset], ",change:", float('%.2f'% change),"%"
    if asset in asset_list_publish :
      if (fabs(change) > change_min and fabs(change) < change_max ) or time.time() - update_time > max_update_hours*60*60:
        need_update = True
  if need_update == True:
    publish_feeds = []
    for asset in asset_list_publish:
      if price_median_last[asset] < 1e-20:
        continue
      change = 100.0 * (price_median[asset] - price_median_last[asset])/price_median_last[asset]
      if fabs(change) > change_max  :
        continue
      publish_feeds.append([asset, price_median[asset]])
      price_median_last[asset] = price_median[asset]
    update_feed(publish_feeds)
  threading.Timer( sample_timer, fetch_price).start()

price = {}
price_queue = {}
price_median = {}
price_median_last = {}
update_time = 0
for asset in asset_list_all:
  rate_cny[asset] = 0.0
  price[asset] = []
  price_queue[asset] = []
  price_median[asset] = 0.0
  price_median_last[asset] = 0.0

get_rate_from_yahoo()
fetch_price()
