#!/usr/bin/python

import sys, getopt
import requests
import json
from pprint import pprint
import time
import sched, time

config_data = open('config.json')
config = json.load(config_data)
config_data.close()
contact = config["contact"]

delegates = {}

last_block = 0

counter = 0

for key in contact.keys():
    for d in contact[key]["delegates"]:
        delegates[d] = key

pprint(delegates)

def send_simple_message(email, delegate, block_num):
    global contact
    uuid = config["mail_gun"]["uuid"]
    if contact[email]["count"] > 10:
        print email + " exceed the maximum notification"
        return
    contact[email]["count"] += 1

    return requests.post(
            "https://api.mailgun.net/v2/bitsuperlab.com/messages",
            auth=("api", uuid),
            data={"from": "Bitsuperlab <no-reply@bitsuperlab.com>",
                "to": [email],
                "subject": delegate + " is missing blocks",
                "text": "The delegate " + delegate + " is missing block" + str(block_num) + ", please check it ASAP!"})

def query_missing() :
    global last_block, contact, delegates
    headers = {'content-type': 'application/json'}

    auth = (config["bts_rpc"]["username"], config["bts_rpc"]["password"])
    url = config["bts_rpc"]["url"]

    info = {
        "method": "info",
        "params": [],
        "jsonrpc": "2.0",
        "id": 1
    }

    try:
      info_res = requests.post(url, data=json.dumps(info), headers=headers, auth=auth)
      info_json = json.loads(vars(info_res)["_content"])
    except:
      print "Can't connect to rpc server"
      return None
    if not "result" in info_json:
        return
    block_header_num = info_json["result"]["blockchain_head_block_num"]

    if last_block == block_header_num:
        return None

    last_block = block_header_num

    #print block_header_num

    list_missing = {
        "method": "blockchain_list_missing_block_delegates",
        "params": [block_header_num - 2],
        "jsonrpc": "2.0",
        "id": 1
    }

    #print "query last status of producing blocks ..."
    response = requests.post(url, data=json.dumps(list_missing), headers=headers, auth=auth)
    json_result = json.loads(vars(response)["_content"])
    if not "result" in json_result:
        return
    result = json_result["result"]
    #pprint(result)
    if len(result):
        for d in result:
            print time.strftime("%x %X", time.localtime(time.time())), d , " missed block: " , block_header_num-2
            if d in delegates:
                mail_res = send_simple_message(delegates[d], d, block_header_num -2)
                print "send mail to: " , delegates[d]

if __name__ == "__main__":
    s = sched.scheduler(time.time, time.sleep)
    print contact

    def do_something(sc):
        global counter, contact
        if counter > 12 * 60 * 24:
            counter = 0
            for key in contact.keys():
                contact[key]["count"] = 0

        counter += 1
        # do your stuff
        query_missing()
        sc.enter(5, 1, do_something, (sc,))

    s.enter(5, 1, do_something, (s,))
    s.run()
