casper.test.comment("Simple login form test.");
var helper = require("./djangocasper.js");

var username = 'duncantest',
		password = 'dadedade';

helper.scenario('/',
  function() {
		casper.waitForSelector('.login-form', function() {
			this.test.assertExists('.login-form', 'Login form exists');
			casper.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
			casper.fillSelectors('.login-form', {
				'input[name="username"]': username,
				'input[name="password"]': password
			}, true);
		})

		.then(function() {
			casper.waitForSelector('.user-overview .name', function() {
				this.test.assertSelectorHasText('', username, 'User overview name matches ' + username);
			});
		});
  }
);

helper.run();
