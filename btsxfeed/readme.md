how to use this script?

1. run client with rpc enable, you can execute with a parameter like this:

      ./bitshares_client  --server --httpport 9989 --rpcuser user --rpcpassword pass

  or edit the config.json  like this:

      "rpc": {
        "enable": true,
        "rpc_user": "user",
        "rpc_password": "pass",
        "rpc_endpoint": "127.0.0.1:0",
        "httpd_endpoint": "127.0.0.1:9989",
        "htdocs": "./htdocs"
       },

2. cp config.json.sample to config.json

    edit the rpc parameter, delegate-list ...

3. if you just want to watch the price, run command without parameter

    ./btsx_feed_auto.py 

4. if you want to publish feed,run command with the asset lists, like:

   ./btsx_feed_auto.py USD CNY GLD

