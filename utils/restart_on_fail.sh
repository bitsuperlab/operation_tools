while [ 1=1 ] ; do
 echo "Starting node server" >>node1.log
 ./bitshares_client --data-dir=seed1 --p2p-port=1776 --input-log=./command.txt
 echo "Balls, crashed" >> node1.log
 sleep 5
done
