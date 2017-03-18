import datetime

import requests
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import serializers

from api import serializer_fields
from kw_webapp.constants import KANIWANI_SRS_LEVELS, KW_SRS_LEVEL_NAMES
from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level, Tag, AnswerSynonym, \
    FrequentlyAskedQuestion, Announcement
from kw_webapp.tasks import get_users_current_reviews, get_users_future_reviews, get_users_reviews


class SRSCountSerializer(serializers.BaseSerializer):
    def to_representation(self, user):
        all_reviews = get_users_reviews(user)
        return {srs_level: all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS[srs_level]).count() for srs_level in
                KW_SRS_LEVEL_NAMES}


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.username')
    reviews_count = serializers.SerializerMethodField()
    unlocked_levels = serializers.StringRelatedField(many=True)
    reviews_within_hour_count = serializers.SerializerMethodField()
    reviews_within_day_count = serializers.SerializerMethodField()
    srs_counts = SRSCountSerializer(source='user', many=False, read_only=True)

    class Meta:
        model = Profile
        fields = ('name', 'reviews_count', 'api_key', 'api_valid', 'join_date', 'last_wanikani_sync_date',
                  'level', 'unlocked_levels', 'follow_me', 'auto_advance_on_success',
                  'auto_expand_answer_on_success', 'auto_expand_answer_on_failure',
                  'only_review_burned', 'on_vacation', 'vacation_date', 'reviews_within_day_count',
                  'reviews_within_hour_count', "srs_counts")

        read_only_fields = ('api_valid', 'join_date', 'last_wanikani_sync_date', 'level',
                            'unlocked_levels', 'vacation_date', 'reviews_within_day_count',
                            'reviews_within_hour_count', 'reviews_count')

    def get_reviews_count(self, obj):
        return get_users_current_reviews(obj.user).count()

    def get_reviews_within_hour_count(self, obj):
        return get_users_future_reviews(obj.user,
                                        time_limit=datetime.timedelta(hours=1)).count()

    def get_reviews_within_day_count(self, obj):
        return get_users_future_reviews(obj.user, time_limit=datetime.timedelta(hours=24)).count()


class RegistrationSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, max_length=32)
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('api_key', 'password', 'username', 'email')

    def validate_password(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("Password is not long enough!")
        return value

    def validate_api_key(self, value):
        r = requests.get("https://www.wanikani.com/api/user/{}/user-information".format(value))
        if r.status_code == 200:
            json_data = r.json()
            if "error" in json_data.keys():
                raise serializers.ValidationError("API Key not associated with a WaniKani User!")
        else:
            raise serializers.ValidationError("Invalid!")
        return value

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            return value
        else:
            raise serializers.ValidationError("Email is already in use!")

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            return value
        else:
            raise serializers.ValidationError("Username is already in use!")

    def create(self, validated_data):
        preexisting_users = User.objects.filter(Q(username=validated_data.get('username')) |
                                                Q(email=validated_data.get('email')))

        if preexisting_users.count() > 0:
            raise serializers.ValidationError("Username or email already in use!")

        api_key = validated_data.pop('api_key', None)

        user = User.objects.create(**validated_data)
        user.set_password(validated_data.get('password'))
        user.save()
        Profile.objects.create(user=user, api_key=api_key, level=1)
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False, read_only=True)
    api_key = serializers.CharField(write_only=True, max_length=32)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('api_key', 'password', 'username', 'email', 'profile')
        read_only_fields = ('id', 'last_login', 'is_active', 'date_joined', 'is_staff', 'is_superuser', 'profile')

    def validate_password(self, value):
        if len(value) < 4:
            raise serializers.ValidationError("Password is not long enough!")
        return value

    def validate_api_key(self, value):
        r = requests.get("https://www.wanikani.com/api/user/{}/user-information".format(value))
        if r.status_code == 200:
            json_data = r.json()
            if "error" in json_data.keys():
                raise serializers.ValidationError("API Key not associated with a WaniKani User!")
        else:
            raise serializers.ValidationError("Invalid!")
        return value

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            return value
        else:
            raise serializers.ValidationError("Email is already in use!")

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            return value
        else:
            raise serializers.ValidationError("Username is already in use!")

    def create(self, validated_data):
        preexisting_users = User.objects.filter(Q(username=validated_data.get('username')) |
                                                Q(email=validated_data.get('email')))

        if preexisting_users.count() > 0:
            raise serializers.ValidationError("Username or email already in use!")

        api_key = validated_data.pop('api_key', None)

        user = User.objects.create(**validated_data)
        user.set_password(validated_data.get('password'))
        Profile.objects.create(user=user, api_key=api_key, level=1)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name',)


class ReadingSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Reading
        fields = ('id', 'character', 'kana', 'level', 'tags', 'sentence_en', 'sentence_ja',
                  'jlpt', 'common')


class VocabularySerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(many=True, read_only=True)

    class Meta:
        model = Vocabulary
        fields = ('id', 'meaning', 'readings')


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
    vocabulary_url = serializer_fields.VocabularyByLevelHyperlinkedField(read_only=True)
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


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=100)
