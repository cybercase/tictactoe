from rest_framework import viewsets, response, permissions, status
from rest_framework.decorators import action
from core.models import Game, User, Stats
from core.serializers import GameSerializer, UserSerializer, StatsSerializer
import random


class IsPlayer(permissions.BasePermission):

    def has_object_permission(self, request, view, game):
        return request.user.id in [game.user1.id, game.user2.id]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MeViewSet(viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet):
    model = User
    serializer_class = UserSerializer

    def get_queryset(self):
        return super(MeViewSet, self).get_queryset() \
            .filter(id=self.request.user.id)


class StatsViewSet(viewsets.mixins.ListModelMixin,
    viewsets.mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    model = Stats
    serializer_class = StatsSerializer


class GameListViewSet(viewsets.mixins.ListModelMixin,
    viewsets.mixins.CreateModelMixin,
    viewsets.GenericViewSet):
    model = Game
    serializer_class = GameSerializer

    def get_queryset(self):
        return super(GameListViewSet, self).get_queryset().filter(user2__isnull=True,
            user1__isnull=False).exclude(user1=self.request.user)

    def pre_save(self, obj):
        obj.user1 = self.request.user
        obj.user1.stats.created += 1


class GameDetailViewSet(viewsets.mixins.RetrieveModelMixin,
    viewsets.mixins.UpdateModelMixin,
    viewsets.GenericViewSet):
    queryset = Game.objects.filter()
    serializer_class = GameSerializer

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.user2 is not None:
            return response.Response({'error': "Someone already joined"},
                status=status.HTTP_400_BAD_REQUEST)

        if obj.user1.id == self.request.user.id:
            return response.Response({'error': "Already joined as player ONE"},
                status=status.HTTP_400_BAD_REQUEST)

        return super(GameDetailViewSet, self).partial_update(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.user2 = self.request.user
        obj.user2.stats.joined += 1
        obj.user2.stats.save()
        obj.status = random.choice([Game.STATUS_TURN_ONE, # Chooses first turn randomly
            Game.STATUS_TURN_TWO])


    @action(permission_classes=[IsPlayer])
    def set(self, request, pk):
        try:
            pos = int(request.DATA['square'])
            if pos >= 9:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            return response.Response({'error': "Wrong move. Allowed [1...9]"},
                status=status.HTTP_400_BAD_REQUEST)

        game = self.get_object()

        if game.status not in [Game.STATUS_TURN_ONE, Game.STATUS_TURN_TWO]:
            return response.Response({'error': "Wrong game status"},
                status=status.HTTP_400_BAD_REQUEST)

        is_user1 = request.user.id == game.user1.id
        is_user2 = request.user.id == game.user2.id

        wrong_turn = is_user1 and game.status != Game.STATUS_TURN_ONE
        wrong_turn |= is_user2 and game.status != Game.STATUS_TURN_TWO

        if wrong_turn:
            return response.Response({'error': "Not Your Turn!"},
                status=status.HTTP_400_BAD_REQUEST)

        val = is_user1 and Game.GRID_PLAYER_ONE or Game.GRID_PLAYER_TWO

        if game.grid[pos] == Game.GRID_EMPTY:
            game.grid[pos] = val
        else:
            return response.Response("Bad Move Move!", status=status.HTTP_400_BAD_REQUEST)

        if not game.check_ended():
            game.status = is_user1 and Game.STATUS_TURN_TWO or Game.STATUS_TURN_ONE

        game.save()

        return response.Response(GameSerializer(game).data)
