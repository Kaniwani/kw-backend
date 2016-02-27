// CONFIG

casper.options.viewportSize = {width: 1600, height: 1050};

// UTIL
var handlePageError = function(msg, trace) {
   casper.echo('Error: ' + msg, 'ERROR');
   for(var i=0; i<trace.length; i++) {
       var step = trace[i];
       casper.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
   }
};

var handleTimeOut = function(msg) {
	casper.echo(msg + ' test Timed out');
};

// SETUP
casper.on('page.error', handlePageError);


// TESTS
var textCount = 3;
casper.test.begin('KW Login test', textCount, function suite(test) {
	var username = 'duncantest1',
			password = 'dadedade';

	casper.start('http://localhost:8000/', function then() {
		var title = 'login';
		test.assertTitleMatches(/login/i, 'Title matches "' + title + '".');
	});

	casper.waitForSelector('.login-form', function then() {
		test.assertExists('.login-form', 'Login form exists');
		this.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
  	this.fillSelectors('.login-form', {
    	'input[name="username"]': username,
  	  'input[name="password"]': password
		}, true);
	});

	casper.then(function() {
		casper.waitForUrl(/kw\/$/, function then() {
				this.echo('# Succesfully redirected to logged in home', 'INFO');
				test.assertSelectorHasText('.user-overview .name', username, 'User overview name matches ' + username);
			},
			function onTimeOut() { this.echo('Waiting for logged in home url timed out', "ERROR"); },
			30000)
	});

	casper.run(function() {test.done();});
});
