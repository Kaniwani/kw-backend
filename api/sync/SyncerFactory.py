from api.sync.WanikaniUserSyncerV2 import WanikaniUserSyncerV2


class Syncer:
    @staticmethod
    def factory(profile):
        return WanikaniUserSyncerV2(profile)
