import os
from casper.tests import CasperTestCase

from kw_webapp.tests.utils import create_user, create_profile

# if these are changed, will need to update variables in JS test files as well
test_username = "duncantest"
test_password = "dadedade"

# to skip BE tests run: manage.py test kw_webapp.tests.test_frontend_js

# util method
def testFile(filename):
    return os.path.join(os.path.dirname(__file__), "..", "..", "_front-end/test/", filename + ".js")

class AllFrontEndTests(CasperTestCase):

    def setUp(self):
        # This is the rough outline of how to create a user. This "setUp" function is called before every
        # single test is run. Any data you add to database in this method will be emptied out at the end of EVERY test.
        # The overall way a test runs is. setUp() -> test() -> tearDown()
        # https://github.com/dobarkod/django-casper#bypassing-log-in-procedure
        self.user = create_user(test_username)
        self.user.set_password(test_password)

        self.user.save()
        create_profile(self.user, "whatever", 2)

    def tearDown(self):
        pass

    def test_register(self):
        self.assertTrue(self.casper(testFile('register-test')))

    def test_login(self):
        self.assertTrue(self.casper(testFile('login-test')))

    def test_logged_in(self):
        self.client.login(username=test_username, password=test_password)
        self.assertTrue(self.casper(testFile('logged-in-test')))

    def test_about(self):
        self.client.login(username=test_username, password=test_password)
        self.assertTrue(self.casper(testFile('about-test')))


