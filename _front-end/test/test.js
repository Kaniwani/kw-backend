// CONFIG
casper.options.viewportSize = { width: 1600, height: 1050 };

// SETUP
var handlePageError = function(msg, trace) {
	casper.echo('Error: ' + msg, 'ERROR');
	for(var i=0; i<trace.length; i++) {
		var step = trace[i];
		casper.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
	}
};

casper.on('page.error', handlePageError);

// TESTS
var testCount = 3,
	title = 'login',
	username = 'duncantest1',
	password = 'dadedade';

casper.test.begin('KW Login test', testCount, function suite(test) {
	casper.start('http://localhost:8000/', function then() {
		test.assertTitleMatches(/login/i, 'Title matches "' + title + '".');
	});

	casper.waitForSelector('.login-form', function then() {
		test.assertExists('.login-form', 'Login form exists');
	});

	casper.then(function() {
		casper.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
  	casper.fillSelectors('.login-form', {
    	'input[name="username"]': username,
  	  'input[name="password"]': password
		}, true);
	})

	casper.then(function() {
		casper.waitForUrl(/kw\/$/, function then() {
			casper.echo('# Succesfully redirected to logged in home', 'INFO');
			test.assertSelectorHasText('.user-overview .name', username, 'User overview name matches ' + username);
		});
	});

	casper.run(function() { test.done(); });
});
