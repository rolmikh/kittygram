from django.conf import settings
from django.db import models
from django.utils import timezone

from cats.models import Cat


class Tournament(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_FINISHED = 'finished'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FINISHED, 'Finished'),
    ]

    name = models.CharField(max_length=100)

    start_date = models.DateTimeField(default=timezone.now)

    end_date = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )

    winner = models.ForeignKey(
        Cat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_tournaments'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=1)

        super().save(*args, **kwargs)

    def update_results(self):

        finished_duels = self.duels.filter(
            status=Duel.STATUS_FINISHED
        )

        if not finished_duels.exists():
            return

        wins = {}

        for duel in finished_duels:

            if duel.winner:
                wins[duel.winner_id] = (
                    wins.get(duel.winner_id, 0) + 1
                )

        if not wins:
            return

        winner_id = max(wins, key=wins.get)

        self.winner_id = winner_id

        unfinished_duels_exists = self.duels.exclude(
            status=Duel.STATUS_FINISHED
        ).exists()

        if unfinished_duels_exists:
            self.status = self.STATUS_ACTIVE
        else:
            self.status = self.STATUS_FINISHED

        self.save(update_fields=['winner', 'status'])

    def __str__(self):
        return self.name


class Duel(models.Model):

    STATUS_PLANNED = 'planned'
    STATUS_ACTIVE = 'active'
    STATUS_FINISHED = 'finished'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'Planned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FINISHED, 'Finished'),
    ]

    first_cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name='duels_as_first'
    )

    second_cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name='duels_as_second'
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='duels',
        null=True,
        blank=True
    )

    start_time = models.DateTimeField(
    null=True,
    blank=True
    )

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNED
    )

    winner = models.ForeignKey(
        Cat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_duels'
    )

    is_draw = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if self.start_time and not self.end_time:
            self.end_time = (
                self.start_time + timezone.timedelta(hours=1)
            )

        super().save(*args, **kwargs)

    def refresh_status(self):

        if not self.start_time or not self.end_time:
            return

        now = timezone.now()

        if now < self.start_time:

            new_status = self.STATUS_PLANNED

        elif self.start_time <= now <= self.end_time:

            new_status = self.STATUS_ACTIVE

        else:

            new_status = self.STATUS_FINISHED

            if self.status != self.STATUS_FINISHED:
                self.finalize()

        if self.status != new_status:

            self.status = new_status

            self.save(update_fields=['status'])

    def finalize(self):

        if not self.end_time or timezone.now() < self.end_time:
            return

        if self.winner or self.is_draw:
            return

        first_votes = self.votes.filter(
            cat=self.first_cat
        ).count()

        second_votes = self.votes.filter(
            cat=self.second_cat
        ).count()

        first_stats, _ = CatStats.objects.get_or_create(
            cat=self.first_cat
        )

        second_stats, _ = CatStats.objects.get_or_create(
            cat=self.second_cat
        )

        if first_votes > second_votes:

            self.winner = self.first_cat

            first_stats.wins += 1
            second_stats.losses += 1

        elif second_votes > first_votes:

            self.winner = self.second_cat

            second_stats.wins += 1
            first_stats.losses += 1

        else:

            self.is_draw = True

            first_stats.draws += 1
            second_stats.draws += 1

        first_stats.total_duels += 1
        second_stats.total_duels += 1

        first_stats.recalc()
        second_stats.recalc()

        self.save(update_fields=['winner', 'is_draw'])

        if self.tournament:
            self.tournament.update_results()

    def __str__(self):
        return f'{self.first_cat} vs {self.second_cat}'


class Vote(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    duel = models.ForeignKey(
        Duel,
        on_delete=models.CASCADE,
        related_name='votes'
    )

    cat = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'duel'],
                name='unique_vote_per_user'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.cat}'


class CatStats(models.Model):

    cat = models.OneToOneField(
        Cat,
        on_delete=models.CASCADE,
        related_name='stats'
    )

    wins = models.PositiveIntegerField(default=0)

    losses = models.PositiveIntegerField(default=0)

    draws = models.PositiveIntegerField(default=0)

    total_duels = models.PositiveIntegerField(default=0)

    rating = models.IntegerField(default=0)

    def recalc(self):

        self.rating = (self.wins * 3) + self.draws

        self.save(update_fields=['rating'])

    def __str__(self):
        return f'Stats of {self.cat}'
