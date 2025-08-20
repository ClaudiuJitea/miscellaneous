/**
 * PowerUp class for special abilities and effects
 */

class PowerUp {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.width = 30;
        this.height = 15;
        this.type = type;
        this.speed = 2;
        this.collected = false;
        this.glowIntensity = 0;
        this.glowDirection = 1;
        
        // Power-up properties
        this.properties = this.getPowerUpProperties(type);
    }

    getPowerUpProperties(type) {
        const powerUps = {
            'enlarge': {
                color: '#00ff00',
                symbol: '▬',
                name: 'Enlarge Paddle',
                duration: 10000, // 10 seconds
                effect: 'paddle_size',
                value: 1.5
            },
            'shrink': {
                color: '#ff4444',
                symbol: '▪',
                name: 'Shrink Paddle',
                duration: 8000,
                effect: 'paddle_size',
                value: 0.7
            },
            'speed_up': {
                color: '#ffff00',
                symbol: '►',
                name: 'Speed Up',
                duration: 8000,
                effect: 'ball_speed',
                value: 1.3
            },
            'slow_down': {
                color: '#00ccff',
                symbol: '◄',
                name: 'Slow Down',
                duration: 10000,
                effect: 'ball_speed',
                value: 0.7
            },
            'multi_ball': {
                color: '#ff00ff',
                symbol: '●',
                name: 'Multi Ball',
                duration: 0, // Instant effect
                effect: 'multi_ball',
                value: 2
            },
            'laser': {
                color: '#ff6600',
                symbol: '↑',
                name: 'Laser Paddle',
                duration: 15000,
                effect: 'laser',
                value: true
            },
            'extra_life': {
                color: '#ff69b4',
                symbol: '♥',
                name: 'Extra Life',
                duration: 0,
                effect: 'extra_life',
                value: 1
            },
            'score_boost': {
                color: '#ffd700',
                symbol: '★',
                name: 'Score Boost',
                duration: 12000,
                effect: 'score_multiplier',
                value: 2
            },
            'sticky_paddle': {
                color: '#8a2be2',
                symbol: '═',
                name: 'Sticky Paddle',
                duration: 15000,
                effect: 'sticky_paddle',
                value: true
            },
            'penetrating_ball': {
                color: '#32cd32',
                symbol: '◆',
                name: 'Penetrating Ball',
                duration: 8000,
                effect: 'penetrating',
                value: true
            }
        };
        
        return powerUps[type] || powerUps['enlarge'];
    }

    update() {
        // Move down
        this.y += this.speed;
        
        // Update glow effect
        this.glowIntensity += this.glowDirection * 0.05;
        if (this.glowIntensity >= 1) {
            this.glowIntensity = 1;
            this.glowDirection = -1;
        } else if (this.glowIntensity <= 0) {
            this.glowIntensity = 0;
            this.glowDirection = 1;
        }
    }

    draw(ctx) {
        ctx.save();
        
        // Glow effect
        const glowSize = 5 + this.glowIntensity * 10;
        ctx.shadowColor = this.properties.color;
        ctx.shadowBlur = glowSize;
        
        // Background
        ctx.fillStyle = this.properties.color;
        ctx.globalAlpha = 0.3 + this.glowIntensity * 0.4;
        ctx.fillRect(this.x, this.y, this.width, this.height);
        
        // Border
        ctx.globalAlpha = 0.8 + this.glowIntensity * 0.2;
        ctx.strokeStyle = this.properties.color;
        ctx.lineWidth = 2;
        ctx.strokeRect(this.x, this.y, this.width, this.height);
        
        // Symbol
        ctx.globalAlpha = 1;
        ctx.fillStyle = this.properties.color;
        ctx.font = 'bold 16px Orbitron';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(
            this.properties.symbol,
            this.x + this.width / 2,
            this.y + this.height / 2
        );
        
        ctx.restore();
    }

    // Check collision with paddle
    checkCollision(paddle) {
        return Utils.rectIntersect(
            { x: this.x, y: this.y, width: this.width, height: this.height },
            { x: paddle.x, y: paddle.y, width: paddle.width, height: paddle.height }
        );
    }

    // Check if power-up is off screen
    isOffScreen(canvasHeight) {
        return this.y > canvasHeight;
    }

    // Get random power-up type
    static getRandomType() {
        const types = [
            'enlarge', 'shrink', 'speed_up', 'slow_down',
            'multi_ball', 'laser', 'extra_life', 'score_boost',
            'sticky_paddle', 'penetrating_ball'
        ];
        
        // Weighted selection (some power-ups are rarer)
        const weights = {
            'enlarge': 15,
            'shrink': 10,
            'speed_up': 12,
            'slow_down': 15,
            'multi_ball': 8,
            'laser': 10,
            'extra_life': 5,
            'score_boost': 12,
            'sticky_paddle': 8,
            'penetrating_ball': 5
        };
        
        const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
        let random = Math.random() * totalWeight;
        
        for (const type of types) {
            random -= weights[type];
            if (random <= 0) {
                return type;
            }
        }
        
        return types[0]; // Fallback
    }
}

