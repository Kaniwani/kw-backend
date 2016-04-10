function buildNav(urlFragment, title) {
	var url = config.baseUrl + urlFragment;

	return function() {
		casper.open(url)
		  .then(function() {
		  	comment(url);
		  	landedSafely(title);
	  });
	};
}

function comment() {
	casper.echo('# Navigated to ' + casper.getTitle(), 'COMMENT');
};

function landedSafely(title) {
	casper.test.assertTitleMatches(RegExp(title, 'gi'), 'Title includes "' + title + '".');
}

var	home = buildNav('', 'KaniWani');
var	review = buildNav('kw/review', 'review');
var	vocabLevels = buildNav('kw/vocabulary/', 'vocab');
var	vocabLevel = buildNav('kw/vocabulary/1/', 'vocab');
var	vocabSrs = buildNav('kw/vocabulary/apprentice/', 'vocab');
var	vocabSingle = buildNav('kw/vocabulary/大/', 'vocab');
var	about = buildNav('kw/about/', 'about');
var	settings = buildNav('kw/settings/', 'settings');
var	contact = buildNav('contact', 'contact');
var	logout = buildNav('auth/logout/', 'login');


module.exports = {
	home: home,
	review: review,
	vocab: {
		levels: vocabLevels,
		level: vocabLevel,
		srs: vocabSrs,
		single: vocabSingle
	},
	about: about,
	contact: contact,
	settings: settings,
	logout: logout
}
