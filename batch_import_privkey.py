#!/usr/bin/python

import requests
import json
from pprint import pprint
import time


def importkeys(keys) :
    url = "http://localhost:8899/rpc"
    headers = {'content-type': 'application/json'}
    payload2 = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 10
    }

    for key in keys:
        payload = {
            "method": "wallet_import_private_key",
            "params": [key],
            "jsonrpc": "2.0",
            "id": i
        }
        auth = ('user', 'password')

        print "sending 1 transaction to import key"
        response = requests.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        pprint(vars(response))

if __name__ == "__main__":
    main()
    f = open("test.txt","r") #opens file with name of "test.txt"
    keys = []
    for line in f:
        keys.append(line)

