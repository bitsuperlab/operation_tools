#!/usr/bin/python

import sys, getopt
import requests
import json
from pprint import pprint
import time
import sched, time
import psutil

config_data = open('config.json')
config = json.load(config_data)
config_data.close()
contact = config["contact"]
monit_procs = config["monitor_procs"]
g_proc_name = ""
g_proc_num = 0
g_interval = 2

def send_simple_message(mail_subject, mail_text):
    global contact
    uuid = config["mail_gun"]["uuid"]

    to_emails = []
    for cont in contact:
        to_emails.append(cont)
    print to_emails

    return requests.post(
            "https://api.mailgun.net/v3/mg.ademail.ren/messages",
            auth=("api", uuid),
            data={"from": "DacTest@mg.ademail.ren",
                "to": to_emails,
                "subject": mail_subject,
                "text": mail_text})

def query_process(name):
    proc_num = 0
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name'])
        except psutil.NoSuchProcess:
            pass
        else:
            if(pinfo['name'] == name):
                proc_num += 1

    return proc_num

def check_process():
    global g_proc_name, g_proc_num
    for proc_name in monit_procs:
        proc_num = query_process(proc_name)
        print proc_name, "has" ,proc_num ,"instances"
        if( proc_num < monit_procs[proc_name]["expected_count"]):
            g_proc_name = proc_name
            g_proc_num = proc_num
            return False

    return True

if __name__ == "__main__":
    s = sched.scheduler(time.time, time.sleep)
    print contact

    def do_something(sc):
        global g_proc_name, g_proc_num
        # do your stuff
        if(not check_process()):
            mail_title = g_proc_name, "is not running"
            mail_text = g_proc_name, "has" ,g_proc_num ,"instances, it is less than expected. Please check asap!"
            print "send ", mail_title, " ",mail_text
            send_simple_message(mail_title, mail_text)
            return

        sc.enter(g_interval, 1, do_something, (sc,))

    s.enter(g_interval, 1, do_something, (s,))
    s.run()
