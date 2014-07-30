#!/usr/bin/expect -f

set timeout -1
set default_port 1776
set port $default_port

### change wallet_name here
set wallet_name "delegate"
send_user "wallet name is: $wallet_name\n"
send_user "wallet passphrase: "
stty -echo
expect_user -re "(.*)\n"
  stty echo
set wallet_pass $expect_out(1,string)

  proc run_wallet {} {
    global wallet_name wallet_pass default_port port
      ### change command line here
      spawn ./bitshares_client --data-dir=delegate --p2p-port $port --server --httpport 9989 --rpcuser user --rpcpassword pass

      expect -exact "(wallet closed) >>> "
      send -- "about\r"
      expect -exact "(wallet closed) >>> "
      send -- "wallet_open $wallet_name\r"
      expect -exact "$wallet_name (locked) >>> "
      send -- "wallet_unlock 99999999\r"
      expect -exact "passphrase: "
      send -- "$wallet_pass\r"
      expect -exact "$wallet_name (unlocked) >>> "
      send -- "wallet_delegate_set_block_production ALL true\r"
      expect -exact "$wallet_name (unlocked) >>> "
      send -- "info\r"
      expect -exact "$wallet_name (unlocked) >>> "
      send -- "wallet_list_my_accounts\r"
      interact
      wait

      if { $port == $default_port } {
        set port [expr $port+1]
      } else {
        set port [expr $port-1]
      }
  }

while true {
  run_wallet
}
