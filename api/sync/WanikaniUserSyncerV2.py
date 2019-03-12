import logging

from django.contrib.auth.models import User
from django.utils import timezone
from wanikani_api.client import Client as WkV2Client
from wanikani_api.exceptions import InvalidWanikaniApiKeyException

from api.sync.WanikaniUserSyncer import WanikaniUserSyncer
from kw_webapp.models import Vocabulary, UserSpecific


class WanikaniUserSyncerV2(WanikaniUserSyncer):
    def __init__(self, profile):
        self.logger = logging.getLogger(__name__)
        self.profile = profile
        self.user = self.profile.user
        self.client = WkV2Client(profile.api_key_v2)

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
        user = User.objects.get(pk=self.user.id)
        self.logger.info("About to begin sync for user {}.".format(user.username))
        profile_sync_succeeded = self.sync_user_profile_with_wk()
        if profile_sync_succeeded:
            if not full_sync:
                new_review_count = self.sync_recent_unlocked_vocab()
            else:
                new_review_count = self.sync_unlocked_vocab()

            updated_synonym_count = self.sync_study_materials()
            return profile_sync_succeeded, new_review_count, updated_synonym_count
        else:
            self.logger.warning(
                "Not attempting to sync, since API key is invalid, or user has indicated they do not want to be "
                "followed "
            )
            return profile_sync_succeeded, 0

    def sync_user_profile_with_wk(self):
        """
        Hits the WK api with user information in order to synchronize user metadata such as level and gravatar
        information.

        :param user: The user to sync their profile with WK.
        :return: boolean indicating the success of the API call.
        """
        try:
            profile_info = self.client.user_information()
        except InvalidWanikaniApiKeyException:
            self.user.profile.api_valid = False
            self.user.profile.save()
            return False

        self.user.profile.join_date = profile_info.started_at
        self.user.profile.last_wanikani_sync_date = timezone.now()
        self.user.profile.api_valid = True

        if self.user.profile.follow_me:
            self.user.profile.unlocked_levels.get_or_create(level=profile_info.level)
            self.user.profile.handle_wanikani_level_change(profile_info.level)

        self.user.profile.save()

        self.logger.info("Synced {}'s Profile.".format(self.user.username))
        return True

    def sync_recent_unlocked_vocab(self):
        if self.user.profile.unlocked_levels_list():
            # We look over the last 3 levels
            levels = [
                level
                for level in range(self.user.profile.level - 2, self.profile.level + 1)
                if level in self.user.profile.unlocked_levels_list()
            ]
            if levels:
                try:
                    assignments = self.client.assignments(subject_types="vocabulary", levels=levels, fetch_all=True)
                    new_review_count, total_unlocked, total_locked = self.process_vocabulary_response_for_user_v2(
                        assignments
                    )
                    return new_review_count
                except InvalidWanikaniApiKeyException:
                    self.user.profile.api_valid = False
                    self.user.profile.save()
                except Exception as e:
                    self.logger.warning(
                        "Couldn't sync recent vocab for {}".format(self.user.username), e
                    )
        return 0, 0

    def process_vocabulary_response_for_user_v2(self, assignments):
        """
        Given a response object from Requests.get(), iterate over the list of vocabulary, and synchronize the user.
        :param json_data:
        :param user:
        :return:
        """
        new_review_count = 0
        unlocked_count = 0
        locked_count = 0
        # Filter items the user has not unlocked.
        for assignment in assignments:
            # We don't port over stuff the user has never looked at
            if assignment.started_at is None:
                locked_count += 1
                continue
            # If the user is being
            if self.profile.follow_me:
                review, created = self.process_single_item_from_wanikani_v2(assignment)
                if created:
                    new_review_count += 1
                unlocked_count += 1
                review.save()
        self.logger.info("Synced Vocabulary for {}".format(self.user.username))

        return new_review_count, unlocked_count, locked_count

    def process_single_item_from_wanikani_v2(self, assignment):
        try:
            vocab = Vocabulary.objects.get(wk_subject_id=assignment.subject_id)
        except Vocabulary.DoesNotExist:
            self.logger.error(f"Attempted to add a UserSpecific for subject ID: {assignment.subject_id} but failed as we don't have it.")
            return None, False
        review, created = self.get_or_create_review_for_user(vocab)
        if review.is_assignment_out_of_date(assignment):
            review.reconcile_assignment(assignment)
        return review, created #Note that synonym added count will need to be fixed.

    # TODO migrate this to class manager in ORM?
    def get_or_create_review_for_user(self, vocab):
        """
        takes a vocab, and creates a UserSpecific object for the user based on it. Returns the vocab object.
        :param vocab: the vocabulary object to associate to the user.
        :param user: The user.
        :return: the vocabulary object after association to the user
        """
        try:
            review, created = UserSpecific.objects.get_or_create(
                vocabulary=vocab, user=self.user
            )
            if created:
                review.needs_review = True
                review.next_review_date = timezone.now()
                review.save()
            return review, created

        except UserSpecific.MultipleObjectsReturned:
            us = UserSpecific.objects.filter(vocabulary=vocab, user=self.user)
            for u in us:
                self.logger.error(
                    "during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(
                        self.user.username, u
                    )
                )
            return None, None

    def sync_study_materials(self):
        self.logger.info(f"About to synchronize all synonyms for {self.user.username}")
        study_materials = self.client.study_materials(subject_types="vocabulary", fetch_all=True)
        updated_synonym_count = 0
        for study_material in study_materials:
            try:
                review = UserSpecific.objects.get(user=self.user, vocabulary__wk_subject_id=study_material.subject_id)
            except UserSpecific.DoesNotExist:
                pass
            else:
                if review.is_study_material_out_of_date(study_material):
                    review.reconcile_study_material(study_material)
                    updated_synonym_count += 1

        self.logger.info(f"Updated {updated_synonym_count} synonyms for {self.user.username}")
        return updated_synonym_count

    def sync_unlocked_vocab(self):
        if self.profile.unlocked_levels_list():
            new_review_count = 0

            self.logger.info(
                "Creating sync string for user {}: {}".format(
                    self.user.username, self.profile.api_key_v2
                )
            )
            try:
                assignments = self.client.assignments(subject_types="vocabulary", fetch_all=True)

                new_review_count, total_unlocked, total_locked = self.process_vocabulary_response_for_user_v2(assignments)
            except InvalidWanikaniApiKeyException:
                self.profile.api_valid = False
                self.profile.save()

            return new_review_count
        else:
            return 0

    def sync_top_level_vocabulary(self):
        self.logger.info("Beginning Subject Sync from WK API")
        try:
            updated_vocabulary_count = 0
            created_vocabulary_count = 0
            vocabulary = self.client.subjects(types="vocabulary")
            for remote_vocabulary in vocabulary:
                try:
                    local_vocabulary = Vocabulary.objects.get(wk_subject_id=remote_vocabulary.id)
                    if local_vocabulary.is_out_of_date(remote_vocabulary):
                        local_vocabulary.reconcile(remote_vocabulary)
                        updated_vocabulary_count += 1
                except Vocabulary.DoesNotExist as e:
                    local_vocabulary = Vocabulary.objects.create(wk_subject_id=remote_vocabulary.id)
                    local_vocabulary.reconcile()
                    created_vocabulary_count += 1
            return updated_vocabulary_count
        except InvalidWanikaniApiKeyException:
            self.logger.error("Couldn't synchronize vocabulary, as the API key is out of date.")
            return 0

    def unlock_vocab(self, levels):
        new_assignments = self.client.assignments(levels=levels)
        return self.process_vocabulary_response_for_user_v2(new_assignments)

    def get_wanikani_level(self):
        user_info = self.client.user_information()
        return user_info.level


