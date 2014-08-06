#!/usr/bin/python

import sys, getopt
import requests
import json
import pprint
import time

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "please input the file containing the private keys"
        quit()
    f = open(sys.argv[1],"r") #opens file contain private keys in lines
    keys = []
    i = 0
    for line in f:
        init_d = {
                "name": ("init" + str(i)),
                "delegate_pay_rate": 100,
                "owner": line.rstrip()
        }

        keys.append(init_d)
        i += 1

    print json.dumps(keys, sort_keys=True, indent=4, separators=(',', ': '))
