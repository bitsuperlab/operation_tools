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

##Actually I think it may be beneficial to discount all feeds by 0.995 to give the market makers some breathing room and provide a buffer against down trends.
discount = 0.995

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

asset_list_all = ["PTS", "PPC", "LTC", "BTC", "WTI", "SLV", "GLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]
if len(sys.argv) == 2:
  if sys.argv[1] == "ALL":
    asset_list_publish = asset_list_all
    asset_list_display = asset_list_all
else:
  asset_list_publish = sys.argv
  asset_list_publish.pop(0)
  asset_list_display = list(set(config["asset_list_display"] + asset_list_publish))

delegate_list = config["delegate_list"]
rate_cny = {}

def publish_rule2():
  global update_time
  if (fabs(change[asset]) > change_min and fabs(change[asset]) < change_max ) or time.time() - update_time > max_update_hours*60*60:
    return True
  else:
    return False

def publish_rule():
  #When attempting to write a market maker the slow movement of the feed can be difficult.
  #I would recommend the following:
  #if  REAL_PRICE < MEDIAN and YOUR_PRICE > MEDIAN publish price
  #if  you haven't published a price in the past 20 minutes
  #   if  REAL_PRICE > MEDIAN  and  YOUR_PRICE < MEDIAN and abs( YOUR_PRICE - REAL_PRICE ) / REAL_PRICE  > 0.005 publish price
  #The goal is to force the price down rapidly and allow it to creep up slowly.
  #By publishing prices more often it helps market makers maintain the peg and minimizes opportunity for shorts to sell USD below the peg that the market makers then have to absorb.
  #If we can get updates flowing smoothly then we can gradually reduce the spread in the market maker bots.
  #*note: all prices in USD per BTSX
  if time.time() - update_time > max_update_hours*60*60:
    return True
  elif price_median_source[asset] < price_median_wallet[asset] and price_publish[asset] > price_median_wallet[asset]:
    return True
  ## if  you haven't published a price in the past 20 minutes, and the price change more than 0.5%
  elif fabs(change[asset]) > change_min and time.time() - update_time > 20*60:
    return True
  else:
    return False

def fetch_from_wallet():
  for asset in asset_list_publish :
     headers = {'content-type': 'application/json'}
     request = {
         "method": "blockchain_get_feeds_for_asset",
         "params": [asset],
         "jsonrpc": "2.0",
         "id": 1
         }
     while True:
       try:
         responce = requests.post(url, data=json.dumps(request), headers=headers, auth=auth)
         feed_list = json.loads(vars(responce)["_content"])["result"]
         for feed in feed_list:
           if feed["delegate_name"] == "MARKET":
              price_median_wallet[asset] = float('%.3g'%float(feed["median_price"]/discount))
       except:
         print "Warnning: rpc call error, retry 5 seconds later"
         time.sleep(5)
         continue
       break

def fetch_from_btc38():
  url="http://api.btc38.com/v1/ticker.php"
  try:
    params = { 'c': 'btsx', 'mk_type': 'btc' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = json.loads(vars(responce)['_content'].decode("utf-8-sig"))
    price["BTC"].append(float("%.3g" % result["ticker"]["last"]))

    params = { 'c': 'pts', 'mk_type': 'cny' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = json.loads(vars(responce)['_content'].decode("utf-8-sig"))
    rate_cny["PTS"] = float(result["ticker"]["last"])
    params = { 'c': 'ppc', 'mk_type': 'cny' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = json.loads(vars(responce)['_content'].decode("utf-8-sig"))
    rate_cny["PPC"] = float(result["ticker"]["last"])
    params = { 'c': 'ltc', 'mk_type': 'cny' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = json.loads(vars(responce)['_content'].decode("utf-8-sig"))
    rate_cny["LTC"] = float(result["ticker"]["last"])

    params = { 'c': 'btsx', 'mk_type': 'cny' }
    responce = requests.get(url=url, params=params, headers=headers)
    result = json.loads(vars(responce)['_content'].decode("utf-8-sig"))
    price_cny = float("%.3g" % result["ticker"]["last"])
    price["CNY"].append(price_cny)
    for asset in asset_list_display:
      if rate_cny[asset] != 0.0:
        price[asset].append(float("%.3g" % (price_cny/rate_cny[asset])))
  except:
    print "Warning: unknown error"
    return

def fetch_from_yunbi():
  try:
    url="https://yunbi.com/api/v2/tickers/btccny.json"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    rate_cny["BTC"] = float(result["ticker"]["last"])

    url="https://yunbi.com/api/v2/tickers/btsxcny.json"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    price_cny = float("%.3g" % float(result["ticker"]["last"]))
    price["CNY"].append(price_cny)
    for asset in asset_list_display:
      if rate_cny[asset] != 0.0:
        price[asset].append(float ("%.3g" % (price_cny/rate_cny[asset])))
    rate_cny["BTC"] = 0.0
  except:
    print "Warning: unknown error"
    return

def fetch_from_bter():
  try:
    url="http://data.bter.com/api/1/ticker/btsx_btc"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    price["BTC"].append(float("%.3g" % float(result["last"])))

    url="http://data.bter.com/api/1/ticker/pts_cny"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    rate_cny["PTS"] = float(result["last"])
    url="http://data.bter.com/api/1/ticker/ppc_cny"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    rate_cny["PPC"] = float(result["last"])
    url="http://data.bter.com/api/1/ticker/ltc_cny"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    rate_cny["LTC"] = float(result["last"])

    url="http://data.bter.com/api/1/ticker/btsx_cny"
    responce = requests.get(url=url, headers=headers)
    result = responce.json()
    price_cny = float("%.3g" % float(result["last"]))
    price["CNY"].append(price_cny)
    for asset in asset_list_display:
      if rate_cny[asset] != 0.0:
        price[asset].append(float ("%.3g" % (price_cny/rate_cny[asset])))
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
      pos = posnext + 1
    rate_cny["CNY"] = 0.0
    rate_cny["BTC"] = 0.0
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
  for asset in asset_list_all:
    price[asset] = []
  fetch_from_wallet()
  fetch_from_btc38()
  fetch_from_yunbi()
  fetch_from_bter()
  need_update = False

  print "========================================================================================="
  print '{: >6}'.format("ASSET"), '{: >10}'.format("MEDIAN"), '{: >10}'.format("PUBLISH"), '{: >10}'.format("REAL"),'{: >8}'.format("CHANGE"),'{: >16}'.format("RATE(CNY/ASSET)"), "| CURRENT PRICE", time.strftime("(%Y%m%dT%H%M%S)", time.localtime(time.time()))
  print "-----------------------------------------------------------------------------------------"
  for asset in asset_list_display:
    if len(price[asset]) == 0:
      print "Warning: can't get price of", asset
      continue
    price_queue[asset].extend(price[asset])
    while len(price_queue[asset]) > median_length :
      price_queue[asset].pop(0)

    price_median_source[asset] = sorted(price_queue[asset])[len(price_queue[asset])/2]
    if price_publish[asset] > 1e-20:
      change[asset] = 100.0 * (price_median_source[asset] - price_publish[asset])/price_publish[asset]
    else:
      change[asset] = 0.0
      price_publish[asset] = price_median_source[asset]
    if asset in asset_list_publish :
      print '{: >6}'.format("*" + asset),  '{: >10}'.format(price_median_wallet[asset]), '{: >10}'.format(price_publish[asset]), '{: >10}'.format(price_median_source[asset]),'{: >8}'.format('%.2f%%'% change[asset]),'{: >16}'.format('%.2f'% rate_cny[asset]), '|', price[asset]
      need_update = publish_rule()
    else:
      print '{: >6}'.format(asset),  '{: >10}'.format(price_median_wallet[asset]), '{: >10}'.format(price_publish[asset]), '{: >10}'.format(price_median_source[asset]),'{: >8}'.format('%.2f%%'% change[asset]),'{: >16}'.format('%.2f'% rate_cny[asset]), '|', price[asset]
  print "========================================================================================="
  if need_update == True:
    publish_feeds = []
    for asset in asset_list_publish:
      if price_publish[asset] < 1e-20:
        continue
      if fabs(change[asset]) > change_max  :
        continue
      publish_feeds.append([asset, price_median_source[asset]*discount])
      price_publish[asset] = price_median_source[asset]
    update_feed(publish_feeds)
  threading.Timer( sample_timer, fetch_price).start()

price = {}
price_queue = {}
price_median_source = {}
price_median_wallet = {}
price_publish = {}
change = {}
update_time = 0
for asset in asset_list_all:
  rate_cny[asset] = 0.0
  price[asset] = []
  price_queue[asset] = []
  price_median_source[asset] = 0.0
  price_median_wallet[asset] = 0.0
  price_publish[asset] = 0.0
  change[asset] = 0.0

get_rate_from_yahoo()
fetch_price()
