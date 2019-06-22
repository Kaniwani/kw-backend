import abc



class WanikaniUserSyncer(abc.ABC):

    @abc.abstractmethod
    def sync_user_profile_with_wk(self):
        """
        Copy over all relevant information from the /user/ endpoint of wanikani.
        :return:
        """
        pass

    @abc.abstractmethod
    def sync_with_wk(self, full_sync=False):
        pass

    @abc.abstractmethod
    def sync_recent_unlocked_vocab(self):
        pass

    @abc.abstractmethod
    def sync_unlocked_vocab(self):
        pass

    @abc.abstractmethod
    def sync_study_materials(self):
        pass

    @abc.abstractmethod
    def sync_top_level_vocabulary(self):
        pass

    @abc.abstractmethod
    def unlock_vocab(self, levels):
        pass

    @abc.abstractmethod
    def get_wanikani_level(self):
        pass
