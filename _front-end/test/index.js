var _ = require('lodash');
var config = require('./config.js');
var util = require('./util.js');
var navigateTo = require('./navigation.js');

// merge our config with defaults
_.assign(casper.options, config);

// Setup
casper.on('page.error', util.handlePageError);

// Tests
var login = require('./sections/login.js');

// all basic nav tests are in login at the moment
// need to decide on a method of chaining tests in different files while remaining logged in

login();

// TODO:
// home()
// vocab()
// vocablevels()
// etc
