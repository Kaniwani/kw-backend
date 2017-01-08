from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level, Tag, AnswerSynonym, \
    FrequentlyAskedQuestion, Announcement


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
    readings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='api:reading-detail')

    class Meta(VocabularySerializer.Meta):
        pass


class SynonymSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSynonym
        fields = '__all__'

    def validate_review(self, value):
        """
        Check that the user creating the synonym owns the related review.
        """
        review = value
        if review.user != self.context['request'].user:
            raise serializers.ValidationError("Can not make a synonym for a review that is not yours!")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySerializer(many=False, read_only=True)
    answer_synonyms = SynonymSerializer(many=True, read_only=True)

    class Meta:
        model = UserSpecific
        fields = '__all__'

        read_only_fields = ('id', 'vocabulary', 'correct', 'incorrect', 'streak',
                            'user', 'needs_review', 'last_studied',
                            'unlock_date', 'wanikani_srs',
                            'wanikani_srs_numeric', 'wanikani_burned', 'burned', 'critical')


class StubbedReviewSerializer(ReviewSerializer):
    class Meta(ReviewSerializer.Meta):
        fields = ('id', 'vocabulary', 'correct', 'incorrect', 'streak', 'notes', 'answer_synonyms')


class LevelSerializer(serializers.Serializer):
    level = serializers.IntegerField(read_only=True)
    unlocked = serializers.BooleanField(read_only=True)
    vocabulary_count = serializers.IntegerField(read_only=True)
    lock_url = serializers.CharField(read_only=True)
    unlock_url = serializers.CharField(read_only=True)


class FrequentlyAskedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = '__all__'


class AnnouncementSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    class Meta:
        model = Announcement
        fields = ('title', 'body', 'pub_date', 'creator')
