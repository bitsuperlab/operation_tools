import requests
import json
from datetime import datetime
import time
import statistics
import re
from math import fabs
import numpy as num
from operator import itemgetter, attrgetter


class Exchanges() :

    ## ----------------------------------------------------------------------------
    ## Init
    ## ----------------------------------------------------------------------------
    def __init__(self,log):
         self.header = {'content-type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}

         self.log = log
         self.order_book_ask = {"btc38":[], "yunbi":[], "bter":[]}
         self.order_book_bid = {"btc38":[], "yunbi":[], "bter":[]}
         self.true_price_in_cny_per_bts = 0
         self.rate_cny = {}

    ## ----------------------------------------------------------------------------
    ## Fetch data
    ## ----------------------------------------------------------------------------
    ###########################################################################
    def fetch_from_btc38(self):
      try :
        url="http://api.btc38.com/v1/depth.php"
        params = { 'c': 'bts', 'mk_type': 'cny' }
        response = requests.get(url=url, params=params, headers=self.header, timeout=3)
        self.order_book_ask["btc38"] = response.json()["asks"]
        self.order_book_bid["btc38"] = response.json()["bids"]
        #self.log.info(self.order_book_ask["btc38"])
        #self.log.info(self.order_book_bid["btc38"])
      except:
        self.log.error("Error fetching results from btc38!")
        return


    def fetch_from_bter(self):
      try:
        url="http://data.bter.com/api/1/depth/bts_cny"
        response = requests.get(url=url, headers=self.header, timeout=3)
        self.order_book_ask["bter"] = []
        self.order_book_bid["bter"] = []
        for order in response.json()["asks"]:
          self.order_book_ask["bter"].insert(0, [float(order[0]), float(order[1])])
        for order in response.json()["bids"]:
          self.order_book_bid["bter"].append([float(order[0]), float(order[1])])
        #self.log.info(self.order_book_ask["bter"])
        #self.log.info(self.order_book_bid["bter"])
      except:
        self.log.error("Error fetching results from bter!")
        return

    def fetch_from_yunbi(self):
      try:
        url="https://yunbi.com/api/v2/depth.json"
        params = { 'market': 'btsxcny'}
        response = requests.get(url=url, params=params, headers=self.header, timeout=3)
        self.order_book_ask["yunbi"] = []
        self.order_book_bid["yunbi"] = []
        for order in response.json()["asks"]:
          self.order_book_ask["yunbi"].insert(0, [float(order[0]), float(order[1])])
        for order in response.json()["bids"]:
          self.order_book_bid["yunbi"].append([float(order[0]), float(order[1])])
        #self.log.info(self.order_book_ask["yunbi"])
        #self.log.info(self.order_book_bid["yunbi"])
      except:
        self.log.error("Error fetching results from yunbi!")
        return


    ###########################################################################
    def fetch_from_yahoo(self, assets):
      rate_cny = {}
      params_s = ""
      url="http://download.finance.yahoo.com/d/quotes.csv"
      for asset in assets:
        if asset == "GOLD":
         asset_yahoo = "XAU"
        elif asset == "SILVER":
         asset_yahoo = "XAG"
        elif asset == "OIL" or asset == "GAS"  or asset == "DIESEL":
         asset_yahoo = "TODO"
        else:
         asset_yahoo = asset
        params_s = params_s + asset_yahoo + "CNY=X,"
      try :
       params = {'s':params_s,'f':'l1','e':'.csv'}
       response = requests.get(url=url, headers=self.header,params=params, timeout=3)

       pos = posnext = 0
       for asset in assets:
         posnext = response.text.find("\n", pos)
         rate_cny[asset] = float(response.text[pos:posnext])
         pos = posnext + 1
       #self.log.info(self.rate_cny)
       return(rate_cny)
      except:
       self.log.error("Error fetching results from yahoo!")
       return

    def fetch_from_exchange(self, exchange):
      self.order_book_ask[exchange] = self.order_book_bid[exchange] = []
      if exchange == "btc38":
        self.fetch_from_btc38()
      elif exchange == "yunbi":
        self.fetch_from_yunbi()
      if exchange == "bter":
        self.fetch_from_bter()

    def get_price_depth_from_exchange(self, exchange, ranger):
      try:
        self.fetch_from_exchange(exchange)

        price = (self.order_book_ask[exchange][0][0] + self.order_book_bid[exchange][0][0])/2.0
        max_ask_price = price * (1+ranger)
        min_bid_price = price * (1-ranger)
        depth_bid = depth_ask = 0
        for order in self.order_book_bid[exchange]:
          if order[0] < min_bid_price:
            break
          depth_bid = depth_bid + order[1]
        for order in self.order_book_ask[exchange]:
          if order[0] > max_ask_price:
            break
          depth_ask = depth_ask + order[1]

        depth = min(depth_bid, depth_ask)
        self.log.debug("get price depth from %s, price is %.5f, depth is %.3f([%.5f,%.3f] - [%.5f,%.3f])" %
            (exchange, price,  depth, min_bid_price, depth_bid, max_ask_price, depth_ask))
        return [price, depth]
      except:
        self.log.error("Error get price from %s!" % exchange)
        return [0, 0]
