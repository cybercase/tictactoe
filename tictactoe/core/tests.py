from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import Game

import json


User = get_user_model()

# Create your tests here.
class GameTest(APITestCase):


    def setUp(self):
        self.user_one = User(username='user1', password='user1')
        self.user_one.save()
        self.user_two = User(username='user2', password='user2')
        self.user_two.save()


    def set_authentication(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)


    def test_create(self):
        self.set_authentication(self.user_one)
        response = self.client.post(reverse('game-list'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.game_obj = json.loads(response.content)
        response = self.client.get(self.game_obj['url'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.game_obj['status'], Game.STATUS_WAITING)


    def test_join(self):
        self.test_create()

        self.set_authentication(self.user_two)
        game_list_response = self.client.get(reverse('game-list'))
        self.assertEqual(game_list_response.status_code, status.HTTP_200_OK)

        game_list = json.loads(game_list_response.content)
        self.assertEqual(len(game_list), 1)

        self.game_obj = game_list.pop()

        response = self.client.patch(self.game_obj['url'],
            {'user2': reverse('user-detail', args=[self.user_two.pk])})

        # FORCE PLAYER_ONE TURN
        g = Game.objects.first()
        g.status = Game.STATUS_TURN_ONE
        g.save()

        response = self.client.get(self.game_obj['url'])
        self.game_obj = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_double_join(self):
        self.test_join()

        response = self.client.patch(self.game_obj['url'],
            {'user2': reverse('user-detail', args=[self.user_two.pk])})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


    def test_move_player_one(self):
        self.test_join()

        self.set_authentication(self.user_one)
        response = self.client.post(self.game_obj['url'] + 'set/', {'square': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        response = self.client.get(self.game_obj['url'])
        self.game_obj = json.loads(response.content)

        self.assertEqual(self.game_obj['grid'][1], 1)
        self.assertEqual(self.game_obj['status'], Game.STATUS_TURN_TWO)


    def test_wrong_turn(self):
        self.test_move_player_one()

        self.set_authentication(self.user_one)
        response = self.client.post(self.game_obj['url'] + 'set/', {'square': 2}, format='json')
        self.assertEqual(response.status_code, 400)


    def test_move_player_two(self):
        self.test_move_player_one()

        self.set_authentication(self.user_two)
        response = self.client.post(self.game_obj['url'] + 'set/', {'square': 0}, format='json')

        response = self.client.get(self.game_obj['url'])
        self.game_obj = json.loads(response.content)

        self.assertEqual(self.game_obj['grid'][0], 2)
        self.assertEqual(self.game_obj['status'], Game.STATUS_TURN_ONE)


    def test_bad_square(self):
        self.test_move_player_one()

        self.set_authentication(self.user_two)
        response = self.client.post(self.game_obj['url'] + 'set/', {'square': 1}, format='json')
        self.assertEqual(response.status_code, 400)


    def test_win_one(self):
        game = Game(user1=self.user_one, user2=self.user_two, status=Game.STATUS_TURN_ONE,
            grid=[1, 0, 1, 1, 2, 1, 2, 1, 2])
        game.save()

        self.set_authentication(self.user_one)
        response = self.client.post(reverse('game-detail', args=[game.pk]) + 'set/',
            {'square': 1}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        game_obj = json.loads(response.content)
        self.assertEqual(game_obj['status'], Game.STATUS_WIN_ONE)


    def test_draw(self):
        game = Game(user1=self.user_one, user2=self.user_two, status=Game.STATUS_TURN_TWO,
            grid=[1, 0, 1, 1, 2, 1, 2, 1, 2])
        game.save()

        self.set_authentication(self.user_two)
        response = self.client.post(reverse('game-detail', args=[game.pk]) + 'set/',
            {'square': 1}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        game_obj = json.loads(response.content)
        self.assertEqual(game_obj['status'], Game.STATUS_DRAW)


    def test_win_two(self):
        game = Game(user1=self.user_one, user2=self.user_two, status=Game.STATUS_TURN_TWO,
            grid=[2, 0, 2, 2, 1, 2, 1, 2, 1])
        game.save()

        self.set_authentication(self.user_two)
        response = self.client.post(reverse('game-detail', args=[game.pk]) + 'set/',
            {'square': 1}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        game_obj = json.loads(response.content)
        self.assertEqual(game_obj['status'], Game.STATUS_WIN_TWO)


    def test_stats_updated(self):
        self.assertEqual(self.user_two.stats.won, 0)
        self.assertEqual(self.user_one.stats.lost, 0)

        self.test_win_two()

        user2 = User.objects.get(id=self.user_two.id)
        self.assertEqual(user2.stats.won, 1)

        user1 = User.objects.get(id=self.user_one.id)
        self.assertEqual(user1.stats.lost, 1)


    def test_two_over_one(self):
        game = Game(user1=self.user_one, user2=self.user_two, status=Game.STATUS_TURN_TWO,
            grid=[2, 0, 2, 2, 1, 2, 1, 2, 1])
        game.save()

        self.set_authentication(self.user_two)
        response = self.client.post(reverse('game-detail', args=[game.pk]) + 'set/',
            {'square': 5}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

