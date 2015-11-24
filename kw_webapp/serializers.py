from django.contrib.auth.models import User, Group
from rest_framework import serializers

from kw_webapp.models import Vocabulary, Synonym, UserSpecific, Reading, Profile


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups', 'profile')


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading


class VocabularySerializer(serializers.ModelSerializer):
    readings = ReadingSerializer(source='reading_set', many=True)

    class Meta:
        model = Vocabulary


class SynonymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synonym


class ReviewSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySerializer()
    synonyms = SynonymSerializer(source='synonym_set', many=True)

    class Meta:
        model = UserSpecific

