import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import GameSession, Shield, GameEvent
from .game_logic import UltronAI

User = get_user_model()

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        self.ultron_ai = UltronAI()
        self.game_task = None
        
        # Join game group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Initialize game state
        await self.initialize_game()
    
    async def disconnect(self, close_code):
        # Cancel game loop
        if self.game_task:
            self.game_task.cancel()
        
        # Leave game group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'place_shield':
                await self.handle_place_shield(data)
            elif message_type == 'start_game':
                await self.handle_start_game()
            elif message_type == 'pause_game':
                await self.handle_pause_game()
            elif message_type == 'resume_game':
                await self.handle_resume_game()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def initialize_game(self):
        """Initialize game state and start the game loop"""
        game = await self.get_game()
        if game:
            # Set up Ultron AI
            self.ultron_ai.set_position(game.ultron_position_x, game.ultron_position_y)
            self.ultron_ai.set_target(game.ultron_target_x, game.ultron_target_y)
            
            # Send initial game state
            await self.send_game_state()
            
            # Start game loop if game is active
            if game.status == 'active':
                self.game_task = asyncio.create_task(self.game_loop())
    
    async def game_loop(self):
        """Main game loop for Ultron movement"""
        try:
            while True:
                game = await self.get_game()
                if not game or game.status != 'active':
                    break
                
                # Check if Ultron can move (not paused)
                if self.ultron_ai.update_pause_status(0.8):
                    # Get current shields
                    shields = await self.get_shields_data()
                    
                    # Get Ultron's next move
                    next_move = self.ultron_ai.get_next_move(shields)
                    
                    if next_move:
                        # Update Ultron position in database
                        await self.update_ultron_position(next_move[0], next_move[1])
                        
                        # Check for shield effects
                        shield_effect = await self.check_shield_at_position(next_move[0], next_move[1])
                        if shield_effect:
                            effect_result = self.ultron_ai.handle_shield_effect(shield_effect['type'])
                            await self.handle_shield_effect(shield_effect, effect_result)
                        
                        # Check win/lose conditions
                        if next_move == self.ultron_ai.target_position:
                            await self.end_game(won=False)
                            break
                        
                        # Send updated game state
                        await self.send_game_state()
                    else:
                        # No path available - player wins
                        await self.end_game(won=True)
                        break
                
                # Wait for next move (0.8 seconds per tile)
                await asyncio.sleep(0.8)
                
        except asyncio.CancelledError:
            pass
    
    async def handle_place_shield(self, data):
        """Handle shield placement"""
        shield_type = data.get('shield_type')
        position_x = data.get('position_x')
        position_y = data.get('position_y')
        
        # Validate and place shield
        success = await self.place_shield(shield_type, position_x, position_y)
        
        if success:
            await self.send_game_state()
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Cannot place shield at this position'
            }))
    
    async def handle_start_game(self):
        """Handle game start"""
        await self.reset_game()
        await self.send_game_state()
        
        # Start game loop
        if self.game_task:
            self.game_task.cancel()
        self.game_task = asyncio.create_task(self.game_loop())
    
    async def handle_pause_game(self):
        """Handle game pause"""
        if self.game_task:
            self.game_task.cancel()
        await self.update_game_status('paused')
    
    async def handle_resume_game(self):
        """Handle game resume"""
        await self.update_game_status('active')
        self.game_task = asyncio.create_task(self.game_loop())
    
    async def handle_shield_effect(self, shield_data, effect_result):
        """Handle shield effects on Ultron"""
        if effect_result['type'] == 'yellow':
            # Increase hostage timer
            await self.increase_hostage_timer(2.0)
        
        # Send effect notification
        await self.send(text_data=json.dumps({
            'type': 'shield_effect',
            'shield_type': shield_data['type'],
            'position': [shield_data['position_x'], shield_data['position_y']],
            'effect': effect_result
        }))
    
    async def send_game_state(self):
        """Send current game state to client"""
        game = await self.get_game()
        shields = await self.get_shields_data()
        
        if game:
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'ultron_position': [game.ultron_position_x, game.ultron_position_y],
                'target_position': [game.ultron_target_x, game.ultron_target_y],
                'hostage_timer': game.hostage_timer,
                'score': game.score,
                'status': game.status,
                'shields': shields
            }))
    
    async def end_game(self, won=False):
        """End the game"""
        await self.update_game_status('won' if won else 'lost')
        
        # Calculate final score
        game = await self.get_game()
        if game:
            final_score = await self.calculate_final_score(game, won)
            
            await self.send(text_data=json.dumps({
                'type': 'game_ended',
                'won': won,
                'final_score': final_score,
                'message': 'Victory! Hostages saved!' if won else 'Defeat! Ultron escaped!'
            }))
    
    # Database operations (sync to async)
    @database_sync_to_async
    def get_game(self):
        try:
            return GameSession.objects.get(id=self.game_id)
        except GameSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_shields_data(self):
        try:
            game = GameSession.objects.get(id=self.game_id)
            shields = []
            for shield in game.shields.filter(is_active=True):
                shields.append({
                    'id': shield.id,
                    'type': shield.shield_type,
                    'position': [shield.position_x, shield.position_y]
                })
            return shields
        except GameSession.DoesNotExist:
            return []
    
    @database_sync_to_async
    def place_shield(self, shield_type, position_x, position_y):
        try:
            game = GameSession.objects.get(id=self.game_id)
            
            # Validation
            if not (0 <= position_x <= 14 and 0 <= position_y <= 14):
                return False
            
            if Shield.objects.filter(
                game_session=game, 
                position_x=position_x, 
                position_y=position_y,
                is_active=True
            ).exists():
                return False
            
            if position_x == game.ultron_position_x and position_y == game.ultron_position_y:
                return False
            
            # Create shield
            Shield.objects.create(
                game_session=game,
                shield_type=shield_type,
                position_x=position_x,
                position_y=position_y
            )
            
            return True
            
        except GameSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_ultron_position(self, x, y):
        try:
            game = GameSession.objects.get(id=self.game_id)
            game.ultron_position_x = x
            game.ultron_position_y = y
            game.save()
        except GameSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_game_status(self, status):
        try:
            game = GameSession.objects.get(id=self.game_id)
            game.status = status
            game.save()
        except GameSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def check_shield_at_position(self, x, y):
        try:
            game = GameSession.objects.get(id=self.game_id)
            shield = Shield.objects.filter(
                game_session=game,
                position_x=x,
                position_y=y,
                is_active=True
            ).first()
            
            if shield:
                return {
                    'type': shield.shield_type,
                    'position_x': shield.position_x,
                    'position_y': shield.position_y
                }
            return None
            
        except GameSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def increase_hostage_timer(self, amount):
        try:
            game = GameSession.objects.get(id=self.game_id)
            game.hostage_timer += amount
            game.save()
        except GameSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def reset_game(self):
        try:
            game = GameSession.objects.get(id=self.game_id)
            game.status = 'active'
            game.hostage_timer = 40.0
            game.ultron_position_x = 0
            game.ultron_position_y = 7
            game.score = 0
            game.save()
            
            # Clear all shields
            game.shields.all().delete()
            
            # Reset AI
            self.ultron_ai.set_position(0, 7)
            self.ultron_ai.current_path = []
            self.ultron_ai.is_paused = False
            self.ultron_ai.pause_time_left = 0
            
        except GameSession.DoesNotExist:
            pass
    
    @database_sync_to_async
    def calculate_final_score(self, game, won):
        if won:
            return int(game.hostage_timer * 10)
        else:
            return int((40.0 - game.hostage_timer) * 5)
