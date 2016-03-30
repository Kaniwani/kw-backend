casper.test.comment("Logged in home test.");
var helper = require("./djangocasper.js"),
		username = 'duncantest',
		password = 'dadedade';

helper.scenario('/',
  function() {
		var	nameSelector = '.user-overview .name';
		casper.waitForSelector(nameSelector, function() {
			this.test.assertSelectorHasText(nameSelector, username, 'User overview name matches ' + username);
		});

/*		.then(function() {

		});
*/
  }
);

helper.run();
