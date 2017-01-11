from rest_framework import serializers
from rest_framework.reverse import reverse

class VocabularyByLevelHyperlinkedField(serializers.HyperlinkedRelatedField):
    view_name = 'api:vocabulary-list'

    def get_url(self, obj, view_name, request, format):
        result = "{}?level={}".format(
            reverse(view_name),
            obj
        )
        return result


