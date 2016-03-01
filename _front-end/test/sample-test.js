casper.test.comment("Simple integration test for casper and django.");
var helper = require("./djangocasper.js");

helper.scenario('/',
    function() {
        this.test.assertSelectorHasText('input[type="submit"]', 'Sign In',
            "The home page has a Login button");
        this.click('input[type="submit"]');
    },
    function() {
        helper.assertAbsUrl('/auth/login/?next=/',
            "After clicking Login, we're redirected to login page");
    }
);
helper.run();