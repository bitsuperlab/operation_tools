#!/usr/bin/env python3
# coding=utf8

import logging
import logging.handlers
import json
import sys
import datetime, threading, time

from bts import BTS
import exchanges as ex
from math import fabs
import os

## Loading Config
config_file = open("config.json")
config = json.load(config_file)
config_file.close()

##Actually I think it may be beneficial to discount all feeds by 0.995 to give the market makers some breathing room and provide a buffer against down trends.
discount = 0.995

exchange_list = ["btc38", "bter", "yunbi"]
## todo: GAS, DIESEL, OIL
#asset_list_all = ["GAS", "DIESEL", "KRW", "BTC", "OIL", "SILVER", "GOLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]
asset_list_all = ["KRW", "BTC", "SILVER", "GOLD", "TRY", "SGD", "HKD", "RUB", "SEK", "NZD", "CNY", "MXN", "CAD", "CHF", "AUD", "GBP", "JPY", "EUR", "USD"]
scale = {"bts_usd":config["market_weight"]["scale_bts_usd"], "bts_cny":config["market_weight"]["scale_bts_cny"],
   "btc38":config["market_weight"]["scale_btc38"], "yunbi":config["market_weight"]["scale_yunbi"], "bter":config["market_weight"]["scale_bter"]}
depth_change = config["market_weight"]["depth_change"]

change_min = config["price_limit"]["change_min"]
change_max = config["price_limit"]["change_max"]
max_update_hours = config["price_limit"]["max_update_hours"]
sample_timer = config["price_limit"]["sample_timer"]
median_length = config["price_limit"]["median_length"]

delegate_list = config["delegate_list"]

## Setting up Logger
logger = logging.getLogger('bts')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s[%(levelname)s]: %(message)s')

#ch = logging.StreamHandler()
#ch.setFormatter(formatter)
#logger.addHandler(ch)

## Setting up Logger
fh = logging.handlers.RotatingFileHandler(config["log"]["filename"], maxBytes = config["log"]["logMaxByte"], backupCount = config["log"]["logBackupCnt"])
fh.setFormatter(formatter)
logger.addHandler(fh)

## Opening RPC to wallet
client = BTS(
    config["client"]["rpc_user"],
    config["client"]["rpc_password"],
    config["client"]["rpc_host"],
    config["client"]["rpc_port"]
)

asset_list_publish = []
asset_list_display = []

if len(sys.argv) == 2:
  if sys.argv[1] == "ALL":
    asset_list_publish = asset_list_all
    asset_list_display = asset_list_all
else:
  asset_list_publish = sys.argv
  asset_list_publish.pop(0)
  asset_list_display = list(set(config["asset_list_display"] + asset_list_publish))

def publish_rule_check(asset):
  #When attempting to write a market maker the slow movement of the feed can be difficult.
  #I would recommend the following:
  #if  REAL_PRICE < MEDIAN and YOUR_PRICE > MEDIAN publish price
  #if  you haven't published a price in the past 20 minutes
  #   if  REAL_PRICE > MEDIAN  and  YOUR_PRICE < MEDIAN and abs( YOUR_PRICE - REAL_PRICE ) / REAL_PRICE  > 0.005 publish price
  #The goal is to force the price down rapidly and allow it to creep up slowly.
  #By publishing prices more often it helps market makers maintain the peg and minimizes opportunity for shorts to sell USD below the peg that the market makers then have to absorb.
  #If we can get updates flowing smoothly then we can gradually reduce the spread in the market maker bots.
  #*note: all prices in USD per BTS
  if time.time() - update_time > max_update_hours*60*60:
    return True
  elif price_median_exchange[asset] < price_median_wallet[asset]/discount and price_publish_last[asset] > price_median_wallet[asset]/discount:
    return True
  ## if  you haven't published a price in the past 20 minutes, and the price change more than 0.5%
  elif fabs(price_change[asset]) > change_min and time.time() - update_time > 20*60:
    return True
  else:
    return False

