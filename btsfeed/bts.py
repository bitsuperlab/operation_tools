#!/usr/bin/env python3
# coding=utf8

import json
import requests
import logging
import time
import sys
from pprint import pprint


class BTS():
    def __init__(self, user, password, host, port):
        self.url = "http://%s:%s@%s:%s/rpc" % (user,password,host,str(port))
        self.log = logging.getLogger('bts')
        #self.log.info("Initializing with URL:  " + self.url)

    def request(self, method, *args):
        payload = {
            "method": method,
            "params": list(*args),
            "jsonrpc": "2.0",
            "id": 0,
        }
        headers = {
          'content-type': 'application/json',
          'Authorization': "Basic YTph"
        }
        response = requests.post(self.url, data=json.dumps(payload), headers=headers)
        return response

    def publish_feeds(self, delegate, feed_list):
        response = self.request("wallet_publish_feeds", [delegate, feed_list])
        if response.status_code != 200:
            self.log.error("%s publish feeds error" % delegate)
            self.log.error(response.json())
            return False
        else:
            self.log.info("%s publish feeds %s" % (delegate,feed_list))
            return response.json()

    def get_depth_in_range(self, quote, base, range):
        price = self.get_price(quote,base)
        max_ask_price = price * (1+range)
        min_bid_price = price * (1-range)
        quote_precision =  self.get_precision(quote)
        base_precision =  self.get_precision(base)
        response = self.request("blockchain_market_order_book", [quote, base, -1])
        order_bid = response.json()["result"][0]
        order_ask = response.json()["result"][1]
        response = self.request("blockchain_market_list_shorts", [quote])
        order_short = response.json()["result"]
        depth_bid = depth_ask = 0
        for order in order_bid:
          order_price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          if order_price  < min_bid_price:
            break
          depth_bid = depth_bid + order["state"]["balance"] / (quote_precision * order_price)
        for order in order_ask:
          order_price = float(order["market_index"]["order_price"]["ratio"]) * base_precision/quote_precision
          if order["type"] == "ask_order" and order_price  < max_ask_price:
            depth_ask = depth_ask + order["state"]["balance"] / base_precision
          #elif order["type"] == "cover_order" and order_price  > min_bid_price:
          #  depth_ask = depth_ask + order["state"]["balance"] / (quote_precision * min_bid_price)
        #for order in order_short:
        #  price_limit = order["state"]["limit_price"]
        #  if price_limit == None or float(price_limit["ratio"]) * base_precision/quote_precision > min_bid_price:
        #    depth_bid = depth_bid + order["state"]["balance"] / base_precision / 2
        depth = min(depth_bid, depth_ask)
        self.log.debug("price(%s/%s) is %.5f, depth is %.3f ([%.5f ,%.3f] - [%.5f, %.3f]" % (quote, base, price, depth, min_bid_price, depth_bid, max_ask_price, depth_ask))
        return [price, depth]

    def get_median(self, asset):
        response = self.request("blockchain_get_feeds_for_asset", [asset])
        feeds = response.json()["result"]
        if feeds[-1]["delegate_name"] == "MARKET":
          return float(feeds[-1]["median_price"])
        else:
          return 0

    def get_centerprice(self, quote, base):
        response = self.request("blockchain_market_status", [quote, base])
        return float(response.json()["result"]["current_feed_price"])

    def submit_bid(self, account, amount, quote, price, base):
        response = self.request("bid", [account, amount, quote, price, base])
        if response.status_code != 200:
            self.log.info("%s submitted a bid" % account)
            self.log.info(response.json())
            return False
        else:
            return response.json()
    def submit_ask(self, account, amount, quote, price, base):
        response = self.request("ask", [account, amount, quote, price, base])
        if response.status_code != 200:
            self.log.info("%s submitted an ask" % account)
            self.log.info(response.json())
            return False
        else:
            return response.json()

    def get_lowest_ask(self, quote, base):
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        response = self.request("blockchain_market_order_book", [quote, base])
        highest_ask = float(response.json()["result"][1][0]["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
        return highest_ask

    def get_highest_bid(self, quote, base):
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        response = self.request("blockchain_market_order_book", [quote, base])
        lowest_bid  = float(response.json()["result"][0][0]["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
        return lowest_bid

    def get_balance(self, account, asset):
        asset_id = self.get_asset_id(asset)
        response = self.request("wallet_account_balance", [account, asset])
        if not response.json():
            self.log.info("Error in get_balance: %s", response["_content"]["message"])
            return 0
        if "result" not in response.json() or len(response.json()["result"]) <1:
            return 0
        asset_array = response.json()["result"][0][1]
        amount = 0
        for item in asset_array:
            if item[0] == asset_id:
                amount = item[1]
                return amount / self.get_precision(asset)
        return 0

    def cancel_bids_less_than(self, account, quote, base, price):
        cancel_args = self.get_bids_less_than(account, quote, base, price)[0]
        response = self.request("batch", ["wallet_market_cancel_order", cancel_args])
        return cancel_args

    def get_bids_less_than(self, account, quote, base, price):
        quotePrecision = self.get_precision( quote )
        basePrecision = self.get_precision( base )
        response = self.request("wallet_market_order_list", [quote, base, -1, account])
        order_ids = []
        quote_shares = 0
        if "result" not in response.json() or response.json()["result"] == None:
            return [[], 0]
        for pair in response.json()["result"]:
            order_id = pair[0]
            item = pair[1]
            if item["type"] == "bid_order":
                if float(item["market_index"]["order_price"]["ratio"])* (basePrecision / quotePrecision) < price:
                    order_ids.append(order_id)
                    quote_shares += int(item["state"]["balance"])
                    self.log.info("%s canceled an order: %s" % (account, str(item)))
        cancel_args = [item for item in order_ids]
        return [cancel_args, float(quote_shares) / quotePrecision]

    def cancel_bids_out_of_range(self, account, quote, base, price, tolerance):
        cancel_args = self.get_bids_out_of_range(account, quote, base, price, tolerance)[0]
        response = self.get_bids_out_of_range(account, quote, base, price, tolerance)
        return cancel_args

    def get_bids_out_of_range(self, account, quote, base, price, tolerance):
        quotePrecision = self.get_precision( quote )
        basePrecision = self.get_precision( base )
        response = self.request("wallet_market_order_list", [quote, base, -1, account]).json()
        order_ids = []
        quote_shares = 0
        if "result" not in response or response["result"] == None:
           return [[], 0]
        for pair in response["result"]:
            order_id = pair[0]
            item = pair[1]
            if item["type"] == "bid_order":
                if abs(price - float(item["market_index"]["order_price"]["ratio"]) * (basePrecision / quotePrecision)) > tolerance:
                    order_ids.append(order_id)
                    quote_shares += int(item["state"]["balance"])
                    self.log.info("%s canceled an order: %s" % (account, str(item)))
        cancel_args = [item for item in order_ids]
        return [cancel_args, float(quote_shares) / quotePrecision]

    def cancel_asks_out_of_range(self, account, quote, base, price, tolerance):
        cancel_args = self.get_asks_out_of_range(account, quote, base, price, tolerance)[0]
        response = self.request("batch", ["wallet_market_cancel_order", cancel_args])
        return cancel_args

    def get_asks_out_of_range(self, account, quote, base, price, tolerance):
        quotePrecision = self.get_precision( quote )
        basePrecision = self.get_precision( base )
        response = self.request("wallet_market_order_list", [quote, base, -1, account]).json()
        order_ids = []
        base_shares = 0
        if "result" not in response or response["result"] == None:
           return [[], 0]
        for pair in response["result"]:
            order_id = pair[0]
            item = pair[1]
            if item["type"] == "ask_order":
                if abs(price - float(item["market_index"]["order_price"]["ratio"]) * (basePrecision / quotePrecision)) > tolerance:
                    order_ids.append(order_id)
                    base_shares += int(item["state"]["balance"])
        cancel_args = [item for item in order_ids]
        return [cancel_args, base_shares / basePrecision]

    def cancel_all_orders(self, account, quote, base):
        cancel_args = self.get_all_orders(account, quote, base)
        #response = self.request("batch", ["wallet_market_cancel_order", [cancel_args[0]] ])
        for i in cancel_args[0] :
            response = self.request("wallet_market_cancel_order", [i])
        return cancel_args[1]

    def get_all_orders(self, account, quote, base):
        response = self.request("wallet_market_order_list", [quote, base, -1, account])
        order_ids = []
        orders = []
        if "result" in response.json():
           for item in response.json()["result"]:
               order_ids.append(item[0])
               orders.append(item[1])
           orderids = [item for item in order_ids]
           return [ orderids, orders ]
        return

    def get_last_fill (self, quote, base):
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        last_fill = -1
        response = self.request("blockchain_market_order_history", [quote, base, 0, 1])
        for order in response.json()["result"]:
            last_fill = float(order["ask_price"]["ratio"])*(basePrecision / quotePrecision)
        return last_fill

    def get_price(self, quote, base):
        response = self.request("blockchain_market_order_book", [quote, base, 1])
        order = response.json()["result"]
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        lowest_bid  = float(order[0][0]["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
        highest_ask = float(order[1][0]["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
        return (lowest_bid+highest_ask)/2

    def ask_at_market_price(self, name, amount, base, quote, confirm=False) :
        last_fill      = -1
        response       = self.request("blockchain_market_order_book", [quote, base])
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        orders = []
        for order in response.json()["result"][0]: # bid orders
            order_price  = float(order["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
            order_amount = float(order["state"]["balance"]/quotePrecision) / order_price  # denoted in BASE
            if amount >= order_amount : # buy full amount
              orders.append([name, order_amount, base, order_price, quote])
              amount -= order_amount
            elif amount < order_amount: # partial
              orders.append([name, amount, base, order_price, quote])
              break
        for o in orders :
            print( "Selling %15.8f %s for %12.8f %s @ %12.8f" %(o[1], o[2], o[1]*o[3], o[4], o[3]) )
        orders = [ i for i in orders ]
        if not confirm or self.query_yes_no( "I dare you confirm the orders above: ") :
            return self.request("batch", ["ask", orders]).json()

    def bid_at_market_price(self, name, amount, base, quote, confirm=False) :
        last_fill      = -1
        response       = self.request("blockchain_market_order_book", [quote, base])
        quotePrecision = self.get_precision(quote)
        basePrecision  = self.get_precision(base)
        orders = []
        for order in response.json()["result"][1]: # ask orders
            order_price  = float(order["market_index"]["order_price"]["ratio"])*(basePrecision / quotePrecision)
            order_amount = float(order["state"]["balance"]/quotePrecision) / order_price  # denoted in BASE
            if amount >= order_amount : # buy full amount
              orders.append([name, order_amount, base, order_price, quote])
              amount -= order_amount
            elif amount < order_amount: # partial
              orders.append([name, amount, base, order_price, quote])
              break
        for o in orders :
            print( "Buying %15.8f %s for %12.8f %s @ %12.8f" %(o[1], o[2], o[1]*o[3], o[4], o[3]) )
        orders = [ i for i in orders ]
        if not confirm or self.query_yes_no( "I dare you confirm the orders above: ") :
            return self.request("batch", ["bid", orders]).json()

    def wait_for_block(self):
        response = self.request("get_info", [])
        blocknum = response.json()["result"]["blockchain_head_block_num"]
        while True:
            time.sleep(0.1)
            response = self.request("get_info", [])
            blocknum2 = response.json()["result"]["blockchain_head_block_num"]
            if blocknum2 != blocknum:
                return

    def get_precision(self, asset):
        response = self.request("blockchain_get_asset", [asset])
        return float(response.json()["result"]["precision"])

    def get_asset_id(self, asset):
        response = self.request("blockchain_get_asset", [asset])
        return response.json()["result"]["id"]

    def get_tx_history( self, name, asset ):
        return self.request("history", [ name, asset ]).json()["result"]

    def query_yes_no(self, question, default="yes"):
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)
        while True:
            sys.stdout.write(question + prompt)
            choice = input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")

