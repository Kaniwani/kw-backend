var handlers = function() {

	casper.on('page.error', function(msg, trace) {
		casper.echo('Error: ' + msg, 'ERROR');
		for(var i=0; i<trace.length; i++) {
			var step = trace[i];
			casper.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
		}
	});

	casper.on('http.status.404', function(resource) {
	  casper.echo(resource.url + ' was 404');
	})

	casper.test.on('fail', function() {
	  casper.capture('test/screenshots/fail.png');
	});

}

module.exports = handlers;
