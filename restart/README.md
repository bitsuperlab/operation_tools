for now, delegate will miss blocks after long time running.
BM suggest to restart client every day.
here is a method for automatic restart.
1. run wallet with this expect script, you should change "wallet_name" and "command line"
this script will start client automatic while it's quit.

```
run_wallet.sh
```

2. kill the client every 24 hours.
call restart.py every 24 hours at crontab, this script will check next block generation timestamp, make sure there is enough time to restart client
```
python restart.py
```

3. we'll provide more suitable tools to detect the missing block and restart automatic soon.
