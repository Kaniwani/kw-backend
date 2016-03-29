import os
from casper.tests import CasperTestCase

from kw_webapp.tests.utils import create_user, create_profile

test_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "_front-end/test/login-test.js")

class AllFrontEndTests(CasperTestCase):

    def setUp(self):
        # This is the rough outline of how to create a user. This "setUp" function is called before every
        # single test is run. Any data you add to database in this method will be emptied out at the end of EVERY test.
        # The overall way a test runs is. setUp() -> test() -> tearDown()
        # https://github.com/dobarkod/django-casper#bypassing-log-in-procedure
        self.user = create_user("duncantest")
        self.user.set_password("dadedade")

        self.user.save()
        create_profile(self.user, "whatever", 15)

    def tearDown(self):
        pass

    def test_index(self):
        self.assertTrue(self.casper(test_file_path))


# to skip BE tests use
# manage.py test kw_webapp.tests.test_frontend_js

# to run a single test
# you could make a django function test_some_css_aspect(): which uses a specific .js test file.
