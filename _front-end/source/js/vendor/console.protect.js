/**
 * Protect window.console method calls, e.g. console is not defined on IE
 * unless dev tools are open, and IE doesn't define console.debug
 */
(function(){

  // Define an empty function
  var a = function(){};

  // A list of all the console methods (as of Chrome 39.0.2171.95 & 34.0.5)
  var methods = [
    "log",
    "assert",
    "debug",
    "info",
    "warn",
    "error",
    "dir",
    "dirxml",
    "trace",
    "group",
    "groupCollapsed",
    "groupEnd",
    "time",
    "timeEnd",
    "profile",
    "profileEnd",
    "count",
    "exception",
    "table",
    "markTimeline",
    "timeStamp",
    "clear",
    "memory",
    "timeline",
    "timelineEnd"
  ];

  if (typeof window.console === "undefined") {
    window.console = {};
  }

  // Loop through all the methods and define non-existing ones
  // using the empty function
  for(var i = 0; i < methods.length; i++) {
    if(typeof window.console[methods[i]] === "undefined") {
      window.console[methods[i]] = a;
    }
  }

}());