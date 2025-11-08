// Captain America Shield Defense - Game JavaScript

class ShieldDefenseGame {
    constructor(gameId) {
        this.gameId = gameId;
        this.selectedShieldType = 'blue';
        this.gameBoard = null;
        this.gameActive = false;
        this.lastShieldPlacement = 0;
        this.shieldPlacementCooldown = 4000; // 4 seconds
        this.gameLoop = null;
        
        this.initializeGame();
        this.setupEventListeners();
        this.startPolling();
    }
    
    initializeGame() {
        this.gameBoard = document.getElementById('game-board');
        this.createGameBoard();
        this.updateShieldSelection();
    }
    
    createGameBoard() {
        this.gameBoard.innerHTML = '';
        
        for (let y = 0; y < 15; y++) {
            for (let x = 0; x < 15; x++) {
                const cell = document.createElement('div');
                cell.className = 'grid-cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                cell.addEventListener('click', () => this.handleCellClick(x, y));
                this.gameBoard.appendChild(cell);
            }
        }
    }
    
    startPolling() {
        // Poll game state every second
        this.gameLoop = setInterval(() => {
            this.fetchGameState();
        }, 1000);
        
        // Initial fetch
        this.fetchGameState();
    }
    
    async fetchGameState() {
        try {
            const response = await fetch(`/api/game/state/${this.gameId}/`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.updateGameState(data);
                }
            }
        } catch (error) {
            console.error('Error fetching game state:', error);
        }
    }
    
    updateGameState(data) {
        // Update game stats
        document.getElementById('hostage-timer').textContent = Math.ceil(data.hostage_timer);
        document.getElementById('score').textContent = data.score;
        document.getElementById('game-status').textContent = data.game_status.charAt(0).toUpperCase() + data.game_status.slice(1);
        
        // Update timer color if critical
        const timerElement = document.getElementById('hostage-timer');
        if (data.hostage_timer <= 10) {
            timerElement.classList.add('timer-critical');
        } else {
            timerElement.classList.remove('timer-critical');
        }
        
        // Clear board
        this.clearBoard();
        
        // Place Ultron
        this.placeUltron(data.ultron_position[0], data.ultron_position[1]);
        
        // Place target
        this.placeTarget(data.target_position[0], data.target_position[1]);
        
        // Place shields
        data.shields.forEach(shield => {
            this.placeShield(shield.position[0], shield.position[1], shield.type);
        });
        
        // Update game status
        this.gameActive = (data.game_status === 'active');
        this.updateGameControls();
        
        // Check for game end
        if (data.game_status === 'won' || data.game_status === 'lost') {
            this.handleGameEnd({
                won: data.game_status === 'won',
                final_score: data.score,
                message: data.game_status === 'won' ? 'Victory! Hostages saved!' : 'Defeat! Ultron escaped!'
            });
        }
    }
    
    clearBoard() {
        const cells = this.gameBoard.querySelectorAll('.grid-cell');
        cells.forEach(cell => {
            cell.className = 'grid-cell';
            cell.innerHTML = '';
        });
    }
    
    placeUltron(x, y) {
        const cell = this.getCell(x, y);
        if (cell) {
            cell.classList.add('ultron');
        }
    }
    
    placeTarget(x, y) {
        const cell = this.getCell(x, y);
        if (cell) {
            cell.classList.add('target');
        }
    }
    
    placeShield(x, y, type) {
        const cell = this.getCell(x, y);
        if (cell) {
            cell.classList.add('shield', type);
            cell.classList.add('shield-placed');
            
            // Remove animation class after animation completes
            setTimeout(() => {
                cell.classList.remove('shield-placed');
            }, 500);
        }
    }
    
    getCell(x, y) {
        return this.gameBoard.querySelector(`[data-x="${x}"][data-y="${y}"]`);
    }
    
    handleCellClick(x, y) {
        if (!this.gameActive) {
            this.showMessage('Starting game...', 'info');
            this.startGame();
            return;
        }
        
        // Check cooldown
        const now = Date.now();
        if (now - this.lastShieldPlacement < this.shieldPlacementCooldown) {
            const remaining = Math.ceil((this.shieldPlacementCooldown - (now - this.lastShieldPlacement)) / 1000);
            this.showMessage(`Shield cooldown: ${remaining}s remaining`, 'warning');
            return;
        }
        
        this.placeShieldAtPosition(x, y);
    }
    
    async placeShieldAtPosition(x, y) {
        try {
            const response = await fetch('/api/game/place-shield/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    game_id: this.gameId,
                    shield_type: this.selectedShieldType,
                    position_x: x,
                    position_y: y
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.lastShieldPlacement = Date.now();
                this.updateCooldownDisplay();
                this.showMessage(`${this.selectedShieldType.charAt(0).toUpperCase() + this.selectedShieldType.slice(1)} shield placed!`, 'success');
            } else {
                this.showMessage(data.error || 'Failed to place shield', 'error');
            }
        } catch (error) {
            console.error('Error placing shield:', error);
            this.showMessage('Error placing shield', 'error');
        }
    }
    
    updateCooldownDisplay() {
        const cooldownElement = document.getElementById('shield-cooldown');
        if (cooldownElement) {
            let remaining = this.shieldPlacementCooldown / 1000;
            
            const updateTimer = () => {
                if (remaining > 0) {
                    cooldownElement.textContent = `${remaining}s`;
                    remaining--;
                    setTimeout(updateTimer, 1000);
                } else {
                    cooldownElement.textContent = 'Ready';
                }
            };
            
            updateTimer();
        }
    }
    
    setupEventListeners() {
        // Shield type selection
        document.querySelectorAll('.shield-type').forEach(element => {
            element.addEventListener('click', () => {
                const shieldType = element.dataset.shieldType;
                this.selectShieldType(shieldType);
            });
        });
        
        // Game control buttons
        const startButton = document.getElementById('start-game');
        if (startButton) {
            startButton.addEventListener('click', () => this.startGame());
        }
        
        const pauseButton = document.getElementById('pause-game');
        if (pauseButton) {
            pauseButton.addEventListener('click', () => this.pauseGame());
        }
        
        const resumeButton = document.getElementById('resume-game');
        if (resumeButton) {
            resumeButton.addEventListener('click', () => this.resumeGame());
        }
    }
    
    selectShieldType(type) {
        this.selectedShieldType = type;
        this.updateShieldSelection();
    }
    
    updateShieldSelection() {
        document.querySelectorAll('.shield-type').forEach(element => {
            element.classList.remove('selected');
        });
        
        const selectedElement = document.querySelector(`[data-shield-type="${this.selectedShieldType}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }
    }
    
    async startGame() {
        try {
            const response = await fetch('/api/game/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            if (data.success) {
                this.gameActive = true;
                this.lastShieldPlacement = 0;
                this.updateGameControls();
                this.showMessage('Game started! Defend the hostages!', 'success');
                this.fetchGameState(); // Immediate update
            } else {
                this.showMessage(data.error || 'Failed to start game', 'error');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            this.showMessage('Error starting game', 'error');
        }
    }
    
    pauseGame() {
        // Implement pause functionality if needed
        this.showMessage('Pause functionality coming soon!', 'info');
    }
    
    resumeGame() {
        // Implement resume functionality if needed
        this.showMessage('Resume functionality coming soon!', 'info');
    }
    
    updateGameControls() {
        const startButton = document.getElementById('start-game');
        const pauseButton = document.getElementById('pause-game');
        const resumeButton = document.getElementById('resume-game');
        
        if (startButton) startButton.disabled = this.gameActive;
        if (pauseButton) pauseButton.disabled = !this.gameActive;
        if (resumeButton) resumeButton.style.display = this.gameActive ? 'none' : 'inline-block';
    }
    
    handleGameEnd(data) {
        this.gameActive = false;
        this.updateGameControls();
        
        // Stop polling
        if (this.gameLoop) {
            clearInterval(this.gameLoop);
        }
        
        const title = data.won ? '🎉 VICTORY! 🎉' : '💥 DEFEAT! 💥';
        const message = data.message + `\n\nFinal Score: ${data.final_score}`;
        
        this.showGameEndDialog(title, message, data.won, data.final_score);
    }
    
    showGameEndDialog(title, message, won, score) {
        const dialog = document.createElement('div');
        dialog.className = 'game-message';
        dialog.innerHTML = `
            <h2>${title}</h2>
            <p>${message.replace(/\n/g, '<br>')}</p>
            <div style="margin-top: 2rem;">
                <button class="btn" onclick="this.parentElement.parentElement.remove()">Close</button>
                <button class="btn secondary" onclick="location.reload()">Play Again</button>
                <a href="/game/leaderboard/" class="btn secondary">Leaderboard</a>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (dialog.parentElement) {
                dialog.remove();
            }
        }, 10000);
    }
    
    showMessage(message, type = 'info', duration = 3000) {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${type}`;
        messageElement.textContent = message;
        messageElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 1rem;
            border-radius: 5px;
            z-index: 1000;
            border-left: 4px solid ${this.getMessageColor(type)};
        `;
        
        document.body.appendChild(messageElement);
        
        setTimeout(() => {
            if (messageElement.parentElement) {
                messageElement.remove();
            }
        }, duration);
    }
    
    getMessageColor(type) {
        const colors = {
            'success': '#00ff00',
            'error': '#ff0000',
            'warning': '#ffff00',
            'info': '#00aaff'
        };
        return colors[type] || '#ffffff';
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    destroy() {
        if (this.gameLoop) {
            clearInterval(this.gameLoop);
        }
    }
}

// Google Authentication
function initGoogleAuth() {
    gapi.load('auth2', function() {
        gapi.auth2.init({
            client_id: window.googleClientId
        });
    });
}

function signInWithGoogle() {
    const authInstance = gapi.auth2.getAuthInstance();
    authInstance.signIn().then(function(googleUser) {
        const idToken = googleUser.getAuthResponse().id_token;
        
        fetch('/auth/google-auth/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                token: idToken
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                alert('Authentication failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Authentication failed');
        });
    });
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Google Auth if on login page
    if (window.googleClientId) {
        initGoogleAuth();
    }
    
    // Initialize game if game board exists
    const gameBoard = document.getElementById('game-board');
    if (gameBoard && window.gameId) {
        window.game = new ShieldDefenseGame(window.gameId);
        
        // Show initial instructions
        setTimeout(() => {
            if (!window.game.gameActive) {
                window.game.showMessage('Click "Start New Game" or click any tile to begin!', 'info', 5000);
            }
        }, 2000);
    }
});
