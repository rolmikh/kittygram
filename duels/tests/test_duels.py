from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from cats.models import Cat
from duels.models import Duel


User = get_user_model()


class DuelTests(APITestCase):

    def setUp(self):

        self.user1 = User.objects.create_user(
            username='capybara',
            password='yeppicapi'
        )

        self.user2 = User.objects.create_user(
            username='capybara2',
            password='ipacippey'
        )

        self.cat1 = Cat.objects.create(
            name='Барсик',
            color='Black',
            birth_year=2020,
            owner=self.user1
        )

        self.cat2 = Cat.objects.create(
            name='Пушон',
            color='White',
            birth_year=2021,
            owner=self.user2
        )

        self.client.force_authenticate(user=self.user1)

    def test_create_duel(self):

        data = {
            'first_cat': self.cat1.id,
            'second_cat': self.cat2.id
        }

        response = self.client.post('/duels/', data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(Duel.objects.count(), 1)

    def test_create_duel_same_cat(self):

        data = {
            'first_cat': self.cat1.id,
            'second_cat': self.cat1.id
        }

        response = self.client.post('/duels/', data)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_get_duels_list(self):

        Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2
        )

        response = self.client.get('/duels/')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_start_duel(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2
        )

        response = self.client.post(
            f'/duels/{duel.id}/start/'
        )

        duel.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            duel.status,
            Duel.STATUS_ACTIVE
        )

    def test_start_already_started_duel(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status=Duel.STATUS_ACTIVE
        )

        response = self.client.post(
            f'/duels/{duel.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_vote_for_cat(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status=Duel.STATUS_ACTIVE
        )

        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

    def test_double_vote_not_allowed(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status=Duel.STATUS_ACTIVE
        )

        self.client.force_authenticate(user=self.user2)

        self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        response = self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_vote_for_own_cat_not_allowed(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status=Duel.STATUS_ACTIVE
        )

        response = self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_vote_in_finished_duel_not_allowed(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            status=Duel.STATUS_FINISHED
        )

        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_results_endpoint(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2
        )

        response = self.client.get(
            f'/duels/{duel.id}/results/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn('status', response.data)

    def test_leaderboard_endpoint(self):

        response = self.client.get(
            '/duels/leaderboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_my_vote_stats(self):

        duel = Duel.objects.create(
            first_cat=self.cat1,
            second_cat=self.cat2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status=Duel.STATUS_ACTIVE
        )

        self.client.force_authenticate(user=self.user2)

        self.client.post(
            f'/duels/{duel.id}/vote/',
            {'cat': self.cat1.id}
        )

        response = self.client.get(
            '/duels/my_vote_stats/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn('total_votes', response.data)
