import re

from django.db.models import Q
from django_filters import rest_framework as filters

from kw_webapp.models import Vocabulary, UserSpecific

import KW.settings


def whole_word_regex(value):
    # Gross hack to handle this until I fix it:
    # https://stackoverflow.com/questions/14997536/whole-word-match-only-in-django-query
    if KW.settings.DB_ENGINE == "sqlite3":
        return r"\b" + re.escape(value) + r"\b"
    else:
        return r"\y" + re.escape(value) + r"\y"


def filter_level_for_vocab(queryset, name, value):
    if value:
        return queryset.filter(readings__level=value).distinct()


def filter_level_for_review(queryset, name, value):
    if value:
        return queryset.filter(vocabulary__readings__level=value).distinct()


def filter_meaning_contains(queryset, name, value):
    if value:
        return queryset.filter(meaning__iregex=whole_word_regex(value))


# This filter awkwardly shoehorned in with the FilterSet filters,
# but used for direct filtering from the ViewSet
def filter_user_meaning_contains(queryset, meaning_contains, user_id):
    if meaning_contains and user_id:
        return queryset.filter(
            Q(meaning__iregex=whole_word_regex(meaning_contains))
            | (Q(userspecific__meaning_synonyms__text__iregex=whole_word_regex(meaning_contains)) &
               Q(userspecific__user_id=user_id))
        ).distinct()


def filter_meaning_contains_for_review(queryset, name, value):
    if value:
        return queryset.filter(
            vocabulary__meaning__iregex=whole_word_regex(value)
        )


def filter_vocabulary_parts_of_speech(queryset, name, value):
    if value:
        return queryset.filter(readings__parts_of_speech__part=value)


def filter_srs_level(queryset, name, value):
    if value:
        return queryset.filter()


def filter_reading_contains(queryset, name, value):
    """
    Filter function return any vocab wherein the reading kana or kanji contain the requested characters
    """
    if value:
        return queryset.filter(
            Q(readings__kana__contains=value)
            | Q(readings__character__contains=value)
        ).distinct()


def filter_reading_contains_for_review(queryset, name, value):
    """
    Filter function return any reviews wherein the vocabulary reading kana or kanji contain the requested characters
    """
    if value:
        return queryset.filter(
            Q(vocabulary__readings__kana__contains=value)
            | Q(vocabulary__readings__character__contains=value)
        ).distinct()


class VocabularyFilter(filters.FilterSet):
    level = filters.NumberFilter(method=filter_level_for_vocab)
    reading_contains = filters.CharFilter(method=filter_reading_contains)
    part_of_speech = filters.CharFilter(
        method=filter_vocabulary_parts_of_speech
    )

    class Meta:
        model = Vocabulary
        fields = "__all__"


def filter_tag_multi(queryset, name, value):
    return queryset.filter(
        vocabulary__readings__parts_of_speech__part__iexact=value
    )


class ReviewFilter(filters.FilterSet):
    level = filters.NumberFilter(method=filter_level_for_review)
    meaning_contains = filters.CharFilter(
        method=filter_meaning_contains_for_review
    )
    reading_contains = filters.CharFilter(
        method=filter_reading_contains_for_review
    )
    srs_level = filters.NumberFilter(field_name="streak", lookup_expr="exact")
    srs_level_lt = filters.NumberFilter(field_name="streak", lookup_expr="lt")
    srs_level_gt = filters.NumberFilter(field_name="streak", lookup_expr="gt")
    part_of_speech = filters.CharFilter(method=filter_tag_multi)

    class Meta:
        model = UserSpecific
        fields = (
            "srs_level",
            "srs_level_gt",
            "srs_level_lt",
            "part_of_speech",
            "wanikani_burned",
        )
