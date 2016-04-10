casper.test.comment("Simple login form test.");
var helper = require("./djangocasper.js");

var username = 'duncantest',
		password = 'dadedade';

helper.scenario('/',
  function() {

		var	loginSelector = '.login-form';
		casper.waitForSelector(loginSelector, function() {
			this.test.assertExists(loginSelector, 'Login form exists');
			casper.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
			casper.fillSelectors(loginSelector, {
				'input[name="username"]': username,
				'input[name="password"]': password
			}, true);
		})

		.then(function() {
			casper.waitForUrl(/kw\/$/, function() {
				casper.echo('# Succesfully redirected to logged in home', 'INFO');
			})
		})

		.then(function() {
			var	nameSelector = '.user-overview .name';
			casper.waitForSelector(nameSelector, function() {
				this.test.assertSelectorHasText(nameSelector, username, 'User overview name matches ' + username);
			});
		});

  }
);

helper.run();
