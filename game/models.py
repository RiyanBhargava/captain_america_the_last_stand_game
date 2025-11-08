from django.db import models
from django.conf import settings
import json

class GameSession(models.Model):
    GAME_STATUS_CHOICES = [
        ('active', 'Active'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('paused', 'Paused'),
    ]
    
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=GAME_STATUS_CHOICES, default='active')
    score = models.IntegerField(default=0)
    hostage_timer = models.FloatField(default=40.0)  # Timer in seconds
    ultron_position_x = models.IntegerField(default=0)
    ultron_position_y = models.IntegerField(default=0)  # Top-left corner
    ultron_target_x = models.IntegerField(default=13)
    ultron_target_y = models.IntegerField(default=13)
    ultron_paused_until = models.DateTimeField(null=True, blank=True)  # When pause ends
    last_move_time = models.DateTimeField(null=True, blank=True)  # Track movement timing
    last_timer_update = models.DateTimeField(null=True, blank=True)  # Track timer updates
    shields_placed = models.TextField(default='[]')  # JSON array of shield positions
    game_start_time = models.DateTimeField(auto_now_add=True)
    game_end_time = models.DateTimeField(null=True, blank=True)
    time_survived = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"Game {self.id} - {self.player.username} - {self.status}"
    
    @property
    def shields_data(self):
        try:
            return json.loads(self.shields_placed)
        except:
            return []
    
    @shields_data.setter
    def shields_data(self, value):
        self.shields_placed = json.dumps(value)

class Shield(models.Model):
    SHIELD_TYPES = [
        ('blue', 'Full Block Shield'),
        ('yellow', 'Timer Reduction Shield'),
        ('red', 'Pause Shield'),
    ]
    
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='shields')
    shield_type = models.CharField(max_length=10, choices=SHIELD_TYPES)
    position_x = models.IntegerField()
    position_y = models.IntegerField()
    placed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    durability = models.IntegerField(default=1)  # Number of hits shield can take
    
    class Meta:
        unique_together = ['game_session', 'position_x', 'position_y']
    
    def __str__(self):
        return f"{self.shield_type} shield at ({self.position_x}, {self.position_y})"

class GameEvent(models.Model):
    EVENT_TYPES = [
        ('shield_placed', 'Shield Placed'),
        ('shield_destroyed', 'Shield Destroyed'),
        ('ultron_moved', 'Ultron Moved'),
        ('ultron_paused', 'Ultron Paused'),
        ('timer_reduced', 'Timer Reduced'),
        ('timer_increased', 'Timer Increased'),
        ('game_won', 'Game Won'),
        ('game_lost', 'Game Lost'),
    ]
    
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    data = models.TextField()  # JSON data for the event
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"
    
    @property
    def event_data(self):
        try:
            return json.loads(self.data)
        except:
            return {}

class Leaderboard(models.Model):
    player = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    highest_score = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    total_time_survived = models.FloatField(default=0.0)
    last_played = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-highest_score', '-games_won']
    
    def __str__(self):
        return f"{self.player.username} - {self.highest_score}"
    
    @property
    def win_rate(self):
        if self.total_games == 0:
            return 0
        return (self.games_won / self.total_games) * 100
