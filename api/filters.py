from django_filters import rest_framework as filters
from kw_webapp.models import Vocabulary


class VocabularyFilter(filters.FilterSet):
    def filter_meaning_contains(self, queryset, value):
        if value:
            return queryset.filter(meaning__contains=value)

    def filter_level(self, queryset, value):
        if value:
            return queryset.filter(readings__level=value)

    def filter_tag(self, queryset, value):
        if value:
            return queryset.filter(readings__tag__name=value)

    level = filters.NumberFilter(method=filter_level)
    meaning_contains = filters.CharFilter(method=filter_meaning_contains)

    class Meta:
        model = Vocabulary
        fields = 'level', 'meaning_contains'



