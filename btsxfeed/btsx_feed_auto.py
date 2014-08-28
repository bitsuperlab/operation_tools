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
asset_list_publish = sys.argv
asset_list_publish.pop(0)
asset_list_display = config["asset_list_display"] + asset_list_publish
asset_list_all = ["PTS", "PPC", "LTC", "BTC", "WTI", "SLV", "GLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]

delegate_list = config["delegate_list"]


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
    price["USD"].append(price_cny/rate_usd_cny)
    price["GLD"].append(price_cny/rate_xau_cny)
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
    price["USD"].append(price_cny/rate_usd_cny)
    price["GLD"].append(price_cny/rate_xau_cny)
  except:
    print "Warning: unknown error"
    return

def get_rate_from_yahoo():
  global headers
  global rate_usd_cny, rate_xau_cny
  try:
    url="http://download.finance.yahoo.com/d/quotes.csv"
    params = {'s':'USDCNY=X,XAUCNY=X','f':'l1','e':'.csv'}
    responce = requests.get(url=url, headers=headers,params=params)
    pos = posnext = 0
    posnext = responce.text.find("\n", pos)
    rate_usd_cny = float(responce.text[pos:posnext])
    print "Fetch: rate usd/cny", rate_usd_cny
    pos = posnext + 1
    posnext = responce.text.find("\n", pos)
    rate_xau_cny = float(responce.text[pos:posnext])
    print "Fetch: rate xau/cny", rate_xau_cny
    ## loop every 10 minutes
    threading.Timer( 600, get_rate_from_yahoo).start()
  except:
    print "Warning: unknown error, try again after 1 seconds"
    threading.Timer( 1, get_rate_from_yahoo).start()

def update_feed(price, asset):
  for delegate in delegate_list:
     headers = {'content-type': 'application/json'}
     request = {
         "method": "wallet_publish_price_feed",
         "params": [delegate, price, asset],
         "jsonrpc": "2.0",
         "id": 1
         }
     while True:
       try:
         responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
         result = json.loads(vars(responce)["_content"])
         print "Update:", delegate, price_average[asset], asset
       except:
         print "Warnning: Can't connect to rpc server, retry 5 seconds later"
         time.sleep(5)
         continue
       break

def fetch_price():
  print
  print '=================', time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time())), '=================='
  for asset in asset_list_all:
    price[asset] = []
  fetch_from_btc38()
  fetch_from_bter()

  for asset in asset_list_display:
    if len(price[asset]) == 0:
      print "Warning: can't get price of", asset
      continue
    price_average[asset] = sum(price[asset])/len(price[asset])
    if price_average_last[asset] != 0.0:
      change = 100.0 * (price_average[asset] - price_average_last[asset])/price_average_last[asset]
    else:
      change = 100.0
    print 'Fetch:', asset, price[asset], ",ave:", price_average[asset], ",change:", float('%.2f'% change),"%"
    if fabs(change) > 5 :
      price_average_last[asset] = price_average[asset]
      if asset in asset_list_publish :
        update_feed(price_average[asset], asset)
  threading.Timer( 60, fetch_price).start()

rate_usd_cny = 0.0
rate_xau_cny = 0.0
get_rate_from_yahoo()

price = {}
price_average = {}
price_average_last = {}
for asset in asset_list_all:
  price[asset] = []
  price_average[asset] = 0.0
  price_average_last[asset] = 0.0
fetch_price()
