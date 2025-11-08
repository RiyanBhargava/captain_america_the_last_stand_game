import heapq
import math
from typing import List, Tuple, Optional

class UltronAI:
    """
    AI for Ultron pathfinding using A* algorithm
    """
    
    def __init__(self, grid_size: int = 15):
        self.grid_size = grid_size
        self.current_position = (0, 7)  # Start position
        self.target_position = (14, 7)  # End position
        self.current_path = []
        self.move_delay = 0.8  # Seconds per tile
        self.is_paused = False
        self.pause_time_left = 0
    
    def set_position(self, x: int, y: int):
        """Set Ultron's current position"""
        self.current_position = (x, y)
    
    def set_target(self, x: int, y: int):
        """Set Ultron's target position"""
        self.target_position = (x, y)
    
    def heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Manhattan distance heuristic"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_neighbors(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        x, y = position
        neighbors = []
        
        # 4-directional movement (up, down, left, right)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                neighbors.append((new_x, new_y))
        
        return neighbors
    
    def find_path(self, obstacles: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Find optimal path using A* algorithm
        obstacles: List of positions with blue shields (full blocks)
        """
        start = self.current_position
        goal = self.target_position
        
        # Convert obstacles to set for O(1) lookup
        obstacle_set = set(obstacles)
        
        # A* algorithm
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current):
                if neighbor in obstacle_set:
                    continue  # Skip blocked positions
                
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return []
    
    def get_next_move(self, shields: List[dict]) -> Optional[Tuple[int, int]]:
        """
        Get Ultron's next move based on current shield positions
        shields: List of shield dictionaries with 'type' and 'position' keys
        """
        # Extract blue shield positions (full blocks)
        blue_shields = []
        for shield in shields:
            if shield['type'] == 'blue':
                pos = shield['position']
                blue_shields.append((pos[0], pos[1]))
        
        # Find new path if needed
        if not self.current_path or self.current_path[0] in blue_shields:
            self.current_path = self.find_path(blue_shields)
        
        # Return next position if path exists
        if self.current_path:
            next_pos = self.current_path.pop(0)
            self.current_position = next_pos
            return next_pos
        
        return None
    
    def handle_shield_effect(self, shield_type: str) -> dict:
        """
        Handle the effect when Ultron passes through a shield
        Returns effect information
        """
        effect = {'type': shield_type, 'applied': True}
        
        if shield_type == 'red':
            # Pause shield - Ultron pauses for 2 seconds
            self.is_paused = True
            self.pause_time_left = 2.0
            effect['pause_duration'] = 2.0
        
        elif shield_type == 'yellow':
            # Delay shield - increases hostage timer by 2 seconds
            effect['timer_increase'] = 2.0
        
        return effect
    
    def update_pause_status(self, delta_time: float) -> bool:
        """
        Update pause status and return True if Ultron can move
        delta_time: Time elapsed since last update
        """
        if self.is_paused:
            self.pause_time_left -= delta_time
            if self.pause_time_left <= 0:
                self.is_paused = False
                self.pause_time_left = 0
                return True
            return False
        return True
    
    def calculate_optimal_strategy(self, shields: List[dict]) -> dict:
        """
        Calculate strategic information for the AI
        Returns information about current strategy and estimated time to goal
        """
        blue_shields = [(s['position'][0], s['position'][1]) for s in shields if s['type'] == 'blue']
        path = self.find_path(blue_shields)
        
        if not path:
            return {
                'path_exists': False,
                'estimated_time': float('inf'),
                'path_length': 0,
                'strategy': 'blocked'
            }
        
        # Calculate time considering shield effects
        estimated_time = len(path) * self.move_delay
        
        # Add pause time for red shields in path
        red_shields_in_path = 0
        yellow_shields_in_path = 0
        
        for pos in path:
            for shield in shields:
                shield_pos = (shield['position'][0], shield['position'][1])
                if pos == shield_pos:
                    if shield['type'] == 'red':
                        red_shields_in_path += 1
                    elif shield['type'] == 'yellow':
                        yellow_shields_in_path += 1
        
        # Add pause time for red shields
        estimated_time += red_shields_in_path * 2.0
        
        return {
            'path_exists': True,
            'estimated_time': estimated_time,
            'path_length': len(path),
            'red_shields_in_path': red_shields_in_path,
            'yellow_shields_in_path': yellow_shields_in_path,
            'strategy': 'pathfinding',
            'next_positions': path[:3]  # Next 3 moves for preview
        }
