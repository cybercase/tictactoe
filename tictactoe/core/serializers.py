from rest_framework import serializers
from core.models import Game, User, Stats


class JSONField(serializers.WritableField):

    def to_native(self, obj):
        return obj


class GameSerializer(serializers.HyperlinkedModelSerializer):

    grid = JSONField(read_only=True)

    class Meta:
        model = Game
        read_only_fields = ('user1', 'user2', 'status')


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'url', 'email')


class StatsSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Stats

