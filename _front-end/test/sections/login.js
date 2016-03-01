var login = function(username, password) {

	casper.waitForSelector('.login-form', function() {
		this.test.assertExists('.login-form', 'Login form exists');
		casper.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
		casper.fillSelectors('.login-form', {
			'input[name="username"]': username,
			'input[name="password"]': password
		}, true);
	})

	.then(function() {
		casper.waitForUrl(/kw\/$/, function() {
			casper.echo('# Succesfully redirected to logged in home', 'INFO');
			this.test.assertSelectorHasText('.user-overview .name', username, 'User overview name matches ' + username);
		});
	});

};

module.exports = login;
