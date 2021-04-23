from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from kw_webapp.tasks import set_manual_reading_whitelists

from kw_webapp.tests.utils import (
    create_user,
    create_profile,
    create_vocab,
    create_reading,
    create_review,
)


class TestMeaningSynonymApi(APITestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 5)
        self.review = create_review(self.vocabulary, self.user)

    def test_manual_master_synonyms_work(self):
        vocabulary_one = create_vocab("mother")
        create_reading(vocabulary_one, "おかあさん", "おかあさん", 1)
        create_reading(vocabulary_one, "はは2", "はは2", 1)

        vocabulary_two = create_vocab("mom")
        create_reading(vocabulary_two, "はは2", "はは2", 1)
        create_reading(vocabulary_two, "はは3", "はは3", 1)
        create_reading(vocabulary_two, "はは4", "はは4", 1)

        set_manual_reading_whitelists(vocabulary_two, vocabulary_one)

        vocabulary_two.refresh_from_db()
        vocabulary_one.refresh_from_db()
        
        self.assertEqual(vocabulary_two.manual_reading_whitelist, "おかあさん")
        self.assertTrue("はは4" in vocabulary_one.manual_reading_whitelist)
        self.assertTrue("はは3" in vocabulary_one.manual_reading_whitelist)

    def test_user_can_CRUD_all_their_own_synonyms(self):
        self.client.force_login(self.user)

        # Create
        synonym = {"review": self.review.id, "text": "My fancy synonym"}
        response = self.client.post(
            reverse("api:meaning-synonym-list"), data=synonym
        )
        self.assertEqual(response.status_code, 201)

        # Read
        self.assertEqual(self.review.synonyms_string(), "My fancy synonym")
        response = self.client.get(reverse("api:meaning-synonym-list"))
        self.assertEqual(response.status_code, 200)
        data = response.data
        synonym = data["results"][0]
        self.assertEqual(len(data["results"]), 1)

        # Update
        synonym["text"] = "A different fancy synonym"
        response = self.client.put(
            reverse("api:meaning-synonym-detail", args=(synonym["id"],)),
            data=synonym,
        )

        self.assertEqual(response.status_code, 200)
        # Double check update worked...
        self.review.refresh_from_db()
        self.assertEqual(
            self.review.synonyms_string(), "A different fancy synonym"
        )
        self.assertEqual(len(self.review.synonyms_list()), 1)

        # Delete
        self.client.delete(
            reverse("api:meaning-synonym-detail", args=(synonym["id"],))
        )
        self.review.refresh_from_db()
        self.assertEqual(len(self.review.synonyms_list()), 0)

    def test_another_user_cannot_CRUD_the_users_synonyms(self):
        self.client.force_login(self.user)
        sneaky_user = create_user("sneakster")
        create_profile(sneaky_user, "any key", 5)

        # Lets have the client create their own synonym.
        synonym = {"review": self.review.id, "text": "My fancy synonym"}
        response = self.client.post(
            reverse("api:meaning-synonym-list"), data=synonym
        )
        self.assertEqual(response.status_code, 201)

        # Make sure that the sneaky user CANNOT read it.
        self.client.force_login(sneaky_user)
        synonym_id = self.review.meaning_synonyms.first().id
        response = self.client.get(
            reverse("api:meaning-synonym-detail", args=(synonym_id,))
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            reverse("api:meaning-synonym-detail", args=(synonym_id,))
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            reverse("api:meaning-synonym-detail", args=(synonym_id,))
        )
        self.assertEqual(response.status_code, 404)
