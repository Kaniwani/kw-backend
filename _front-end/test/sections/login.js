var testCount = 11,
		title = 'login',
		c = config;

var login = function() {
	casper.test.begin('KW Login test', testCount, function suite(test) {
		casper.start('http://localhost:8000/', function then() {
			test.assertTitleMatches(/login/i, 'Title matches "' + title + '".');
		});

		casper.waitForSelector('.login-form', function then() {
			test.assertExists('.login-form', 'Login form exists');
		});

		casper.then(function() {
			casper.echo('# Submitting login form with username: ' + c.username + ', password: ' + c.password, 'COMMENT');
			casper.fillSelectors('.login-form', {
				'input[name="username"]': c.username,
				'input[name="password"]': c.password
			}, true);
		})

		casper.then(function() {
			casper.waitForUrl(/kw\/$/, function then() {
				casper.echo('# Succesfully redirected to logged in home', 'INFO');
				test.assertSelectorHasText('.user-overview .name', c.username, 'User overview name matches ' + c.username);
			});
		});

		// just checking them initially for now
		casper.then(function() { navigateTo.review(); });
		casper.then(function() { navigateTo.vocab.levels(); });
		casper.then(function() { navigateTo.vocab.srs(); });
		casper.then(function() { navigateTo.vocab.level(); });
		casper.then(function() { navigateTo.about(); });
		casper.then(function() { navigateTo.contact(); });
		casper.then(function() { navigateTo.settings(); });
		casper.then(function() { navigateTo.logout(); });

		casper.run(function() { test.done(); });
	});
};

module.exports = login;
