import datetime

import requests
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import serializers

from api import serializer_fields
from kw_webapp.constants import KwSrsLevel, KANIWANI_SRS_LEVELS
from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level, Tag, AnswerSynonym, \
    FrequentlyAskedQuestion, Announcement
from kw_webapp.tasks import get_users_lessons, get_users_current_reviews, get_users_future_reviews, get_users_reviews


class SRSCountSerializer(serializers.BaseSerializer):
    """
    Serializer for simply showing SRS counts, e.g., how many apprentice items a user has,
    how many guru, etc.
    """

    def to_representation(self, user):
        all_reviews = get_users_reviews(user)
        return {level.value.lower(): all_reviews.filter(streak__in=KANIWANI_SRS_LEVELS[level.name]).count() for level in
                KwSrsLevel}


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.username')
    reviews_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()
    unlocked_levels = serializers.StringRelatedField(many=True, read_only=True)
    reviews_within_hour_count = serializers.SerializerMethodField()
    reviews_within_day_count = serializers.SerializerMethodField()
    srs_counts = SRSCountSerializer(source='user', many=False, read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'name', 'reviews_count', 'lessons_count', 'api_key', 'api_valid', 'join_date',
                  'last_wanikani_sync_date', 'level', 'follow_me', 'auto_advance_on_success', 'unlocked_levels',
                  'auto_expand_answer_on_success', 'auto_expand_answer_on_failure', 'on_vacation', 'vacation_date',
                  'reviews_within_day_count', 'reviews_within_hour_count', 'srs_counts',
                  'minimum_wk_srs_level_to_review', 'next_review_date')

        read_only_fields = ('id', 'name', 'api_valid', 'join_date', 'last_wanikani_sync_date', 'level',
                            'unlocked_levels', 'vacation_date', 'reviews_within_day_count',
                            'reviews_within_hour_count', 'reviews_count', 'lessons_count', 'srs_counts',
                            'next_review_date')

    def get_next_review_date(self, obj):
        user = obj.user
        if self.get_reviews_count(obj) == 0:
            reviews = get_users_future_reviews(user)
            if reviews:
                next_review_date = reviews[0].next_review_date
                return next_review_date

    def get_reviews_count(self, obj):
        return get_users_current_reviews(obj.user).count()

    def get_lessons_count(self, obj):
        return get_users_lessons(obj.user).count()

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

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile")
        profile_serializer = ProfileSerializer(data=profile_data)
        profile_serializer.save()
        instance.save()


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
    def __init__(self, *args, **kwargs):
        super(VocabularySerializer, self).__init__(*args, **kwargs)
        # If this is part of the review response, simply omit the review field, reducing DB calls.
        if 'nested_in_review' in self.context:
            self.fields.pop('review')

    readings = ReadingSerializer(many=True, read_only=True)
    review = serializers.SerializerMethodField()

    class Meta:
        model = Vocabulary
        fields = ('id', 'meaning', 'readings', 'review')

    # Grab the ID of the related review for this particular user.
    def get_review(self, obj):
        if 'request' in self.context:
            try:
                return UserSpecific.objects.get(user=self.context['request'].user, vocabulary=obj).id
            except UserSpecific.DoesNotExist:
                return None
        return None


class HyperlinkedVocabularySerializer(VocabularySerializer):
    readings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='api:reading-detail')

    class Meta(VocabularySerializer.Meta):
        pass


class SynonymSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSynonym
        fields = '__all__'

    def validate(self, data):
        review = data['review']
        if review.user != self.context['request'].user:
            raise serializers.ValidationError("Can not make a synonym for a review that is not yours!")
        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def is_valid(self, raise_exception=False):
        return super().is_valid(True)


class ReviewSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySerializer(many=False, read_only=True, context={'nested_in_review': True})
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
    fully_unlocked = serializers.BooleanField(read_only=True)
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
