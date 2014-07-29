#!/usr/bin/python

import sys, getopt
import requests
import json
from pprint import pprint
import time


def importkeys(keys) :
    url = "http://localhost:9988/rpc"
    headers = {'content-type': 'application/json'}
    payload2 = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
    }

    for key in keys:
        payload = {
            "method": "wallet_import_private_key",
            "params": [key],
            "jsonrpc": "2.0",
            "id": 1
        }
        auth = ('user', 'password')

        print "sending 1 transaction to import key"
        response = requests.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        pprint(vars(response))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "please input the file containing the private keys"
        quit()
    f = open(sys.argv[1],"r") #opens file contain private keys in lines
    keys = []
    for line in f:
        keys.append(line)
    importkeys(keys)
