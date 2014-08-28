while [ 1=1 ] ; do
 echo "Starting node server" >>node.log
 bitshares_client
 echo "Balls, crashed" >> node.log
 sleep 5
done
