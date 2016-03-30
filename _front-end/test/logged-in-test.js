casper.test.comment("Logged in home test.");
var helper = require("./djangocasper.js"),
		username = 'duncantest',
		password = 'dadedade';

helper.scenario('/',
  function() {

		var	nameSelector = '.user-overview .name';
		casper.waitForSelector(nameSelector, function() {
			// user details has correct name
			this.test.assertSelectorHasText(nameSelector, username, '"' + nameSelector + '" matches ' + username);

			// there are 6 links when logged in
			this.test.assertEval(function() {
				return $('.nav-list .item').length === 6;
			})

			// first navbar link starts with text: Reviews
			this.test.assertEval(function() {
				return /^Reviews/.test($('.nav-list .item').first().text().trim());
			})

			// last navbar link item has text 'Logout'
			this.test.assertEval(function() {
		 		return $('.nav-list .item').last().find('.text').text() === 'Logout';
			})

		// NOTE: no reviews count - need to seed test user with vocab first?
		// this.test.assertEval(function() {
		// 	var reviewsLinkText = document.querySelector('#navReviewCount').textContent;
		// 	return /\d+/g.test(reviewsLinkText);
		// });

		})
  }
);

helper.run();
