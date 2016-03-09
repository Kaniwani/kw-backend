casper.test.comment("Simple integration test for casper and django.");
var helper = require("./djangocasper.js");

helper.scenario('/',
    function() {
        this.test.assertSelectorHasText('.link.-register', 'Register',
            "The home page has a Register button");
        this.click('.link.-register');
    },
    function() {
        helper.assertAbsUrl('/auth/register/',
            "After clicking Register link, we're redirected to the register page");
    }
);
helper.run();
