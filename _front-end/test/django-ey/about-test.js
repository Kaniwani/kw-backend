casper.test.comment("About page tests.");
var helper = require("./djangocasper.js");

helper.scenario('/kw/about',
  function() {

		var	titleSelector = '.about-section .title';
		var hasText = 'this all about';
		casper.waitForSelector(titleSelector, function() {
			// user details has correct name
			this.test.assertSelectorHasText(titleSelector, hasText, '"' + titleSelector + '" contains ' + hasText);

			var donateExists = casper.evaluate(function() {
				return $('.donate-block form').length > 0;
			})
			this.test.assert(donateExists, 'The donate form exists');

		})
  }
);

helper.run();
