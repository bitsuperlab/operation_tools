#!/usr/bin/python

import sys, getopt
import requests
import json
from pprint import pprint
import time


def main() :
    url = "http://localhost:9988/rpc"
    headers = {'content-type': 'application/json'}
    payload2 = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
    }

    for i in range(101):
        payload = {
            "method": "wallet_delegate_set_block_production",
            "params": ["init" + str(i), "true"],
            "jsonrpc": "2.0",
            "id": 1
        }
        auth = ('user', 'password')

        print "sending 1 transaction to enable delegate init" + str(i)
        response = requests.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        pprint(vars(response))

if __name__ == "__main__":
    main()
