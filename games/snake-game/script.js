class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.gridSize = 20;
        this.tileCount = this.canvas.width / this.gridSize;
        
        // Game state
        this.snake = [{ x: 10, y: 10 }];
        this.food = {};
        this.dx = 0;
        this.dy = 0;
        this.score = 0;
        this.highScore = localStorage.getItem('snakeHighScore') || 0;
        this.gameRunning = false;
        this.gameStarted = false;
        this.gamePaused = false;
        this.gameSpeed = 150;
        this.level = 1;
        
        // Animation properties
        this.animationId = null;
        this.lastRenderTime = 0;
        
        // UI elements
        this.currentScoreElement = document.getElementById('current-score');
        this.highScoreElement = document.getElementById('high-score');
        this.finalScoreElement = document.getElementById('finalScore');
        this.snakeLengthElement = document.getElementById('snakeLength');
        this.gameSpeedElement = document.getElementById('gameSpeed');
        this.gameLevelElement = document.getElementById('gameLevel');
        this.gameOverlay = document.getElementById('gameOverlay');
        this.startScreen = document.getElementById('startScreen');
        this.startButton = document.getElementById('startButton');
        this.overlayTitle = document.getElementById('overlayTitle');
        this.overlayMessage = document.getElementById('overlayMessage');
        
        // Sound elements
        this.eatSound = document.getElementById('eatSound');
        this.gameOverSound = document.getElementById('gameOverSound');
        
        this.init();
    }
    
    init() {
        this.updateHighScore();
        this.generateFood();
        this.addEventListeners();
        this.showStartScreen();
        this.updateStats();
    }
    
    addEventListeners() {
        // Keyboard controls
        document.addEventListener('keydown', this.handleKeyPress.bind(this));
        
        // Start button
        this.startButton.addEventListener('click', this.startGame.bind(this));
        
        // Prevent arrow keys from scrolling
        window.addEventListener('keydown', (e) => {
            if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)) {
                e.preventDefault();
            }
        });
    }
    
    handleKeyPress(e) {
        const key = e.key.toLowerCase();
        
        if (!this.gameStarted) {
            if (e.code === 'Space' || key === 'enter') {
                this.startGame();
            }
            return;
        }
        
        if (e.code === 'Space') {
            this.togglePause();
            return;
        }
        
        if (key === 'r') {
            this.restartGame();
            return;
        }
        
        if (this.gamePaused || !this.gameRunning) return;
        
        // Movement controls
        const newDirection = this.getNewDirection(key);
        if (newDirection) {
            // Prevent reverse direction
            if (this.snake.length > 1) {
                const head = this.snake[0];
                const neck = this.snake[1];
                const wouldReverse = (head.x + newDirection.dx === neck.x && 
                                    head.y + newDirection.dy === neck.y);
                if (wouldReverse) return;
            }
            
            this.dx = newDirection.dx;
            this.dy = newDirection.dy;
        }
    }
    
    getNewDirection(key) {
        const directions = {
            'arrowup': { dx: 0, dy: -1 },
            'arrowdown': { dx: 0, dy: 1 },
            'arrowleft': { dx: -1, dy: 0 },
            'arrowright': { dx: 1, dy: 0 },
            'w': { dx: 0, dy: -1 },
            's': { dx: 0, dy: 1 },
            'a': { dx: -1, dy: 0 },
            'd': { dx: 1, dy: 0 }
        };
        
        return directions[key] || null;
    }
    
    startGame() {
        this.hideStartScreen();
        this.resetGame();
        this.gameStarted = true;
        this.gameRunning = true;
        this.gamePaused = false;
        this.gameLoop();
    }
    
    resetGame() {
        this.snake = [{ x: 10, y: 10 }];
        this.dx = 0;
        this.dy = 0;
        this.score = 0;
        this.level = 1;
        this.gameSpeed = 150;
        this.generateFood();
        this.updateScore();
        this.updateStats();
        this.hideGameOverlay();
    }
    
    restartGame() {
        this.gameRunning = false;
        this.gameStarted = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.startGame();
    }
    
    togglePause() {
        if (!this.gameRunning) return;
        
        this.gamePaused = !this.gamePaused;
        if (this.gamePaused) {
            this.showPauseOverlay();
        } else {
            this.hideGameOverlay();
            this.gameLoop();
        }
    }
    
    gameLoop(currentTime = 0) {
        if (!this.gameRunning || this.gamePaused) return;
        
        if (currentTime - this.lastRenderTime >= this.gameSpeed) {
            this.update();
            this.draw();
            this.lastRenderTime = currentTime;
        }
        
        this.animationId = requestAnimationFrame(this.gameLoop.bind(this));
    }
    
    update() {
        if (this.dx === 0 && this.dy === 0) return;
        
        const head = { x: this.snake[0].x + this.dx, y: this.snake[0].y + this.dy };
        
        // Check wall collision
        if (head.x < 0 || head.x >= this.tileCount || 
            head.y < 0 || head.y >= this.tileCount) {
            this.gameOver();
            return;
        }
        
        // Check self collision
        if (this.snake.some(segment => segment.x === head.x && segment.y === head.y)) {
            this.gameOver();
            return;
        }
        
        this.snake.unshift(head);
        
        // Play subtle move sound
        if (this.snake.length > 1) {
            this.playMoveSound();
        }
        
        // Check food collision
        if (head.x === this.food.x && head.y === this.food.y) {
            this.eatFood();
        } else {
            this.snake.pop();
        }
        
        this.updateStats();
    }
    
    eatFood() {
        this.score += 10;
        this.playEatSound();
        this.createParticleEffect(this.food.x, this.food.y);
        this.generateFood();
        this.updateScore();
        this.updateLevel();
        
        // Add score pop animation
        this.currentScoreElement.classList.add('score-pop');
        setTimeout(() => {
            this.currentScoreElement.classList.remove('score-pop');
        }, 300);
        
        // Add canvas glow effect
        this.canvas.classList.add('canvas-glow-intense');
        setTimeout(() => {
            this.canvas.classList.remove('canvas-glow-intense');
        }, 200);
    }
    
    updateLevel() {
        const newLevel = Math.floor(this.score / 100) + 1;
        if (newLevel > this.level) {
            this.level = newLevel;
            this.gameSpeed = Math.max(80, 150 - (this.level - 1) * 10);
            
            // Level up animation
            this.canvas.classList.add('level-up-flash');
            setTimeout(() => {
                this.canvas.classList.remove('level-up-flash');
            }, 1500);
        }
    }
    
    generateFood() {
        let newFood;
        do {
            newFood = {
                x: Math.floor(Math.random() * this.tileCount),
                y: Math.floor(Math.random() * this.tileCount)
            };
        } while (this.snake.some(segment => segment.x === newFood.x && segment.y === newFood.y));
        
        this.food = newFood;
    }
    
    draw() {
        // Clear canvas with gradient
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid
        this.drawGrid();
        
        // Draw food
        this.drawFood();
        
        // Draw snake
        this.drawSnake();
    }
    
    drawGrid() {
        this.ctx.strokeStyle = 'rgba(0, 255, 136, 0.1)';
        this.ctx.lineWidth = 0.5;
        
        for (let i = 0; i <= this.tileCount; i++) {
            // Vertical lines
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.gridSize, 0);
            this.ctx.lineTo(i * this.gridSize, this.canvas.height);
            this.ctx.stroke();
            
            // Horizontal lines
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * this.gridSize);
            this.ctx.lineTo(this.canvas.width, i * this.gridSize);
            this.ctx.stroke();
        }
    }
    
    drawFood() {
        const x = this.food.x * this.gridSize;
        const y = this.food.y * this.gridSize;
        
        // Outer glow
        this.ctx.shadowColor = '#ff6b6b';
        this.ctx.shadowBlur = 15;
        
        // Food gradient
        const gradient = this.ctx.createRadialGradient(
            x + this.gridSize / 2, y + this.gridSize / 2, 0,
            x + this.gridSize / 2, y + this.gridSize / 2, this.gridSize / 2
        );
        gradient.addColorStop(0, '#ff8a8a');
        gradient.addColorStop(1, '#ff4757');
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(x + 2, y + 2, this.gridSize - 4, this.gridSize - 4);
        
        this.ctx.shadowBlur = 0;
    }
    
    drawSnake() {
        this.snake.forEach((segment, index) => {
            const x = segment.x * this.gridSize;
            const y = segment.y * this.gridSize;
            
            if (index === 0) {
                // Snake head with glow
                this.ctx.shadowColor = '#00ff88';
                this.ctx.shadowBlur = 10;
                
                const gradient = this.ctx.createRadialGradient(
                    x + this.gridSize / 2, y + this.gridSize / 2, 0,
                    x + this.gridSize / 2, y + this.gridSize / 2, this.gridSize / 2
                );
                gradient.addColorStop(0, '#00ff88');
                gradient.addColorStop(1, '#00cc6a');
                
                this.ctx.fillStyle = gradient;
                this.ctx.fillRect(x + 1, y + 1, this.gridSize - 2, this.gridSize - 2);
                
                // Eyes
                this.ctx.shadowBlur = 0;
                this.ctx.fillStyle = '#000';
                const eyeSize = 3;
                this.ctx.fillRect(x + 4, y + 4, eyeSize, eyeSize);
                this.ctx.fillRect(x + this.gridSize - 7, y + 4, eyeSize, eyeSize);
            } else {
                // Snake body
                const alpha = Math.max(0.6, 1 - (index * 0.05));
                this.ctx.fillStyle = `rgba(0, 255, 136, ${alpha})`;
                this.ctx.fillRect(x + 2, y + 2, this.gridSize - 4, this.gridSize - 4);
            }
        });
        
        this.ctx.shadowBlur = 0;
    }
    
    createParticleEffect(x, y) {
        const particleCount = 8;
        const canvasRect = this.canvas.getBoundingClientRect();
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = (canvasRect.left + x * this.gridSize + this.gridSize / 2) + 'px';
            particle.style.top = (canvasRect.top + y * this.gridSize + this.gridSize / 2) + 'px';
            
            const angle = (i / particleCount) * Math.PI * 2;
            const velocity = 20;
            const vx = Math.cos(angle) * velocity;
            const vy = Math.sin(angle) * velocity;
            
            particle.style.setProperty('--vx', vx + 'px');
            particle.style.setProperty('--vy', vy + 'px');
            
            document.body.appendChild(particle);
            
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 1000);
        }
    }
    
    gameOver() {
        this.gameRunning = false;
        this.gameStarted = false;
        this.playGameOverSound();
        
        // Add shake effect
        this.canvas.classList.add('shake');
        setTimeout(() => {
            this.canvas.classList.remove('shake');
        }, 500);
        
        if (this.score > this.highScore) {
            this.highScore = this.score;
            localStorage.setItem('snakeHighScore', this.highScore);
            this.updateHighScore();
        }
        
        this.showGameOverOverlay();
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
    
    updateScore() {
        this.currentScoreElement.textContent = this.score;
        this.finalScoreElement.textContent = this.score;
    }
    
    updateHighScore() {
        this.highScoreElement.textContent = this.highScore;
    }
    
    updateStats() {
        this.snakeLengthElement.textContent = this.snake.length;
        this.gameSpeedElement.textContent = this.level;
        this.gameLevelElement.textContent = this.level;
    }
    
    showStartScreen() {
        this.startScreen.classList.remove('hidden');
    }
    
    hideStartScreen() {
        this.startScreen.classList.add('hidden');
    }
    
    showGameOverOverlay() {
        this.overlayTitle.textContent = 'GAME OVER';
        this.overlayMessage.textContent = 'Press SPACE to restart';
        this.gameOverlay.classList.remove('hidden');
    }
    
    showPauseOverlay() {
        this.overlayTitle.textContent = 'PAUSED';
        this.overlayMessage.textContent = 'Press SPACE to resume';
        this.gameOverlay.classList.remove('hidden');
    }
    
    hideGameOverlay() {
        this.gameOverlay.classList.add('hidden');
    }
    
    playEatSound() {
        // Create eat sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(1200, audioContext.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
            console.log('Audio not supported');
        }
    }
    
    playGameOverSound() {
        // Create game over sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(200, audioContext.currentTime + 0.5);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            console.log('Audio not supported');
        }
    }
    
    playMoveSound() {
        // Subtle move sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(150, audioContext.currentTime);
            oscillator.type = 'square';
            
            gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.05);
        } catch (e) {
            console.log('Audio not supported');
        }
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SnakeGame();
});

// Add CSS for particle animation
const particleStyle = document.createElement('style');
particleStyle.textContent = `
    .particle {
        animation: particle-move 1s ease-out forwards;
    }
    
    @keyframes particle-move {
        0% {
            opacity: 1;
            transform: translate(0, 0) scale(1);
        }
        100% {
            opacity: 0;
            transform: translate(var(--vx, 0), var(--vy, 0)) scale(0);
        }
    }
`;
document.head.appendChild(particleStyle);