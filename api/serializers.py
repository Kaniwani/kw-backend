from django.contrib.auth.models import User
from rest_framework import serializers

from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level, Tag, AnswerSynonym


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ('level',)


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.username')
    reviews_count = serializers.ReadOnlyField(source='user.reviews.count')
    unlocked_levels = serializers.StringRelatedField(many=True)

    class Meta:
        model = Profile
        fields = ('name', 'reviews_count', 'api_key', 'api_valid', 'join_date', 'last_wanikani_sync_date',
                  'level', 'unlocked_levels', 'follow_me', 'auto_advance_on_success',
                  'auto_expand_answer_on_success', 'auto_expand_answer_on_failure',
                  'only_review_burned', 'on_vacation', 'vacation_date')
        read_only_fields = ('api_valid', 'join_date', 'last_wanikani_sync_date', 'level',
                            'unlocked_levels', 'vacation_date')


class UserSerializer(serializers.ModelSerializer):
    reviews = serializers.PrimaryKeyRelatedField(many=True, queryset=UserSpecific.objects.all())
    profile = serializers.PrimaryKeyRelatedField(many=False, queryset=Profile.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'profile', 'reviews')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name',)


class ReadingSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Reading
        fields = ('character', 'kana', 'level', 'tags', 'sentence_en', 'sentence_ja',
                  'jlpt', 'common')


class VocabularySerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(many=True, read_only=True)

    class Meta:
        model = Vocabulary
        fields = ('meaning', 'readings')


class HyperlinkedVocabularySerializer(VocabularySerializer):
    readings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='vocabulary-detail')

    class Meta(VocabularySerializer.Meta):
        pass

class SynonymSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSynonym
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySerializer(many=False, read_only=True)
    answer_synonyms = SynonymSerializer(many=True, read_only=True)

    class Meta:
        model = UserSpecific
        fields = '__all__'

        read_only_fields = ('id', 'vocabulary', 'correct', 'incorrect', 'streak'
                            'user', 'needs_review', 'last_studied', 'unlock_date', 'wanikani_srs',
                            'wanikani_srs_numeric', 'wanikani_burned', 'burned')


class StubbedReviewSerializer(ReviewSerializer):
    class Meta(ReviewSerializer.Meta):
        fields = ('id', 'vocabulary', 'correct', 'incorrect', 'streak', 'notes', 'answer_synonyms')
