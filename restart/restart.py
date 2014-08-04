#!/usr/bin/python

import requests
import json
import time
import os

safetime = 120  # safe time, 120 seconds is safe to restart client
auth = ('user', 'pass') ## user/pass for rpc service
url = "http://localhost:9989/rpc"  ## rpc url

def main() :
    headers = {'content-type': 'application/json'}
    info = {
        "method": "get_info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
    }

    while True:
        info_res = requests.post(url, data=json.dumps(info), headers=headers, auth=auth)
        info_json = json.loads(vars(info_res)["_content"])
        if not "result" in info_json:
            return
        block_production_timestamp = info_json["result"]["wallet_next_block_production_timestamp"]
        safe_timestamp = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()+safetime))
        if block_production_timestamp > safe_timestamp :
            break;
        #print("wait...")
        time.sleep(10)
    #print("kill...")
    time.sleep(10) ## wait 10 second make sure it's broadcast out
    os.system("killall -9 bitshares_client");

if __name__ == "__main__":
    main()
