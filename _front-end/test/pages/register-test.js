casper.test.comment("Register page test.");
var helper = require("../djangocasper.js");

var	loginForm = '.login-form',
		username = 'registertest',
		password = 'password';

helper.scenario('/',
  function() {
    this.test.assertSelectorHasText('.link.-register', 'Register', "The home page has a Register button");
    this.click('.link.-register');
  },
  function() {
    helper.assertAbsUrl('/auth/register/', "After clicking Register link, we're redirected to the register page");
  },
  function() {
    this.test.assertSelectorHasText('.login-section .title', 'Register', "The section title is Register");
  },
  function() {
		casper.fillSelectors(loginForm, {
			'input[name="username"]': username,
			'input[name="email"]': 'register@test.com',
			'input[name="password1"]': password,
			'input[name="password2"]': password,
			// level 1 user with no vocab - WK might remove this inactive profile at some point
			'input[name="api_key"]': 'ac961ccd0c59c432f89951fb827de879'
		}, true);
	},
	function() {
		casper.waitForUrl(/kw\/$/, function() {
			casper.echo('# Succesfully redirected to logged in home', 'INFO');
		})
	},
 function() {
		casper.waitForSelector(loginForm, function() {
			this.test.assertExists(loginForm, 'Login form exists');
			casper.echo('# Submitting login form with username: ' + username + ', password: ' + password, 'COMMENT');
			casper.fillSelectors(loginForm, {
				'input[name="username"]': username,
				'input[name="password"]': password
			}, true);
		})
	},
	function() {
		casper.waitForUrl(/kw\/$/, function() {
			casper.echo('# Succesfully redirected to logged in home', 'INFO');
		})
	},
	function() {
		var	nameSelector = '.user-overview .name';
		casper.waitForSelector(nameSelector, function() {
			this.test.assertSelectorHasText(nameSelector, username, 'User overview name matches ' + username);
		});
	}
);

helper.run();
