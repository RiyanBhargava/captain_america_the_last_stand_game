from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import GameSession, Shield, GameEvent, Leaderboard
from .game_logic import UltronAI
import json

@login_required
def game_view(request):
    """Main game view"""
    # Get or create active game session
    active_game = GameSession.objects.filter(
        player=request.user, 
        status='active'
    ).first()
    
    # Check if we should show tutorial
    show_tutorial = request.session.pop('show_tutorial', False)
    
    return render(request, 'game/game.html', {
        'game_session': active_game,
        'user': request.user,
        'show_tutorial': show_tutorial
    })

@login_required
def leaderboard_view(request):
    """Leaderboard view"""
    top_players = Leaderboard.objects.all()[:10]
    user_stats = Leaderboard.objects.filter(player=request.user).first()
    
    return render(request, 'game/leaderboard.html', {
        'top_players': top_players,
        'user_stats': user_stats
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def start_game(request):
    """Start a new game session"""
    try:
        # End any active games
        GameSession.objects.filter(
            player=request.user, 
            status='active'
        ).update(status='lost')
        
        # Create new game
        game = GameSession.objects.create(
            player=request.user,
            status='active',
            hostage_timer=40.0,
            ultron_position_x=0,
            ultron_position_y=0,
            ultron_target_x=13,
            ultron_target_y=13
        )
        
        return JsonResponse({
            'success': True,
            'game_id': game.id,
            'ultron_position': [game.ultron_position_x, game.ultron_position_y],
            'target_position': [game.ultron_target_x, game.ultron_target_y],
            'hostage_timer': game.hostage_timer
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def place_shield(request):
    """Place a shield on the game board"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        shield_type = data.get('shield_type')
        position_x = data.get('position_x')
        position_y = data.get('position_y')
        
        game = get_object_or_404(GameSession, id=game_id, player=request.user, status='active')
        
        # Check if position is valid
        if not (0 <= position_x <= 14 and 0 <= position_y <= 14):
            return JsonResponse({'success': False, 'error': 'Invalid position'})
        
        # Check if position is already occupied
        if Shield.objects.filter(
            game_session=game, 
            position_x=position_x, 
            position_y=position_y,
            is_active=True
        ).exists():
            return JsonResponse({'success': False, 'error': 'Position already occupied'})
        
        # Check if it's Ultron's current position
        if position_x == game.ultron_position_x and position_y == game.ultron_position_y:
            return JsonResponse({'success': False, 'error': 'Cannot place shield on Ultron'})
        
        # Set durability based on shield type
        if shield_type == 'blue':
            durability = 1  # Blue shields block but are destroyed when hit
        elif shield_type == 'yellow':
            durability = 1  # Yellow shields reduce timer and are destroyed
        elif shield_type == 'red':
            durability = 1  # Red shields pause and are destroyed
        else:
            durability = 1
        
        # Create shield
        shield = Shield.objects.create(
            game_session=game,
            shield_type=shield_type,
            position_x=position_x,
            position_y=position_y,
            durability=durability
        )
        
        # Log event
        GameEvent.objects.create(
            game_session=game,
            event_type='shield_placed',
            data=json.dumps({
                'shield_type': shield_type,
                'position': [position_x, position_y]
            })
        )
        
        return JsonResponse({
            'success': True,
            'shield_id': shield.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["GET"])
def get_game_state(request, game_id):
    """Get current game state - also processes game logic for PythonAnywhere compatibility"""
    try:
        game = get_object_or_404(GameSession, id=game_id, player=request.user)
        
        # Process game logic if game is active (for PythonAnywhere free tier)
        if game.status == 'active':
            from game.management.commands.run_game_loop import Command as GameLoopCommand
            loop_command = GameLoopCommand()
            try:
                loop_command.process_game(game)
                game.refresh_from_db()  # Reload from database after processing
            except Exception as e:
                print(f"Error processing game: {e}")
        
        shields = []
        for shield in game.shields.filter(is_active=True):
            shields.append({
                'id': shield.id,
                'type': shield.shield_type,
                'position': [shield.position_x, shield.position_y]
            })
        
        return JsonResponse({
            'success': True,
            'game_status': game.status,
            'ultron_position': [game.ultron_position_x, game.ultron_position_y],
            'target_position': [game.ultron_target_x, game.ultron_target_y],
            'hostage_timer': game.hostage_timer,
            'score': game.score,
            'shields': shields
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def end_game(request):
    """End the current game"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        won = data.get('won', False)
        
        game = get_object_or_404(GameSession, id=game_id, player=request.user, status='active')
        
        # Calculate final score
        time_survived = (timezone.now() - game.game_start_time).total_seconds()
        game.time_survived = time_survived
        
        if won:
            game.status = 'won'
            game.score = int(game.hostage_timer * 10)  # Score based on final timer
        else:
            game.status = 'lost'
            game.score = int(time_survived * 5)  # Score based on survival time
        
        game.game_end_time = timezone.now()
        game.save()
        
        # Update leaderboard
        leaderboard, created = Leaderboard.objects.get_or_create(player=request.user)
        leaderboard.total_games += 1
        leaderboard.total_time_survived += time_survived
        
        if won:
            leaderboard.games_won += 1
        
        if game.score > leaderboard.highest_score:
            leaderboard.highest_score = game.score
        
        leaderboard.save()
        
        # Update user stats
        user = request.user
        user.games_played += 1
        user.total_score += game.score
        
        if won:
            user.games_won += 1
        
        if game.score > user.best_score:
            user.best_score = game.score
        
        user.save()
        
        # Log event
        GameEvent.objects.create(
            game_session=game,
            event_type='game_won' if won else 'game_lost',
            data=json.dumps({
                'final_score': game.score,
                'time_survived': time_survived,
                'hostage_timer': game.hostage_timer
            })
        )
        
        return JsonResponse({
            'success': True,
            'final_score': game.score,
            'time_survived': time_survived,
            'won': won
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
