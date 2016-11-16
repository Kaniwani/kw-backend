from django.contrib.auth.models import User
from rest_framework import serializers

from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level


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

class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = ('character', 'kana', 'level')



class VocabularySerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(many=True, read_only=True)

    class Meta:
        model = Vocabulary
        fields = ('meaning', 'readings')

class ReviewSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySerializer(many=False, read_only=True)

    class Meta:
        model = UserSpecific
        fields = ('id', 'vocabulary', 'correct', 'incorrect', 'streak', 'last_studied', 'needs_review', 'unlock_date',
                  'next_review_date', 'burned', 'hidden', 'wanikani_srs', 'wanikani_srs_numeric', 'wanikani_burned')



