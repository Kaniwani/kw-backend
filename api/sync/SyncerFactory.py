from api.sync.WanikaniUserSyncerV1 import WanikaniUserSyncerV1
from api.sync.WanikaniUserSyncerV2 import WanikaniUserSyncerV2


class Syncer:
    @staticmethod
    def factory(profile):
        if profile.api_key_v2 is not None:
            return WanikaniUserSyncerV2(profile)
        else:
            return WanikaniUserSyncerV1(profile)
