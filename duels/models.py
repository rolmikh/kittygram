from django.conf import settings
from django.db import models
from django.utils import timezone
from cats.models import Cat


class Duel(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('finished', 'Finished'),
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

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='planned'
    )

    def save(self, *args, **kwargs):
        if not self.start_time:
            self.start_time = timezone.now()
        if not self.end_time:
            self.end_time = self.start_time + timezone.timedelta(hours=1)

        super().save(*args, **kwargs)

    def update_status(self):
        now = timezone.now()

        if now < self.start_time:
            self.status = 'planned'
        elif self.start_time <= now <= self.end_time:
            self.status = 'active'
        else:
            self.status = 'finished'

        self.save()


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    duel = models.ForeignKey(Duel, on_delete=models.CASCADE, related_name='votes')

    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'duel'],
                name='unique_vote_per_user'
            )
        ]
