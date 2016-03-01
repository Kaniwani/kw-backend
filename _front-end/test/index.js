var utils = require('utils'); //casper utils
var config = require('./config.js');
var handlers = require('./handlers.js');
var nav = require('./navigation.js');

// merge our config with defaults
utils.mergeObjects(casper.options, config);

// attach our custom event handlers
handlers();

// Tests
var login = require('./sections/login.js');
// var vocabulary = require('./sections/vocabulary.js')
// var settings = require('./sections/settings.js')


// whhhhhy do I have to update this argh
var testCount = 11;
casper.test.begin('----- ALL TESTS -----', testCount, function suite(test) {
	casper.start('http://localhost:8000/', function then() {
		login('duncantest1', 'dadedade');
	})
	// replace all these with actual page tests from separate files (that start with the navigation)
	.then(function() { nav.review(); })
	.then(function() { nav.vocab.levels(); })
	.then(function() { nav.vocab.srs(); })
	.then(function() { nav.vocab.level(); })
	.then(function() { nav.vocab.single(); })
	.then(function() { nav.contact(); })
	.then(function() { nav.settings(); })
	.then(function() { nav.about(); })
	.then(function() { nav.logout(); })

  .run(function() {
	  test.comment('----- COMPLETE -----\n');
    test.done();
  });
});
