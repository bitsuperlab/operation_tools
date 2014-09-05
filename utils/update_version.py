#!/usr/bin/python

import sys, getopt
import requests
import json
from pprint import pprint
import time


def update_version(version):
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
            "method": "wallet_account_update_registration",
            "params": ["init" + str(i), "init" + str(i), { "version" : version } ],
            "jsonrpc": "2.0",
            "id": 1
        }
        auth = ('admin', 'pass')

        print "sending 1 transaction to update version"
        response = requests.post(url, data=json.dumps(payload), headers=headers, auth=auth)
        pprint(vars(response))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "please input the file containing the private keys"
        quit()
    version = sys.argv[1]
    update_version(version)
