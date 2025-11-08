from django.contrib import admin
from .models import GameSession, Shield, GameEvent, Leaderboard

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'status', 'score', 'hostage_timer', 'time_survived', 'game_start_time')
    list_filter = ('status', 'game_start_time')
    search_fields = ('player__username',)
    readonly_fields = ('game_start_time', 'game_end_time')
    ordering = ('-game_start_time',)

@admin.register(Shield)
class ShieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'game_session', 'shield_type', 'position_x', 'position_y', 'placed_at', 'is_active')
    list_filter = ('shield_type', 'is_active', 'placed_at')
    search_fields = ('game_session__player__username',)

@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'game_session', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('game_session__player__username',)
    readonly_fields = ('timestamp',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('player', 'highest_score', 'total_games', 'games_won', 'win_rate', 'last_played')
    search_fields = ('player__username',)
    readonly_fields = ('last_played',)
    ordering = ('-highest_score',)
