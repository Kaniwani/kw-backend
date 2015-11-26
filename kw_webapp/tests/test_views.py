from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import TestCase, RequestFactory, Client

import kw_webapp
from kw_webapp.models import UserSpecific
from kw_webapp.tests.utils import create_user, create_userspecific
from kw_webapp.tests.utils import create_vocab


class TestViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = create_user("user1")
        self.factory = RequestFactory()
        self.cat_vocab = create_vocab("cat")

    def test_review_requires_login(self):
        request = self.factory.get('/kw/review/')
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        response = generic_view(request)
        self.assertEqual(response.status_code, 302)

    def test_recording_answer_works_on_correct_answer(self):
        us = create_userspecific(self.cat_vocab, self.user)

        # Generate and pass off the request
        request = self.factory.post('/kw/record_answer/',
                                    {'user_correct': "true", 'user_specific_id': us.id, 'wrong_before': 'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        generic_view(request)

        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = us.correct == 1 and us.streak == 1 and us.needs_review is False
        self.assertTrue(recorded_properly)

    def test_wrong_answer_records_failure(self):
        vocab = create_vocab("dog")
        us = create_userspecific(vocab, self.user)

        # Generate and pass off the request
        request = self.factory.post('/kw/record_answer/',
                                    {'user_correct': "false", 'user_specific_id': us.id, 'wrong_before': 'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        response = generic_view(request)

        # grab it again and ensure it's correct.
        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = (us.incorrect == 1 and us.streak == 0 and us.needs_review is True)
        self.assertTrue(recorded_properly)

    def test_nonexistent_user_specific_id_raises_error_in_record_answer(self):
        # Generate and pass off the request
        request = self.factory.post('/kw/record_answer/',
                                    {'user_correct': "true", 'user_specific_id': 150, 'wrong_before': 'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()

        self.assertRaises(Http404, generic_view, request)

        # TODO write tests for vocab page

        # def test_vocab_page_contains_only_unlocked_vocab(self):
        #     u = create_user("Tadgh")
        #     v1 = create_vocab("cat")
        #     r1 = create_reading(v1, "猫", "ねこ", 5)
        #     v2 = create_vocab("dog")
        #     r2 = create_reading(v2, "犬", "いぬ", 5)
        #     review = create_userspecific(v1, u)
        #     request = self.factory.get('/kw/vocabulary')
        #     request.user = u
        #     returned_response = kw_webapp.views.UnlockedVocab.as_view()(request).render().content
        #     self.assertIn("cat", str(returned_response))