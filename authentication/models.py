from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    @property
    def win_rate(self):
        if self.games_played == 0:
            return 0
        return (self.games_won / self.games_played) * 100
