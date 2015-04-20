refresh_order_book = function (text) {
      var precision_price = 5
      tab_bid = document.getElementById('order_book_bid');
      tab_ask = document.getElementById('order_book_ask');
      var order_bid_list = text["bid"];
      var order_ask_list = text["ask"];
      var rowCount = tab_bid.rows.length;
      for (var index = rowCount -1; index>0; index--) {
         tab_bid.deleteRow(index);
         }
      var rowCount = tab_ask.rows.length;
      for (var index = rowCount -1; index>0; index--) {
         tab_ask.deleteRow(index);
         }

      for (index in order_bid_list) {
        dataTR = tab_bid.insertRow();
        var price = order_bid_list[index]["price"]
        var volume = order_bid_list[index]["volume"]
        var balance = volume * price
        dataTR.insertCell(0).innerHTML = price.toFixed(precision_price);
        dataTR.insertCell(1).innerHTML = volume.toFixed(2);
        dataTR.insertCell(2).innerHTML = balance.toFixed(2);
      } 
      for (index in order_ask_list) {
        dataTR = tab_ask.insertRow();
        var price = order_ask_list[index]["price"]
        var volume = order_ask_list[index]["volume"]
        var balance = volume * price
        dataTR.insertCell(0).innerHTML = price.toFixed(precision_price);
        dataTR.insertCell(1).innerHTML = volume.toFixed(2);
        dataTR.insertCell(2).innerHTML = balance.toFixed(2);
      } 
};

Date.prototype.format = function(format) {
   var date = {
     "M+": this.getMonth() + 1,
     "d+": this.getDate(),
     "h+": this.getHours(),
     "m+": this.getMinutes(),
     "s+": this.getSeconds(),
     "q+": Math.floor((this.getMonth() + 3) / 3),
     "S+": this.getMilliseconds()
   };
   if (/(y+)/i.test(format)) {
     format = format.replace(RegExp.$1, (this.getFullYear() + '').substr(4 - RegExp.$1.length));
   }
   for (var k in date) {
     if (new RegExp("(" + k + ")").test(format)) {
       format = format.replace(RegExp.$1, RegExp.$1.length == 1
       ? date[k] : ("00" + date[k]).substr(("" + date[k]).length));
     }
   }
   return format;
}

time_format = function (text) {
   time = new Date(text+"Z")
   //time = new Date(time.getTime() - time.getTimezoneOffset()*60000)
   time_str = time.format('MM-dd hh:mm:ss')
   return time_str;
}
refresh_trx = function (text) {
      if (!text) return;
      tab = document.getElementById('transaction_history');
      var hisData = text;
      hisData.sort();
      for (index in hisData) {
        data = hisData[index];
        blockid = data.shift();
        time = time_format(data.shift())
        type = data.shift();
        price = data.shift().toFixed(5);
        volume = data.shift().toFixed(3);
        balance = (price*volume).toFixed(3)
        dataTR = tab.insertRow(1);
        dataTR.insertCell(0).innerHTML = time;
        dataTR.insertCell(1).innerHTML = blockid;
        dataTR.insertCell(2).innerHTML = type;
        dataTR.insertCell(3).innerHTML = price;
        dataTR.insertCell(4).innerHTML = volume;
        dataTR.insertCell(5).innerHTML = balance;
      } 
      try {
        while (true) {
          tab.deleteRow(41);
        }
      } catch (e) {
      }
};

try {
   var autobahn = require('autobahn');
} catch (e) {
   // when running in browser, AutobahnJS will
   // be included without a module system
}

var connection = new autobahn.Connection({
   url: 'ws://pusher.btsbots.com:8080/ws',
   realm: 'realm1'}
);

connection.onopen = function (session) {
   var quote="CNY", base="BTS";

   console.log("session open");

   session.call('btsbots.get_last', ['bts.orderbook.'+quote+'_'+base]).then(
        function (res) {
           refresh_order_book(res);
        }
   );
   session.call('btsbots.get_history', ['bts.orderbook.'+quote+'_'+base+".trx",20]).then(
        function (res) {
           refresh_trx(res);
        }
   );

   function on_order_book(args) {
      refresh_order_book(args[0]);
   }
   session.subscribe('bts.orderbook.'+quote+'_'+base, on_order_book);
   function on_trx(args) {
      refresh_trx([args[0]]);
   }
   session.subscribe('bts.orderbook.'+quote+'_'+base+".trx", on_trx);
};

connection.open();
