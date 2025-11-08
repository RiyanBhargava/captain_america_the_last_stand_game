"""
Process active games once - designed for scheduled tasks
Run this every minute via PythonAnywhere's scheduled tasks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import GameSession, Shield, GameEvent, Leaderboard
from game.ai import UltronAI
import json
from datetime import timedelta


class Command(BaseCommand):
    help = 'Process all active games once (for scheduled tasks)'

    def handle(self, *args, **options):
        active_games = GameSession.objects.filter(status='active')
        
        self.stdout.write(f'Processing {active_games.count()} active games')
        
        for game in active_games:
            try:
                self.process_game(game)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing game {game.id}: {str(e)}'))

    def process_game(self, game):
        """Process a single game"""
        now = timezone.now()
        
        # Check if Ultron is paused
        if game.ultron_paused_until and now < game.ultron_paused_until:
            # Still paused, just save and continue
            game.save()
            return
        
        # Update hostage timer (only once per second)
        timer_should_update = False
        if game.hostage_timer > 0:
            if game.last_timer_update:
                time_since_last_timer_update = (now - game.last_timer_update).total_seconds()
                if time_since_last_timer_update >= 1.0:
                    timer_should_update = True
            else:
                timer_should_update = True
            
            if timer_should_update:
                game.hostage_timer -= 1.0
                game.last_timer_update = now
            
            if game.hostage_timer <= 0:
                self.end_game(game, won=True, reason='Hostages escaped successfully!')
                return
        
        # Check if enough time has passed for Ultron to move (1 second per tile)
        if game.last_move_time:
            time_since_last_move = (now - game.last_move_time).total_seconds()
            if time_since_last_move < 1.0:
                game.save()
                return
        else:
            game.last_move_time = now
        
        # Move Ultron using AI
        shields = game.shields.filter(is_active=True)
        shield_data = []
        for shield in shields:
            shield_data.append({
                'type': shield.shield_type,
                'position': [shield.position_x, shield.position_y]
            })
        
        ultron_ai = UltronAI()
        ultron_ai.set_position(game.ultron_position_x, game.ultron_position_y)
        ultron_ai.set_target(game.ultron_target_x, game.ultron_target_y)
        
        next_move = ultron_ai.get_next_move(shield_data)
        
        if next_move:
            old_x, old_y = game.ultron_position_x, game.ultron_position_y
            game.ultron_position_x, game.ultron_position_y = next_move
            game.last_move_time = now
            
            if (game.ultron_position_x == game.ultron_target_x and 
                game.ultron_position_y == game.ultron_target_y):
                self.end_game(game, won=False, reason='Ultron escaped')
                return
            
            shield_at_position = shields.filter(
                position_x=game.ultron_position_x,
                position_y=game.ultron_position_y
            ).first()
            
            if shield_at_position:
                self.handle_shield_interaction(game, shield_at_position)
        
        game.save()
    
    def handle_shield_interaction(self, game, shield):
        """Handle Ultron hitting a shield"""
        now = timezone.now()
        
        if shield.shield_type == 'blue':
            damage = 1
        elif shield.shield_type == 'yellow':
            old_timer = game.hostage_timer
            game.hostage_timer = max(0, game.hostage_timer - 2.0)
            damage = 1
        elif shield.shield_type == 'red':
            game.ultron_paused_until = now + timedelta(seconds=4)
            damage = 1
        else:
            damage = 0
        
        shield.durability -= damage
        if shield.durability <= 0:
            shield.is_active = False
            shield.save()
        
        GameEvent.objects.create(
            game_session=game,
            event_type='shield_hit',
            data=json.dumps({
                'shield_type': shield.shield_type,
                'position': [shield.position_x, shield.position_y],
                'ultron_position': [game.ultron_position_x, game.ultron_position_y]
            })
        )

    def end_game(self, game, won, reason=''):
        """End a game session"""
        from game.models import Leaderboard
        
        game.status = 'won' if won else 'lost'
        game.game_end_time = timezone.now()
        
        time_survived = (game.game_end_time - game.game_start_time).total_seconds()
        
        if won:
            game.score = 1000
        else:
            game.score = int(time_survived * 20)
        
        game.save()
        
        user = game.player
        user.games_played += 1
        user.total_score += game.score
        
        if won:
            user.games_won += 1
        
        if game.score > user.best_score:
            user.best_score = game.score
        
        user.save()
        
        leaderboard, created = Leaderboard.objects.get_or_create(player=user)
        leaderboard.total_games += 1
        leaderboard.total_time_survived += time_survived
        
        if won:
            leaderboard.games_won += 1
        
        if game.score > leaderboard.highest_score:
            leaderboard.highest_score = game.score
        
        leaderboard.save()
        
        GameEvent.objects.create(
            game_session=game,
            event_type='game_won' if won else 'game_lost',
            data=json.dumps({
                'reason': reason,
                'final_score': game.score,
                'time_survived': time_survived
            })
        )
        
        self.stdout.write(self.style.SUCCESS(f'Game {game.id} ended: {"Won" if won else "Lost"} - {reason}'))