def fetch_price():
  global asset_list_display
  for exchange_name in exchange_list:
    if scale[exchange_name] == 0.0:
      continue
    price_depth[exchange_name] = exchanges.get_price_depth_from_exchange(exchange_name, depth_change)
  price_depth["bts_usd"] = client.get_depth_in_range("USD","BTS", depth_change)
  price_depth["bts_cny"] = client.get_depth_in_range("CNY","BTS", depth_change)
  price_depth["bts_usd"][0] *= rate_cny["USD"]
  price_total = weight_total = 0

  os.system("clear")
  print("===================%s=======================" % time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time())))
  print('{: >12}'.format("EXCHANGE"),'{: >15}'.format("PRICE"), '{: >15}'.format("DEPTH"), '{: >8}'.format("SCALE"))
  print("---------------------------------------------------------")
  for exchange_name in sorted(price_depth.keys()):
    price = price_depth[exchange_name][0]
    weight = price_depth[exchange_name][1] * scale[exchange_name]
    if price != 0:
      price_total += price * weight
      weight_total += weight
    logger.info("%s: price is %.5f, depth is %.3f, scale is %.3f"%( exchange_name ,price, price_depth[exchange_name][1], scale[exchange_name]))
    print('{: >12}'.format("%s" % exchange_name), '{: >15}'.format('%.5f'% price_depth[exchange_name][0]),
          '{: >15}'.format('%.5f'% price_depth[exchange_name][1]), '{: >8}'.format('%.5f'% scale[exchange_name]))
  price_average = price_total / weight_total
  logger.info("average price is %.5f", price_average)
  print("---------------------------------------------------------")
  print('{: >12}'.format("average"), '{: >15}'.format('%.5f'% price_average))
  print("========================================================")

  for asset in asset_list_display:
    price_queue[asset].append(price_average / rate_cny[asset])
    while len(price_queue[asset]) > median_length :
      price_queue[asset].pop(0)
    price_median_exchange[asset] = sorted(price_queue[asset])[int(len(price_queue[asset])/2)]

def display_price():
  global update_time
  print("===============================================================================================")
  print('{: >8}'.format("ASSET"),'{: >10}'.format("RATE(CNY)"), '{: >15}'.format("CURRENT_FEED"), '{: >15}'.format("CURRENT_PRICE"),
     '{: >15}'.format("MEDIAN_PRICE"), '{: >15}'.format("LAST_PUBLISH"), '{: >8}'.format("CHANGE"))
  print("-----------------------------------------------------------------------------------------------")
  need_update = False
  for asset in sorted(asset_list_display):
    if price_publish_last[asset] > 1e-20:
      price_change[asset] = 100.0 * (price_median_exchange[asset] - price_publish_last[asset])/price_publish_last[asset]
    else:
      price_change[asset] = 0.0
      price_publish_last[asset] = price_median_exchange[asset]
    price_median_wallet[asset] = client.get_median(asset)
    asset_display = "%s" % asset
    if asset in asset_list_publish :
      asset_display = "*%s" % asset
      need_update = publish_rule_check(asset)
    print('{: >8}'.format("%s" % asset_display), '{: >10}'.format('%.3f'% rate_cny[asset]), '{: >15}'.format("%.4g" % price_median_wallet[asset]),
         '{: >15}'.format('%.4g'% price_queue[asset][-1]), '{: >15}'.format("%.4g"%price_median_exchange[asset]),
         '{: >15}'.format("%.4g"%price_publish_last[asset]), '{: >8}'.format('%.2f%%'% price_change[asset]))
  print("===============================================================================================")

  if need_update == True:
    update_time = time.time()
    publish_feeds = []
    for asset in asset_list_publish:
      if price_publish_last[asset] < 1e-20:
        continue
      if fabs(price_change[asset]) > change_max  :
        continue
      publish_feeds.append([asset, price_median_exchange[asset]*discount])
      price_publish_last[asset] = price_median_exchange[asset]
    for delegate in delegate_list:
      client.publish_feeds(delegate, publish_feeds)

def thread_get_rate_from_yahoo():
  global rate_cny
  try:
    rate_cny = exchanges.fetch_from_yahoo(asset_list_all)
    threading.Timer( 600, thread_get_rate_from_yahoo).start()
  except:
    logger.error("Warning: unknown error, try again after 1 seconds")
    threading.Timer( 1, thread_get_rate_from_yahoo).start()

rate_cny = {}
price_depth = {}
price_queue = {}
price_median_exchange = {}
price_median_wallet = {}
price_publish_last = {}
price_change = {}
update_time = 0
for asset in asset_list_all:
  rate_cny[asset] = 0.0
  price_queue[asset] = []
  price_median_exchange[asset] = 0.0
  price_median_wallet[asset] = 0.0
  price_publish_last[asset] = 0.0
  price_change[asset] = 0.0

exchanges = ex.Exchanges(logger)

thread_get_rate_from_yahoo()

while True:
  try:
    fetch_price()
    display_price()
  except:
    logger.error("Warning: unknown error, can't fetch price")
  time.sleep(sample_timer)
