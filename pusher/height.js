try {
   var autobahn = require('autobahn');
} catch (e) {
   // when running in browser, AutobahnJS will
   // be included without a module system
}

var connection = new autobahn.Connection({
   url: 'ws://pusher.btsbots.com/ws',
   realm: 'realm1'}
);

connection.onopen = function (session) {

   console.log("session open");

   session.call('btsbots.get_last', ['btsbots.demo.height']).then(
        function (res) {
           document.getElementById('height').innerHTML = res;
           console.log("call last height: " + res);
        }
   );

   function on_height(args) {
      document.getElementById('height').innerHTML = args[0];
      console.log("on_height: height is " + args[0]);
   }
   session.subscribe('btsbots.demo.height', on_height);
};

connection.open();
