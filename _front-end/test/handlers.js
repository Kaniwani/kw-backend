var handlers = function() {

	// if js error in current page scripts (ie. reviews.js)
	casper.on('page.error', function(msg, trace) {
		casper.echo('Error: ' + msg, 'ERROR');
		for(var i=0; i<trace.length; i++) {
			var step = trace[i];
			casper.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
		}
	});

	// take a screenshot of page last test failed on
	casper.test.on('fail', function() {
	  casper.capture('test/screenshots/fail.png');
	});

}

module.exports = handlers;
