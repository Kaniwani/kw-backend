casper.test.comment("Logged in home tests.");
var helper = require("../djangocasper.js");

helper.scenario('/',
  function() {
		var	nameSelector = '.user-overview .name';
		var username = 'duncantest';
		this.test.assertSelectorHasText(nameSelector, username, '"' + nameSelector + '" matches ' + username);
	},
	function() {
		var linksLength = casper.evaluate(function() {
			return $('.nav-list .item').length === 6;
		});
		this.test.assert(linksLength, 'There are 6 links when logged in');
	},
	function() {
		var firstLinkText = casper.evaluate(function() {
			return /^Reviews/.test($('.nav-list .item').first().text().trim());
		});
		this.test.assert(firstLinkText, 'First navbar link starts with text: Reviews');
	},
	function() {
		var lastLinkText = casper.evaluate(function() {
	 		return $('.nav-list .item').last().find('.text').text() === 'Logout';
		});
		this.test.assert(lastLinkText, 'Last navbar link item has text: Logout');
	},
	function() {
		// NOTE: no reviews count - need to seed test user with vocab first?
		// var reviewsCount = casper.evaluate(function() {
		// 	var text = $('#navReviewCount').text();
		// 	return /\d+/g.test(text) && parseInt(text) > 0;
		// });
		// this.test.assert(reviewsCount, 'Reviews nav link contains a positive integer');
		return true;
	}
);

helper.run();
