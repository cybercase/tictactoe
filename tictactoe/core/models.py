from django.db import models
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from json_field import JSONField


@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
        Stats.objects.create(user=instance)


class Stats(models.Model):
    user = models.OneToOneField(get_user_model(), related_name='stats')

    created = models.IntegerField(default=0)
    joined = models.IntegerField(default=0)

    won = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    draw = models.IntegerField(default=0)


User = get_user_model()


class Game(models.Model):

    GRID_EMPTY = 0
    GRID_PLAYER_ONE = 1
    GRID_PLAYER_TWO = 2

    STATUS_TURN_ONE = 'PLAYER_TURN_ONE'
    STATUS_TURN_TWO = 'PLAYER_TURN_TWO'
    STATUS_WIN_ONE = 'PLAYER_WIN_ONE'
    STATUS_WIN_TWO = 'PLAYER_WIN_TWO'
    STATUS_DRAW = 'DRAW'
    STATUS_WAITING = 'WAITING'

    GAME_STATUS = (
        (STATUS_TURN_ONE, STATUS_TURN_ONE),
        (STATUS_TURN_TWO, STATUS_TURN_TWO),
        (STATUS_WIN_ONE, STATUS_WIN_ONE),
        (STATUS_WIN_TWO, STATUS_WIN_ONE),
        (STATUS_WAITING, STATUS_WAITING)
    )

    user1 = models.ForeignKey(get_user_model(), related_name='game_creators')
    user2 = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='game_joiners')

    grid = JSONField(default=[GRID_EMPTY]*9, blank=True)

    status = models.CharField(choices=GAME_STATUS, max_length=32,
        default=STATUS_WAITING, blank=True)

    def check_ended(self):
        # if game ended, set finale status and return true
        # else return false
        winning_conditions = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

        winner = None
        loser = None
        for c1, c2, c3 in winning_conditions:
            if self.grid[c1] == self.grid[c2] == self.grid[c3] and self.grid[c1] != 0:

                winner = self.grid[c1] == self.GRID_PLAYER_ONE and self.user1 \
                    or self.user2
                loser = self.user1 == winner and self.user2 or self.user1

                self.status = winner == self.user1 and self.STATUS_WIN_ONE \
                    or self.STATUS_WIN_TWO

                break

        ended = False

        if winner and loser:
            winner.stats.won += 1
            loser.stats.lost += 1
            ended = True

        elif Game.GRID_EMPTY not in self.grid:  # Grid filled
            self.status = self.STATUS_DRAW
            self.user1.stats.draw += 1
            self.user2.stats.draw += 1
            ended = True

        else:
            ended = False

        if ended:
            self.user1.stats.save()
            self.user2.stats.save()

        return ended

    def __unicode__(self):
        return u'{0} vs {1} - {2}'.format(self.user1, self.user2, self.status)