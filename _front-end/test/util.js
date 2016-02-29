var handlePageError = function(msg, trace) {
	casper.echo('Error: ' + msg, 'ERROR');
	for(var i=0; i<trace.length; i++) {
		var step = trace[i];
		casper.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
	}
};

module.exports = {
	handlePageError: handlePageError
}
