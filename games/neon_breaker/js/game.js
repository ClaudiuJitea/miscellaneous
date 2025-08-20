/**
 * Main Game class - controls game state, logic, and rendering
 */

class Game {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Game state
        this.state = 'start'; // start, playing, paused, gameOver, levelComplete
        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.combo = 0;
        this.maxCombo = 0;
        
        // Game objects
        this.paddle = null;
        this.balls = [];
        this.bricks = [];
        this.powerUpManager = new PowerUpManager();
        this.paddleController = null;
        
        // Level configuration
        this.levelConfig = null;
        this.bricksRemaining = 0;
        
        // Game timing
        this.lastTime = 0;
        this.deltaTime = 0;
        this.targetFPS = 60;
        this.frameTime = 1000 / this.targetFPS;
        
        // High scores
        this.highScores = Utils.loadFromStorage('highScores', []);
        
        // Initialize game
        this.init();
    }

    init() {
        // Setup canvas
        this.setupCanvas();
        
        // Create game objects
        this.paddle = new Paddle(
            this.canvas.width / 2 - 75,
            this.canvas.height - 60,
            150,
            22
        );
        
        this.paddleController = new PaddleController(this.paddle, this.canvas.width);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load level
        this.loadLevel(this.level);
        
        // Update UI
        this.updateUI();
        
        // Start game loop
        this.gameLoop();
    }

    setupCanvas() {
        // Make canvas responsive
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Set canvas properties for crisp rendering
        this.ctx.imageSmoothingEnabled = false;
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        const containerRect = container.getBoundingClientRect();
        
        // Maintain aspect ratio
        const aspectRatio = 4 / 3;
        let width = Math.min(1200, containerRect.width - 40);
        let height = width / aspectRatio;
        
        if (height > window.innerHeight * 0.7) {
            height = window.innerHeight * 0.7;
            width = height * aspectRatio;
        }
        
        this.canvas.style.width = width + 'px';
        this.canvas.style.height = height + 'px';
        
        // Update paddle controller
        if (this.paddleController) {
            this.paddleController.updateCanvasWidth(this.canvas.width);
        }
    }

    setupEventListeners() {
        // Game control keys
        document.addEventListener('keydown', (e) => {
            switch (e.code) {
                case 'Space':
                    e.preventDefault();
                    this.handleSpaceKey();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.togglePause();
                    break;
            }
        });
        
        // UI button events
        this.setupUIEvents();
    }

    setupUIEvents() {
        document.getElementById('startButton').addEventListener('click', () => this.startGame());
        document.getElementById('resumeButton').addEventListener('click', () => this.resumeGame());
        document.getElementById('restartButton').addEventListener('click', () => this.restartGame());
        document.getElementById('nextLevelButton').addEventListener('click', () => this.nextLevel());
        document.getElementById('mainMenuButton').addEventListener('click', () => this.showMainMenu());
        document.getElementById('menuButton').addEventListener('click', () => this.showMainMenu());
        document.getElementById('leaderboardButton').addEventListener('click', () => this.showLeaderboard());
        document.getElementById('backButton').addEventListener('click', () => this.showMainMenu());
    }

    // Game state management
    startGame() {
        this.state = 'playing';
        this.resetGame();
        this.hideAllOverlays();
        this.spawnBall();
    }

    resetGame() {
        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.combo = 0;
        this.maxCombo = 0;
        this.balls = [];
        this.powerUpManager.clear();
        
        // Reset paddle
        this.paddle.reset(
            this.canvas.width / 2 - 50,
            this.canvas.height - 40
        );
        
        // Load first level
        this.loadLevel(this.level);
        this.updateUI();
    }

    restartGame() {
        this.startGame();
    }

    togglePause() {
        if (this.state === 'playing') {
            this.state = 'paused';
            this.showOverlay('pauseScreen');
        } else if (this.state === 'paused') {
            this.resumeGame();
        }
    }

    resumeGame() {
        this.state = 'playing';
        this.hideAllOverlays();
    }

    gameOver() {
        this.state = 'gameOver';
        this.saveHighScore();
        this.updateFinalScore();
        this.showOverlay('gameOverScreen');
        Utils.playSound('gameOverSound', 0.7);
    }

    levelComplete() {
        this.state = 'levelComplete';
        const bonus = this.calculateLevelBonus();
        this.score += bonus;
        this.updateLevelBonus(bonus);
        this.showOverlay('levelCompleteScreen');
        
        // Create celebration effect
        window.particleSystem?.createLevelComplete(this.canvas.width, this.canvas.height);
    }

    nextLevel() {
        this.level++;
        this.loadLevel(this.level);
        this.spawnBall();
        this.state = 'playing';
        this.hideAllOverlays();
        this.updateUI();
    }

    // Level management
    loadLevel(levelNumber) {
        this.levelConfig = this.generateLevelConfig(levelNumber);
        this.createBricks();
        this.bricksRemaining = this.bricks.filter(brick => !brick.destroyed).length;
    }

    generateLevelConfig(level) {
        const configs = {
            1: {
                rows: 5,
                cols: 10,
                brickTypes: ['normal'],
                specialChance: 0.1,
                ballSpeed: 5
            },
            2: {
                rows: 6,
                cols: 10,
                brickTypes: ['normal', 'strong'],
                specialChance: 0.15,
                ballSpeed: 5.5
            },
            3: {
                rows: 6,
                cols: 11,
                brickTypes: ['normal', 'strong', 'explosive'],
                specialChance: 0.2,
                ballSpeed: 6
            },
            4: {
                rows: 7,
                cols: 11,
                brickTypes: ['normal', 'strong', 'explosive', 'moving'],
                specialChance: 0.25,
                ballSpeed: 6.5
            },
            5: {
                rows: 7,
                cols: 12,
                brickTypes: ['normal', 'strong', 'explosive', 'moving', 'regenerating'],
                specialChance: 0.3,
                ballSpeed: 7
            }
        };
        
        // For levels beyond 5, increase difficulty progressively
        if (level > 5) {
            const baseConfig = configs[5];
            return {
                rows: Math.min(8, baseConfig.rows + Math.floor((level - 5) / 3)),
                cols: Math.min(13, baseConfig.cols + Math.floor((level - 5) / 2)),
                brickTypes: [...baseConfig.brickTypes, 'metal'],
                specialChance: Math.min(0.4, baseConfig.specialChance + (level - 5) * 0.02),
                ballSpeed: Math.min(10, baseConfig.ballSpeed + (level - 5) * 0.2)
            };
        }
        
        return configs[level] || configs[1];
    }

    createBricks() {
        this.bricks = [];
        const config = this.levelConfig;
        const brickWidth = 80;
        const brickHeight = 30;
        const padding = 5;
        const offsetX = (this.canvas.width - (config.cols * (brickWidth + padding) - padding)) / 2;
        const offsetY = 60;
        
        for (let row = 0; row < config.rows; row++) {
            for (let col = 0; col < config.cols; col++) {
                const x = offsetX + col * (brickWidth + padding);
                const y = offsetY + row * (brickHeight + padding);
                
                // Determine brick type
                let brickType = 'normal';
                let hitPoints = 1;
                
                if (Math.random() < config.specialChance) {
                    brickType = config.brickTypes[Utils.randomInt(1, config.brickTypes.length - 1)];
                } else {
                    brickType = config.brickTypes[0];
                }
                
                // Set hit points based on type
                switch (brickType) {
                    case 'strong':
                        hitPoints = 2;
                        break;
                    case 'metal':
                        hitPoints = 3;
                        break;
                    case 'unbreakable':
                        hitPoints = Infinity;
                        break;
                    default:
                        hitPoints = 1;
                }
                
                this.bricks.push(new Brick(x, y, brickType, hitPoints));
            }
        }
    }

    // Ball management
    spawnBall() {
        const ball = new Ball(
            this.paddle.getCenterX(),
            this.paddle.y - 20,
            8
        );
        ball.speed = this.levelConfig.ballSpeed;
        ball.launch(); // Launch the ball with default upward angle
        this.balls = [ball];
    }

    spawnMultiBalls(count) {
        if (this.balls.length === 0) return;
        
        const originalBall = this.balls[0];
        for (let i = 0; i < count; i++) {
            const newBall = originalBall.clone();
            this.balls.push(newBall);
        }
    }

    addLife() {
        this.lives = Math.min(5, this.lives + 1);
        this.updateUI();
    }

    // Game loop
    gameLoop(currentTime = 0) {
        // Calculate delta time
        this.deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;
        
        // Update FPS counter
        Utils.fps.update();
        
        // Update game
        if (this.state === 'playing') {
            this.update();
        }
        
        // Render
        this.render();
        
        // Continue loop
        requestAnimationFrame((time) => this.gameLoop(time));
    }

    update() {
        // Update paddle
        this.paddleController.update();
        this.paddle.update(this.canvas.width, this.powerUpManager);
        
        // Update balls
        this.updateBalls();
        
        // Update bricks
        this.updateBricks();
        
        // Update power-ups
        this.powerUpManager.update(this.paddle, this.canvas.height);
        
        // Update particles
        window.particleSystem?.update();
        
        // Check win condition
        this.checkWinCondition();
    }

    updateBalls() {
        this.balls = this.balls.filter(ball => {
            // Update ball
            ball.update(this.canvas.width, this.canvas.height, this.powerUpManager);
            
            // Update stuck ball position
            if (ball.stuck) {
                ball.updateStuckPosition(this.paddle);
            }
            
            // Handle collisions
            this.handleBallCollisions(ball);
            
            // Check if ball is lost
            if (ball.isBelowPaddle(this.paddle.y)) {
                return false; // Remove ball
            }
            
            return true; // Keep ball
        });
        
        // Check if all balls are lost
        if (this.balls.length === 0) {
            this.loseLife();
        }
    }

    updateBricks() {
        this.bricks.forEach(brick => {
            if (!brick.destroyed || brick.type === 'regenerating') {
                brick.update();
            }
        });
    }

    handleBallCollisions(ball) {
        // Paddle collision
        if (ball.handlePaddleCollision(this.paddle, this.powerUpManager)) {
            this.combo = 0; // Reset combo on paddle hit
        }
        
        // Brick collisions
        this.handleBrickCollisions(ball);
        
        // Laser collisions
        const laserHitBricks = this.paddle.checkLaserCollisions(this.bricks);
        laserHitBricks.forEach(brick => {
            const result = brick.hit();
            if (result.destroyed) {
                this.handleBrickDestruction(result, brick);
            }
        });
    }

    handleBrickCollisions(ball) {
        for (const brick of this.bricks) {
            if (brick.destroyed && brick.type !== 'regenerating') continue;
            
            const result = ball.handleBrickCollision(brick);
            if (result) {
                this.handleBrickDestruction(result, brick);
                
                // Break if not penetrating
                if (!ball.penetrating) {
                    break;
                }
            }
        }
    }

    handleBrickDestruction(result, brick) {
        if (!result.destroyed) return;
        
        // Update score and combo
        this.combo++;
        this.maxCombo = Math.max(this.maxCombo, this.combo);
        
        const comboMultiplier = Math.min(5, 1 + Math.floor(this.combo / 3));
        const scoreMultiplier = this.powerUpManager.getEffectValue('score_multiplier', 1);
        const points = result.score * comboMultiplier * scoreMultiplier;
        
        this.score += points;
        this.bricksRemaining--;
        
        // Handle special brick effects
        if (result.special) {
            this.handleSpecialBrickEffect(result.special, brick);
        }
        
        // Spawn power-up
        this.powerUpManager.spawnPowerUp(brick.x + brick.width/2, brick.y + brick.height/2);
        
        // Screen shake for high combos
        if (this.combo >= 5) {
            Utils.screenShake(200);
        }
        
        this.updateUI();
    }

    handleSpecialBrickEffect(effect, brick) {
        switch (effect.type) {
            case 'explosion':
                this.handleExplosion(brick.x + brick.width/2, brick.y + brick.height/2, effect.radius);
                break;
            case 'regenerate':
                // Brick will regenerate automatically
                this.bricksRemaining++; // Don't count as destroyed yet
                break;
        }
    }

    handleExplosion(x, y, radius) {
        // Create explosion effect
        window.particleSystem?.createExplosion(x, y, 20, '#ffff00', 2);
        Utils.screenShake(300);
        
        // Damage nearby bricks
        this.bricks.forEach(brick => {
            if (!brick.destroyed && brick.isInExplosionRadius(x, y, radius)) {
                const result = brick.hit(2); // Explosion does 2 damage
                if (result.destroyed) {
                    this.handleBrickDestruction(result, brick);
                }
            }
        });
    }

    loseLife() {
        this.lives--;
        this.combo = 0;
        
        if (this.lives <= 0) {
            this.gameOver();
        } else {
            this.spawnBall();
            this.powerUpManager.clear(); // Clear power-ups on life loss
        }
        
        this.updateUI();
    }

    checkWinCondition() {
        const activeBricks = this.bricks.filter(brick => 
            !brick.destroyed && brick.type !== 'unbreakable'
        ).length;
        
        if (activeBricks === 0) {
            this.levelComplete();
        }
    }

    handleSpaceKey() {
        if (this.state === 'playing') {
            // Launch stuck balls or pause
            const stuckBalls = this.balls.filter(ball => ball.stuck);
            if (stuckBalls.length > 0) {
                stuckBalls.forEach(ball => {
                    const angle = -Math.PI/2 + Utils.random(-0.3, 0.3);
                    ball.launch(angle);
                });
            } else {
                this.togglePause();
            }
        }
    }

    // Rendering
    render() {
        // Clear canvas
        this.ctx.fillStyle = 'rgba(0, 8, 20, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.state === 'playing' || this.state === 'paused') {
            // Draw game objects
            this.renderGameObjects();
        }
        
        // Draw particles
        window.particleSystem?.draw(this.ctx);
        
        // Draw FPS (debug)
        if (window.DEBUG) {
            this.drawFPS();
        }
    }

    renderGameObjects() {
        // Draw bricks
        this.bricks.forEach(brick => brick.draw(this.ctx));
        
        // Draw paddle
        this.paddle.draw(this.ctx);
        
        // Draw balls
        this.balls.forEach(ball => ball.draw(this.ctx));
        
        // Draw power-ups
        this.powerUpManager.draw(this.ctx);
    }

    drawFPS() {
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '12px monospace';
        this.ctx.fillText(`FPS: ${Utils.fps.current}`, 10, 20);
        this.ctx.fillText(`Particles: ${window.particleSystem?.getCount() || 0}`, 10, 35);
    }

    // UI Management
    updateUI() {
        document.getElementById('score').textContent = Utils.formatScore(this.score);
        document.getElementById('level').textContent = this.level;
        document.getElementById('highScore').textContent = Utils.formatScore(this.getHighScore());
        
        // Update lives display
        const livesContainer = document.getElementById('lives');
        const lifeElements = livesContainer.querySelectorAll('.life');
        lifeElements.forEach((life, index) => {
            life.classList.toggle('active', index < this.lives);
        });
    }

    updateFinalScore() {
        document.getElementById('finalScore').textContent = Utils.formatScore(this.score);
    }

    updateLevelBonus(bonus) {
        document.getElementById('levelBonus').textContent = Utils.formatScore(bonus);
    }

    calculateLevelBonus() {
        return this.level * 100 + this.maxCombo * 50;
    }

    // High Score Management
    getHighScore() {
        return this.highScores.length > 0 ? this.highScores[0].score : 0;
    }

    saveHighScore() {
        const newScore = {
            score: this.score,
            level: this.level,
            date: new Date().toLocaleDateString()
        };
        
        this.highScores.push(newScore);
        this.highScores.sort((a, b) => b.score - a.score);
        this.highScores = this.highScores.slice(0, 10); // Keep top 10
        
        Utils.saveToStorage('highScores', this.highScores);
    }

    showLeaderboard() {
        const list = document.getElementById('leaderboardList');
        list.innerHTML = '';
        
        if (this.highScores.length === 0) {
            list.innerHTML = '<div class="leaderboard-entry"><span>No scores yet</span><span>-</span></div>';
        } else {
            this.highScores.forEach((score, index) => {
                const entry = document.createElement('div');
                entry.className = 'leaderboard-entry';
                entry.innerHTML = `
                    <span>#${index + 1} - Level ${score.level}</span>
                    <span>${Utils.formatScore(score.score)}</span>
                `;
                list.appendChild(entry);
            });
        }
        
        this.showOverlay('leaderboardScreen');
    }

    // Overlay Management
    showOverlay(overlayId) {
        this.hideAllOverlays();
        document.getElementById(overlayId).classList.remove('hidden');
    }

    hideAllOverlays() {
        const overlays = document.querySelectorAll('.game-overlay');
        overlays.forEach(overlay => overlay.classList.add('hidden'));
    }

    showMainMenu() {
        this.state = 'start';
        this.showOverlay('startScreen');
    }
}

// Make game instance globally available
window.game = null;