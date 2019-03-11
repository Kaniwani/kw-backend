import logging

from django.contrib.auth.models import User

from api.sync.WanikaniUserSyncer import WanikaniUserSyncer


class WanikaniUserSyncerV1(WanikaniUserSyncer):
    def __init__(self, profile):
        self.logger = logging.getLogger(__name__)

    def sync_user_profile_with_wk(self):
        pass

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
        user = User.objects.get(pk=user_id)
        logger.info("About to begin sync for user {}.".format(user.username))
        profile_sync_succeeded = sync_user_profile_with_wk(user)
        if profile_sync_succeeded:
            if not full_sync:
                new_review_count = sync_recent_unlocked_vocab_with_wk(
                    user
                )
            else:
                new_review_count = sync_unlocked_vocab_with_wk(user)

            return profile_sync_succeeded, new_review_count
        else:
            logger.warning(
                "Not attempting to sync, since API key is invalid, or user has indicated they do not want to be followed "
            )
            return profile_sync_succeeded, 0, 0

        def sync_recent_unlocked_vocab(self):
            pass

        def sync_unlocked_vocab(self):
            pass

        def sync_study_materials(self):
            pass

        def sync_top_level_vocabulary(self):
            pass

    def unlock_vocab(self, levels):
        pass

    def get_wanikani_level(self):
        pass

