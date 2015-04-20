refresh_order_book = function (text) {
      var precision_price = 7
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

   console.log('btsbots.demo.order_book_'+quote+'_'+base);
   session.call('btsbots.get_last', ['btsbots.demo.order_book_'+quote+'_'+base]).then(
        function (res) {
           refresh_order_book(res);
        }
   );

   function on_order_book(args) {
      refresh_order_book(args[0]);
   }
   session.subscribe('btsbots.demo.order_book_'+quote+'_'+base, on_order_book);
};

connection.open();
