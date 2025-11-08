from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import GameSession, Shield, GameEvent
from game.game_logic import UltronAI
import time
import json
import threading
from datetime import timedelta

class Command(BaseCommand):
    help = 'Run the game loop for active games'
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=float,
            default=1.0,
            help='Game loop interval in seconds (default: 1.0)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(
            self.style.SUCCESS(f'Starting game loop with {interval}s interval...')
        )
        
        try:
            while self.running:
                self.process_active_games()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Game loop stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Game loop error: {str(e)}')
            )
    
    def process_active_games(self):
        """Process all active games"""
        active_games = GameSession.objects.filter(status='active')
        
        print(f"Processing {active_games.count()} active games")
        
        for game in active_games:
            try:
                print(f"Processing game {game.id} (Player: {game.player.username})")
                self.process_game(game)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing game {game.id}: {str(e)}')
                )
    
    def process_game(self, game):
        """Process a single game"""
        now = timezone.now()
        
        # Update hostage timer (only once per second)
        timer_should_update = False
        if game.hostage_timer > 0:
            # Check if enough time has passed to update timer (1 second)
            if game.last_timer_update:
                time_since_last_timer_update = (now - game.last_timer_update).total_seconds()
                if time_since_last_timer_update >= 1.0:
                    timer_should_update = True
            else:
                # First timer update - initialize last_timer_update
                timer_should_update = True
            
            if timer_should_update:
                game.hostage_timer -= 1.0
                game.last_timer_update = now
                print(f"Timer updated for game {game.id}: {game.hostage_timer}")
            
            # Check if timer expired
            if game.hostage_timer <= 0:
                self.end_game(game, won=True, reason='Hostages escaped successfully!')
                return
        
        # Check if Ultron is paused
        if game.ultron_paused_until and now < game.ultron_paused_until:
            # Ultron is still paused, don't move
            game.save()
            return
        elif game.ultron_paused_until and now >= game.ultron_paused_until:
            # Pause has ended
            game.ultron_paused_until = None
        
        # Check if enough time has passed for Ultron to move (1 second per tile)
        if game.last_move_time:
            time_since_last_move = (now - game.last_move_time).total_seconds()
            if time_since_last_move < 1.0:
                # Not enough time has passed
                game.save()
                return
        else:
            # First move - initialize last_move_time
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
            game.last_move_time = now  # Update last move time
            print(f"Ultron moved: ({old_x}, {old_y}) -> ({game.ultron_position_x}, {game.ultron_position_y})")
            
            # Check if Ultron reached target
            if (game.ultron_position_x == game.ultron_target_x and 
                game.ultron_position_y == game.ultron_target_y):
                print(f"Ultron reached target at ({game.ultron_target_x}, {game.ultron_target_y})")
                self.end_game(game, won=False, reason='Ultron escaped')
                return
            
            # Check for shield interactions
            shield_at_position = shields.filter(
                position_x=game.ultron_position_x,
                position_y=game.ultron_position_y
            ).first()
            
            if shield_at_position:
                self.handle_shield_interaction(game, shield_at_position)
        
        # Save game state
        game.save()
    
    def handle_shield_interaction(self, game, shield):
        """Handle Ultron hitting a shield"""
        now = timezone.now()
        
        print(f"Shield interaction! Game {game.id}, Shield type: {shield.shield_type} at ({shield.position_x}, {shield.position_y})")
        
        if shield.shield_type == 'blue':
            # Blue shields block completely - this shouldn't happen as AI avoids them
            damage = 1
        elif shield.shield_type == 'yellow':
            # Yellow shields reduce hostage timer by 2 seconds when passed through
            old_timer = game.hostage_timer
            game.hostage_timer = max(0, game.hostage_timer - 2.0)
            print(f"Yellow shield hit! Timer: {old_timer} -> {game.hostage_timer}")
            damage = 1  # Shield is destroyed after use
            
            # Log timer reduction
            GameEvent.objects.create(
                game_session=game,
                event_type='timer_reduced',
                data=json.dumps({
                    'timer_reduction': 2.0,
                    'new_timer': game.hostage_timer,
                    'position': [shield.position_x, shield.position_y]
                })
            )
        elif shield.shield_type == 'red':
            # Red shields pause Ultron for 4 seconds
            game.ultron_paused_until = now + timedelta(seconds=4)
            damage = 1  # Shield is destroyed after use
            
            # Log pause effect
            GameEvent.objects.create(
                game_session=game,
                event_type='ultron_paused',
                data=json.dumps({
                    'pause_duration': 4.0,
                    'paused_until': game.ultron_paused_until.isoformat(),
                    'position': [shield.position_x, shield.position_y]
                })
            )
        else:
            damage = 1
        
        shield.durability -= damage
        
        if shield.durability <= 0:
            shield.is_active = False
            shield.save()
            
            # Log shield destruction
            GameEvent.objects.create(
                game_session=game,
                event_type='shield_destroyed',
                data=json.dumps({
                    'shield_type': shield.shield_type,
                    'position': [shield.position_x, shield.position_y]
                })
            )
        else:
            shield.save()
    
    def end_game(self, game, won, reason=''):
        """End a game session"""
        from game.models import Leaderboard
        
        game.status = 'won' if won else 'lost'
        game.game_end_time = timezone.now()
        
        # Calculate score
        time_survived = (game.game_end_time - game.game_start_time).total_seconds()
        
        if won:
            # Player wins: Full 1000 points for winning
            game.score = 1000
        else:
            # Player loses: More points for surviving longer (closer to 40 seconds)
            # Score = time_survived * 20 (max ~800 points if survived close to 40 seconds)
            game.score = int(time_survived * 20)
        
        game.save()
        
        # Update user stats
        user = game.player
        user.games_played += 1
        user.total_score += game.score
        
        if won:
            user.games_won += 1
        
        if game.score > user.best_score:
            user.best_score = game.score
        
        user.save()
        
        # Update leaderboard
        leaderboard, created = Leaderboard.objects.get_or_create(player=user)
        leaderboard.total_games += 1
        leaderboard.total_time_survived += time_survived
        
        if won:
            leaderboard.games_won += 1
        
        if game.score > leaderboard.highest_score:
            leaderboard.highest_score = game.score
        
        leaderboard.save()
        
        # Log game end
        GameEvent.objects.create(
            game_session=game,
            event_type='game_won' if won else 'game_lost',
            data=json.dumps({
                'reason': reason,
                'final_score': game.score,
                'time_survived': time_survived
            })
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Game {game.id} ended: {"Won" if won else "Lost"} - {reason}')
        )
