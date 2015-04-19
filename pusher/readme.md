this is a demo for howto use puser service from btsbots.com

1. require autobahn:
pip3 install asyncio
pip3 install autobahn

2. demo
1) height** , demo for push blockchain height
2) order_book**, demo for push order book of CNY/BTS

3. howto run demo
1) set config.json to your wamp server and wallet rpc server
cp config.json.sample config.json
edit config.json

2) run backend
./height_backend.py

3) run frontend
3.1) watch pusher at console
./height_forntend.py

3.2) or watch pusher at browser
firefox height.html