// PowerUp Manager class
class PowerUpManager {
    constructor() {
        this.activePowerUps = [];
        this.fallingPowerUps = [];
        this.spawnChance = 0.15; // 15% chance per brick
    }

    // Spawn power-up from brick position
    spawnPowerUp(x, y) {
        if (Math.random() < this.spawnChance) {
            const type = PowerUp.getRandomType();
            const powerUp = new PowerUp(x, y, type);
            this.fallingPowerUps.push(powerUp);
            return true;
        }
        return false;
    }

    // Update all power-ups
    update(paddle, canvasHeight) {
        // Update falling power-ups
        this.fallingPowerUps = this.fallingPowerUps.filter(powerUp => {
            powerUp.update();
            
            // Check collision with paddle
            if (powerUp.checkCollision(paddle)) {
                this.collectPowerUp(powerUp);
                return false;
            }
            
            // Remove if off screen
            return !powerUp.isOffScreen(canvasHeight);
        });
        
        // Update active power-up durations
        this.activePowerUps = this.activePowerUps.filter(powerUp => {
            if (powerUp.duration > 0) {
                powerUp.duration -= 16; // Assuming 60 FPS (16ms per frame)
                return powerUp.duration > 0;
            }
            return false;
        });
    }

    // Collect power-up and apply effect
    collectPowerUp(powerUp) {
        Utils.playSound('powerUpSound', 0.6);
        
        // Create collection effect
        window.particleSystem?.createPowerUpEffect(powerUp.x + powerUp.width/2, powerUp.y + powerUp.height/2, powerUp.properties.color);
        
        // Apply power-up effect
        const effect = {
            type: powerUp.properties.effect,
            value: powerUp.properties.value,
            duration: powerUp.properties.duration,
            name: powerUp.properties.name,
            startTime: Date.now()
        };
        
        // Handle instant effects
        if (powerUp.properties.duration === 0) {
            this.applyInstantEffect(effect);
        } else {
            // Remove existing effect of same type
            this.activePowerUps = this.activePowerUps.filter(active => active.type !== effect.type);
            this.activePowerUps.push(effect);
        }
        
        // Show power-up notification
        this.showPowerUpNotification(powerUp.properties.name, powerUp.properties.color);
    }

    // Apply instant effects
    applyInstantEffect(effect) {
        switch (effect.type) {
            case 'multi_ball':
                // This will be handled by the game class
                window.game?.spawnMultiBalls(effect.value);
                break;
            case 'extra_life':
                window.game?.addLife();
                break;
        }
    }

    // Get active effect value
    getEffectValue(effectType, defaultValue = 1) {
        const effect = this.activePowerUps.find(powerUp => powerUp.type === effectType);
        return effect ? effect.value : defaultValue;
    }

    // Check if effect is active
    hasEffect(effectType) {
        return this.activePowerUps.some(powerUp => powerUp.type === effectType);
    }

    // Show power-up notification
    showPowerUpNotification(name, color) {
        // Remove existing notification
        const existing = document.querySelector('.powerup-indicator');
        if (existing) {
            existing.remove();
        }
        
        // Create new notification
        const notification = document.createElement('div');
        notification.className = 'powerup-indicator';
        notification.style.color = color;
        notification.style.borderColor = color;
        notification.style.boxShadow = `0 0 15px ${color}33`;
        notification.textContent = name;
        
        document.querySelector('.canvas-container').appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Draw falling power-ups
    draw(ctx) {
        this.fallingPowerUps.forEach(powerUp => powerUp.draw(ctx));
    }

    // Clear all power-ups
    clear() {
        this.fallingPowerUps = [];
        this.activePowerUps = [];
        
        // Remove notification
        const notification = document.querySelector('.powerup-indicator');
        if (notification) {
            notification.remove();
        }
    }

    // Get active power-ups for display
    getActivePowerUps() {
        return this.activePowerUps.map(powerUp => ({
            name: powerUp.name,
            timeLeft: Math.max(0, powerUp.duration)
        }));
    }
}