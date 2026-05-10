from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from cats.models import Cat
from duels.models import Tournament, Duel


User = get_user_model()


class TournamentTests(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='capybara',
            password='yepicapi'
        )

        self.client.force_authenticate(user=self.user)

        self.cat1 = Cat.objects.create(
            name='Барсик',
            color='Black',
            birth_year=2020,
            owner=self.user
        )

        self.cat2 = Cat.objects.create(
            name='Пушок',
            color='White',
            birth_year=2021,
            owner=self.user
        )

    def test_create_tournament(self):

        data = {
            'name': 'Summer Cup',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=1)
        }

        response = self.client.post(
            '/tournaments/',
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_invalid_tournament_dates(self):

        data = {
            'name': 'Invalid Cup',
            'start_date': timezone.now(),
            'end_date': timezone.now() - timedelta(days=1)
        }

        response = self.client.post(
            '/tournaments/',
            data,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_tournament_results(self):

        tournament = Tournament.objects.create(
            name='Test Cup',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1)
        )

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            tournament=tournament,
            status=Duel.STATUS_FINISHED,
            winner=self.cat1
        )

        response = self.client.get(
            f'/tournaments/{tournament.id}/results/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_tournament_leaderboard(self):

        tournament = Tournament.objects.create(
            name='Test Cup',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1)
        )

        response = self.client.get(
            f'/tournaments/{tournament.id}/leaderboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
