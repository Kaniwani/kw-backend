import django_filters
from kw_webapp.models import Vocabulary, Reading
from api.serializers import VocabularySerializer


class VocabularyFilter(django_filters.FilterSet):
    level = django_filters.MethodFilter()
    meaning_contains = django_filters.MethodFilter()

    def filter_level(self, queryset, value):
        if value:
            return queryset.filter(readings__level=value)

    def filter_meaning_contains(self, queryset, value):
        if value:
            return queryset.filter(meaning__contains=value)

    class Meta:
        model = Vocabulary
        fields = 'level', 'meaning_contains'



