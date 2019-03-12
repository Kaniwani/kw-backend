import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from api.sync.WanikaniUserSyncer import WanikaniUserSyncer
from kw_webapp.models import Vocabulary, UserSpecific, Profile
from kw_webapp.wanikani import exceptions, make_api_call


class WanikaniUserSyncerV1(WanikaniUserSyncer):
    def __init__(self, profile):
        self.token = profile.api_key
        self.profile = profile
        self.logger = logging.getLogger(__name__)


    def sync_user_profile_with_wk(self):
        """
        Hits the WK api with user information in order to synchronize user metadata such as level and gravatar information.

        :param user: The user to sync their profile with WK.
        :return: boolean indicating the success of the API call.
        """

        api_string = self.build_user_information_api_string(self.profile.api_key)

        try:
            json_data = make_api_call(api_string)
        except exceptions.InvalidWaniKaniKey:
            self.profile.api_valid = False
            self.profile.save()
            return False

        user_info = json_data["user_information"]
        self.profile.title = user_info["title"]
        self.profile.join_date = datetime.utcfromtimestamp(user_info["creation_date"])
        self.profile.topics_count = user_info["topics_count"]
        self.profile.posts_count = user_info["posts_count"]
        self.profile.about = user_info["about"]
        self.profile.set_website(user_info["website"])
        self.profile.set_twitter_account(user_info["twitter"])
        self.profile.gravatar = user_info["gravatar"]
        self.profile.last_wanikani_sync_date = timezone.now()
        self.profile.api_valid = True

        if self.profile.follow_me:
            self.profile.unlocked_levels.get_or_create(level=user_info["level"])
            self.profile.handle_wanikani_level_change(user_info["level"])

        self.profile.save()

        self.logger.info("Synced {}'s Profile.".format(self.profile.user.username))

        return True

    def build_user_information_api_string(self, api_key):
        return "https://www.wanikani.com/api/user/{}/user-information".format(api_key)

    def sync_with_wk(self, full_sync=False):
        """
        Takes a user. Checks the vocab list from WK for all levels. If anything new has been unlocked on the WK side,
        it also unlocks it here on Kaniwani and creates a new review for the user.

        :param user_id: id of the user to sync
        :param full_sync:
        :return: None
        """
        # We split this into two seperate API calls as we do not necessarily know the current level until
        # For the love of god don't delete this next line
        self.logger.info("About to begin sync for user {}.".format(self.profile.user.username))
        profile_sync_succeeded = self.sync_user_profile_with_wk()
        if profile_sync_succeeded:
            if not full_sync:
                new_review_count, new_synonym_count = self.sync_recent_unlocked_vocab()
            else:
                new_review_count, new_synonym_count = self.sync_unlocked_vocab()

            return profile_sync_succeeded, new_review_count, new_synonym_count
        else:
            self.logger.warning(
             "Not attempting to sync, since API key is invalid, or user has indicated they do not want to be followed "
            )
            return profile_sync_succeeded, 0, 0

    def build_API_sync_string_for_api_key_for_levels(self, levels):
        """
        Given a user, build a vocabulary request string based on their api key, for a particular level.
        :param user: The related user.
        :param level: The level of vocabulary we want to update.
        :return: The fully formatted API string that will provide.
        """
        level_string = (
            ",".join(str(level) for level in levels) if isinstance(levels, list) else levels
        )
        api_call = "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(
            self.profile.api_key, level_string
        )
        api_call += ","
        return api_call

    def build_API_sync_string_for_user_for_levels(self, levels):
        return self.build_API_sync_string_for_api_key_for_levels(levels)

    def sync_recent_unlocked_vocab(self):
        if self.profile.unlocked_levels_list():
            levels = [
                level
                for level in range(self.profile.level - 2, self.profile.level + 1)
                if level in self.profile.unlocked_levels_list()
            ]
            if levels:
                request_string = self.build_API_sync_string_for_user_for_levels(levels)
                try:
                    json_data = make_api_call(request_string)
                    new_review_count, new_synonym_count = self.process_vocabulary_response_for_user(
                        json_data
                    )
                    return new_review_count, new_synonym_count
                except exceptions.InvalidWaniKaniKey:
                    self.profile.api_valid = False
                    self.profile.save()
                except exceptions.WanikaniAPIException as e:
                    self.logger.warn(
                        "Couldn't sync recent vocab for {}".format(self.profile.user.username), e
                    )
        return 0, 0
        pass

    def get_level_pages(self, levels):
        page_size = 5
        return [levels[i : i + page_size] for i in range(0, len(levels), page_size)]

    def sync_unlocked_vocab(self):
        if self.profile.unlocked_levels_list():
            pages = self.get_level_pages(self.profile.unlocked_levels_list())
            new_review_count = new_synonym_count = 0
            for page in pages:
                request_string = self.build_API_sync_string_for_user_for_levels(page)
                self.logger.info(
                    "Creating sync string for user {}: {}".format(
                        self.profile.user.username, self.profile.api_key
                    )
                )
                try:
                    response = make_api_call(request_string)
                    current_page_review_count, current_page_synonym_count = self.process_vocabulary_response_for_user(
                        response
                    )
                    new_review_count += current_page_review_count
                    new_synonym_count += current_page_synonym_count
                except exceptions.InvalidWaniKaniKey:
                    self.profile.api_valid = False
                    self.profile.save()
                except exceptions.WanikaniAPIException as e:
                    self.logger.error(
                        "Couldn't sync recent vocab for {}".format(self.profile.user.username), e
                    )
            return new_review_count, new_synonym_count
        else:
            return 0, 0

    def sync_study_materials(self):
        """
        Syncs up the user's synonyms for WK for all levels that they have currently unlocked.

        :param user: The user to pull all synonyms for
        :return: None
        """

        if self.profile :
            for level in self.profile.unlocked_levels_list():
                self.pull_user_synonyms_by_level(level)
                self.logger.info("Pulled user synonyms for {}".format(self.profile.user.username))
        else:
            #TODO move this elsewhere? This full synonym sync code.
            for profile in Profile.objects.all():
                if len(profile.api_key) == 32:
                    user = profile.user
                    for level in profile.unlocked_levels_list():
                        self.pull_user_synonyms_by_level(level)
                    self.logger.info("Pulled user synonyms for {}".format(user.username))

    def sync_top_level_vocabulary(self):
        """
        This is intentionally left blank, as we do not trust the V1 syncer data,
        since it relies on V1 API data, which is less useful than V2 API data.
        """
        pass

    def unlock_vocab(self, levels):
        """
        I don't like duplicating code like this, but its for the purpose of reducing API call load on WaniKani. It's a
        hassle if the user caps out.
        :param user: user to add vocab to. :param levels: requested level unlock. This can
        also be a list. :return: unlocked count, locked count
        """

        api_call_string = self.build_API_sync_string_for_user_for_levels(levels)
        response = make_api_call(api_call_string)
        unlocked_this_request, total_unlocked, locked = self.process_vocabulary_response_for_unlock(response)
        return unlocked_this_request, total_unlocked, locked

    def get_wanikani_level(self):
        api_string = self.build_user_information_api_string(self.profile.api_key)

        json_data = make_api_call(api_string)
        user_info = json_data["user_information"]
        return user_info["level"]


    def process_vocabulary_response_for_user(self, json_data):
        """
        Given a response object from Requests.get(), iterate over the list of vocabulary, and synchronize the user.
        :param json_data:
        :param user:
        :return:
        """
        new_review_count = 0
        new_synonym_count = 0
        vocab_list = json_data["requested_information"]
        # Filter items the user has not unlocked.
        vocab_list = [
            vocab_json
            for vocab_json in vocab_list
            if vocab_json["user_specific"] is not None
        ]

        for vocabulary_json in vocab_list:
            if self.profile.follow_me:
                review, created, synonyms_added_count = self.process_single_item_from_wanikani(
                    vocabulary_json
                )
                synonyms_added_count += new_synonym_count
                if created:
                    new_review_count += 1
                review.save()
            else: # User does not want to be followed, so we prevent creation of new vocab, and sync only synonyms instead.
                vocabulary, created = self.get_or_create_vocab_by_json(vocabulary_json)
                new_review, synonyms_added_count = self.associate_synonyms_to_vocab(vocabulary, vocabulary_json['user_specific'])
                new_synonym_count += synonyms_added_count
        self.logger.info("Synced Vocabulary for {}".format(self.profile.user.username))
        return new_review_count, new_synonym_count


    def process_single_item_from_wanikani(self, vocabulary):
        user_specific = vocabulary["user_specific"]
        vocab, _ = self.import_vocabulary_from_json(vocabulary)
        review, created = self.associate_vocab_to_user(vocab)
        review, synonyms_added_count = self.synchronize_synonyms(review, user_specific)
        review.wanikani_srs = user_specific["srs"]
        review.wanikani_srs_numeric = user_specific["srs_numeric"]
        review.wanikani_burned = user_specific["burned"]
        review.save()
        return review, created, synonyms_added_count

    def import_vocabulary_from_json(self, vocabulary):
        vocab, is_new = self.get_or_create_vocab_by_json(vocabulary)
        vocab = self.update_local_vocabulary_information(vocab, vocabulary)
        return vocab, is_new

    def get_or_create_vocab_by_json(self,vocab_json):
        """
        if lookup by meaning fails, create a new vocab object and return it. See JSON Example here
        https://www.wanikani.com/api
        :param: vocab_json: a dictionary holding the information needed to create new
        vocabulary.
        :return: vocabulary object.
        """

        try:
            vocab = self.get_vocab_by_kanji(vocab_json["character"])
            created = False
        except Vocabulary.DoesNotExist:
            vocab = self.create_new_vocabulary(vocab_json)
            created = True
        return vocab, created

    def get_vocab_by_kanji(self, kanji):
        v = Vocabulary.objects.filter(readings__character=kanji).distinct()
        number_of_vocabulary = v.count()
        if number_of_vocabulary > 1:
            error = "Found multiple Vocabulary with identical kanji with ids: [{}]".format(
                ", ".join([str(vocab.id) for vocab in v])
            )
            self.logger.error(error)
            raise Vocabulary.MultipleObjectsReturned(error)
        elif number_of_vocabulary == 0:
            # TODO remove V1 syncer capability to ever update acutal infromation.
            # TODO leave this for the V2 syncer, as it is more accurate.
            self.logger.error(
                "While attempting to get vocabulary {} we could not find it!".format(kanji)
            )
            raise Vocabulary.DoesNotExist("Couldn't find meaning: {}".format(kanji))
        else:
            return v.first()

    def create_new_vocabulary(self, vocabulary_json):
        """
        Creates a new vocabulary based on a json object provided by Wanikani and returns this vocabulary.
        :param vocabulary_json: A JSON object representing a single vocabulary, as provided by Wanikani.
        :return: The newly created Vocabulary object.
        """
        meaning = vocabulary_json["meaning"]
        vocab = Vocabulary.objects.create(meaning=meaning)
        vocab = self.update_local_vocabulary_information(vocab, vocabulary_json)
        return vocab

    def update_local_vocabulary_information(self, vocab, vocabulary_json):

        kana_list = [reading.strip() for reading in vocabulary_json["kana"].split(",")]
        # Update the local meaning based on WK meaning
        meaning = vocabulary_json["meaning"]
        vocab.meaning = meaning

        character = vocabulary_json["character"]
        level = vocabulary_json["level"]
        for reading in kana_list:
            new_reading, created = vocab.readings.get_or_create(
                kana=reading, character=character
            )
            new_reading.level = level
            new_reading.save()
            if created:
                self.logger.info(
                    """Created new reading: {}, level {}
                                         associated to vocab {}""".format(
                        new_reading.kana, new_reading.level, new_reading.vocabulary.meaning
                    )
                )
        vocab.save()
        return vocab

    def associate_vocab_to_user(self, vocab):
        """
        takes a vocab, and creates a UserSpecific object for the user based on it. Returns the vocab object.
        :param vocab: the vocabulary object to associate to the user.
        :param user: The user.
        :return: the vocabulary object after association to the user
        """
        try:
            review, created = UserSpecific.objects.get_or_create(
                vocabulary=vocab, user=self.profile.user
            )
            if created:
                review.needs_review = True
                review.next_review_date = timezone.now()
                review.save()
            return review, created

        except UserSpecific.MultipleObjectsReturned:
            us = UserSpecific.objects.filter(vocabulary=vocab, user=self.profile.user)
            for u in us:
                self.logger.error(
                    "during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(
                        self.profile.user.username, u
                    )
                )
            return None, None

    def synchronize_synonyms(self, review, user_specific_json):
        synonym_count = 0
        incoming_synonyms = user_specific_json["user_synonyms"]
        if incoming_synonyms is None or len(incoming_synonyms) == 0:
            return review, synonym_count

        # Add new synonyms
        for synonym in incoming_synonyms:
            _, created = review.meaning_synonyms.get_or_create(text=synonym)
            if created:
                synonym_count += 1

        # Delete Stale Synonyms
        for synonym in review.meaning_synonyms.all():
            if synonym.text not in user_specific_json["user_synonyms"]:
                synonym.delete()
                synonym_count -= 1

        return review, synonym_count

    def associate_synonyms_to_vocab(self, vocab, user_specific_json):
        review = None
        synonym_count = 0

        try:
            review = UserSpecific.objects.get(user=self.profile.useruser, vocabulary=vocab)
            _, synonym_count = self.synchronize_synonyms(review, user_specific_json)
        except UserSpecific.DoesNotExist:
            pass

        return review, synonym_count

    def process_vocabulary_response_for_unlock(self, json_data):
        """
        Given a JSON Object from WK, iterate over the list of vocabulary, and synchronize the user.
        :param user:
        :param json_data:
        :return:
        """
        vocab_list = json_data["requested_information"]
        original_length = len(vocab_list)
        vocab_list = [
            vocab_json
            for vocab_json in vocab_list
            if vocab_json["user_specific"] is not None
        ]  # filters out locked items.
        total_unlocked_count = 0
        unlocked_this_request = 0
        for vocabulary_json in vocab_list:
            total_unlocked_count += 1
            _, created, _ = self.process_single_item_from_wanikani(vocabulary_json)
            if created:
                unlocked_this_request += 1

        self.logger.info("Unlocking level for {}".format(self.profile.user.username))
        remaining_locked = original_length - total_unlocked_count
        return unlocked_this_request, total_unlocked_count, remaining_locked


    def pull_user_synonyms_by_level(self, level):
        """
        Retrieves vocabulary list from the WK API, specifically searching to pull in synonyms.

        :param user: User to pull WK synonyms or
        :param level: The level for synonyms that should be pulled
        :return: None
        """
        request_string = self.build_API_sync_string_for_user_for_levels(level)
        try:
            json_data = make_api_call(request_string)
            vocabulary_list = json_data["requested_information"]
            for vocabulary in vocabulary_list:
                meaning = vocabulary["meaning"]
                if (
                        vocabulary["user_specific"]
                        and vocabulary["user_specific"]["user_synonyms"]
                ):
                    try:
                        review = UserSpecific.objects.get(
                            user=self.profile.user, vocabulary__meaning=meaning
                        )
                        for synonym in vocabulary["user_specific"]["user_synonyms"]:
                            review.meaning_synonyms.get_or_create(text=synonym)
                        review.save()
                    except UserSpecific.DoesNotExist as e:
                        self.logger.error(
                            "Couldn't pull review during a synonym sync: {}".format(e)
                        )
                    except KeyError as e:
                        self.logger.error("No user_specific or synonyms?: {}".format(json_data))
                    except UserSpecific.MultipleObjectsReturned:
                        reviews = UserSpecific.objects.filter(
                            user=self.profile.user, vocabulary__meaning=meaning
                        )
                        for review in reviews:
                            self.logger.error(
                                "Found something janky! Multiple reviews under 1 vocab meaning?!?: {}".format(
                                    review
                                )
                            )

        except exceptions.InvalidWaniKaniKey:
            self.profile.api_valid = False
            self.profile.save()
        except exceptions.WanikaniAPIException as e:
            self.logger.warning("Couldnt pull user synonyms for {}".format(self.profile.user.username), e)
