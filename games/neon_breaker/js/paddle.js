/**
 * Paddle class with controls and special abilities
 */

class Paddle {
    constructor(x, y, width = 150, height = 22) {
        this.x = x;
        this.y = y;
        this.defaultWidth = width;
        this.width = width;
        this.height = height;
        this.speed = 8;
        
        // Visual properties
        this.glowIntensity = 0;
        this.glowDirection = 1;
        this.color = '#00ffff';
        this.glowColor = '#00ffff';
        
        // Laser system
        this.lasers = [];
        this.laserCooldown = 0;
        this.laserSpeed = 10;
        
        // Power-up effects
        this.sizeMultiplier = 1;
        this.hasLaser = false;
        this.isSticky = false;
    }

    update(canvasWidth, powerUpManager) {
        // Update glow effect
        this.updateGlow();
        
        // Apply power-up effects
        this.applyPowerUpEffects(powerUpManager);
        
        // Update lasers
        this.updateLasers();
        
        // Keep paddle within canvas bounds
        this.x = Utils.clamp(this.x, 0, canvasWidth - this.width);
    }

    updateGlow() {
        this.glowIntensity += this.glowDirection * 0.03;
        if (this.glowIntensity >= 1) {
            this.glowIntensity = 1;
            this.glowDirection = -1;
        } else if (this.glowIntensity <= 0) {
            this.glowIntensity = 0;
            this.glowDirection = 1;
        }
    }

    applyPowerUpEffects(powerUpManager) {
        // Size modification
        this.sizeMultiplier = powerUpManager.getEffectValue('paddle_size', 1);
        this.width = this.defaultWidth * this.sizeMultiplier;
        
        // Laser ability
        this.hasLaser = powerUpManager.hasEffect('laser');
        
        // Sticky paddle
        this.isSticky = powerUpManager.hasEffect('sticky_paddle');
        
        // Update colors based on active effects
        this.updateColors(powerUpManager);
    }

    updateColors(powerUpManager) {
        if (this.hasLaser) {
            this.color = '#ff6600';
            this.glowColor = '#ff6600';
        } else if (this.isSticky) {
            this.color = '#8a2be2';
            this.glowColor = '#8a2be2';
        } else if (this.sizeMultiplier > 1) {
            this.color = '#00ff00';
            this.glowColor = '#00ff00';
        } else if (this.sizeMultiplier < 1) {
            this.color = '#ff4444';
            this.glowColor = '#ff4444';
        } else {
            this.color = '#00ffff';
            this.glowColor = '#00ffff';
        }
    }

    updateLasers() {
        // Update laser cooldown
        if (this.laserCooldown > 0) {
            this.laserCooldown--;
        }
        
        // Update laser positions
        this.lasers = this.lasers.filter(laser => {
            laser.y -= this.laserSpeed;
            return laser.y > -laser.height;
        });
    }

    // Move paddle
    move(direction, canvasWidth) {
        const moveDistance = this.speed * direction;
        this.x += moveDistance;
        this.x = Utils.clamp(this.x, 0, canvasWidth - this.width);
    }

    // Set paddle position (for mouse control)
    setPosition(x, canvasWidth) {
        this.x = Utils.clamp(x - this.width / 2, 0, canvasWidth - this.width);
    }

    // Fire laser
    fireLaser() {
        if (!this.hasLaser || this.laserCooldown > 0) {
            return false;
        }
        
        // Create two lasers from paddle edges
        const laserWidth = 4;
        const laserHeight = 15;
        
        this.lasers.push({
            x: this.x + 10,
            y: this.y,
            width: laserWidth,
            height: laserHeight
        });
        
        this.lasers.push({
            x: this.x + this.width - 10 - laserWidth,
            y: this.y,
            width: laserWidth,
            height: laserHeight
        });
        
        this.laserCooldown = 15; // Cooldown frames
        Utils.playSound('paddleHitSound', 0.3);
        
        return true;
    }

    // Check laser collisions with bricks
    checkLaserCollisions(bricks) {
        const hitBricks = [];
        
        this.lasers = this.lasers.filter(laser => {
            let laserHit = false;
            
            for (const brick of bricks) {
                if (brick.destroyed) continue;
                
                if (Utils.rectIntersect(laser, brick.getBounds())) {
                    hitBricks.push(brick);
                    laserHit = true;
                    
                    // Create laser hit effect
                    window.particleSystem?.createSparks(
                        laser.x + laser.width / 2,
                        laser.y,
                        6,
                        '#ff6600'
                    );
                    
                    break;
                }
            }
            
            return !laserHit;
        });
        
        return hitBricks;
    }

    draw(ctx) {
        ctx.save();
        
        // Glow effect
        const glowSize = 5 + this.glowIntensity * 8;
        ctx.shadowColor = this.glowColor;
        ctx.shadowBlur = glowSize;
        
        // Main paddle body
        const gradient = ctx.createLinearGradient(this.x, this.y, this.x, this.y + this.height);
        gradient.addColorStop(0, this.lightenColor(this.color, 30));
        gradient.addColorStop(0.5, this.color);
        gradient.addColorStop(1, this.darkenColor(this.color, 20));
        
        ctx.fillStyle = gradient;
        ctx.fillRect(this.x, this.y, this.width, this.height);
        
        // Paddle border
        ctx.strokeStyle = this.lightenColor(this.color, 50);
        ctx.lineWidth = 2;
        ctx.strokeRect(this.x, this.y, this.width, this.height);
        
        // Special effects indicators
        this.drawSpecialEffects(ctx);
        
        // Draw lasers
        this.drawLasers(ctx);
        
        ctx.restore();
    }

    drawSpecialEffects(ctx) {
        // Sticky paddle effect
        if (this.isSticky) {
            ctx.strokeStyle = '#8a2be2';
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            
            for (let i = 0; i < 3; i++) {
                const offset = i * 2;
                ctx.strokeRect(
                    this.x - offset, 
                    this.y - offset, 
                    this.width + offset * 2, 
                    this.height + offset * 2
                );
            }
            
            ctx.setLineDash([]);
        }
        
        // Laser paddle indicators
        if (this.hasLaser) {
            const indicatorSize = 6;
            const leftX = this.x + 10 - indicatorSize / 2;
            const rightX = this.x + this.width - 10 - indicatorSize / 2;
            const indicatorY = this.y - indicatorSize - 2;
            
            ctx.fillStyle = '#ff6600';
            ctx.fillRect(leftX, indicatorY, indicatorSize, indicatorSize);
            ctx.fillRect(rightX, indicatorY, indicatorSize, indicatorSize);
            
            // Laser charging effect
            if (this.laserCooldown === 0) {
                ctx.shadowColor = '#ff6600';
                ctx.shadowBlur = 8;
                ctx.fillStyle = '#ffaa00';
                ctx.fillRect(leftX - 1, indicatorY - 1, indicatorSize + 2, indicatorSize + 2);
                ctx.fillRect(rightX - 1, indicatorY - 1, indicatorSize + 2, indicatorSize + 2);
            }
        }
        
        // Size modification indicators
        if (this.sizeMultiplier !== 1) {
            const centerX = this.x + this.width / 2;
            const centerY = this.y + this.height / 2;
            
            ctx.font = 'bold 10px Orbitron';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#ffffff';
            
            if (this.sizeMultiplier > 1) {
                ctx.fillText('↔', centerX, centerY);
            } else {
                ctx.fillText('→←', centerX, centerY);
            }
        }
    }

    drawLasers(ctx) {
        if (this.lasers.length === 0) return;
        
        ctx.shadowColor = '#ff6600';
        ctx.shadowBlur = 8;
        
        this.lasers.forEach(laser => {
            // Laser beam gradient
            const gradient = ctx.createLinearGradient(
                laser.x, laser.y, 
                laser.x, laser.y + laser.height
            );
            gradient.addColorStop(0, '#ffaa00');
            gradient.addColorStop(0.5, '#ff6600');
            gradient.addColorStop(1, '#cc3300');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(laser.x, laser.y, laser.width, laser.height);
            
            // Laser core
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(
                laser.x + laser.width / 4, 
                laser.y, 
                laser.width / 2, 
                laser.height
            );
        });
    }

    // Get paddle bounds for collision detection
    getBounds() {
        return {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height
        };
    }

    // Get paddle center position
    getCenterX() {
        return this.x + this.width / 2;
    }

    // Reset paddle to default state
    reset(x, y) {
        this.x = x;
        this.y = y;
        this.width = this.defaultWidth;
        this.sizeMultiplier = 1;
        this.hasLaser = false;
        this.isSticky = false;
        this.lasers = [];
        this.laserCooldown = 0;
        this.color = '#00ffff';
        this.glowColor = '#00ffff';
    }

    // Color utility functions
    lightenColor(color, percent) {
        const rgb = Utils.hexToRgb(color);
        if (!rgb) return color;
        
        const factor = 1 + percent / 100;
        return `rgb(${Math.min(255, rgb.r * factor)}, ${Math.min(255, rgb.g * factor)}, ${Math.min(255, rgb.b * factor)})`;
    }

    darkenColor(color, percent) {
        const rgb = Utils.hexToRgb(color);
        if (!rgb) return color;
        
        const factor = 1 - percent / 100;
        return `rgb(${rgb.r * factor}, ${rgb.g * factor}, ${rgb.b * factor})`;
    }
}

// Input handler for paddle control
class PaddleController {
    constructor(paddle, canvasWidth) {
        this.paddle = paddle;
        this.canvasWidth = canvasWidth;
        this.keys = {};
        this.mouseX = 0;
        this.touchX = 0;
        this.useMouseControl = false;
        this.useTouchControl = false;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
            
            // Space for laser
            if (e.code === 'Space') {
                e.preventDefault();
                this.paddle.fireLaser();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
        });
        
        // Mouse events
        const canvas = document.getElementById('gameCanvas');
        
        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            this.mouseX = (e.clientX - rect.left) * scaleX;
            this.useMouseControl = true;
            this.useTouchControl = false;
        });
        
        canvas.addEventListener('click', (e) => {
            this.paddle.fireLaser();
        });
        
        // Touch events
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.handleTouch(e);
        });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.handleTouch(e);
        });
        
        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (e.touches.length === 0) {
                this.paddle.fireLaser();
            }
        });
    }

    handleTouch(e) {
        if (e.touches.length > 0) {
            const canvas = document.getElementById('gameCanvas');
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            this.touchX = (e.touches[0].clientX - rect.left) * scaleX;
            this.useTouchControl = true;
            this.useMouseControl = false;
        }
    }

    update() {
        // Mouse control (highest priority)
        if (this.useMouseControl) {
            this.paddle.setPosition(this.mouseX, this.canvasWidth);
            return;
        }
        
        // Touch control
        if (this.useTouchControl) {
            this.paddle.setPosition(this.touchX, this.canvasWidth);
            return;
        }
        
        // Keyboard control (fallback)
        let direction = 0;
        if (this.keys['ArrowLeft'] || this.keys['KeyA']) {
            direction -= 1;
        }
        if (this.keys['ArrowRight'] || this.keys['KeyD']) {
            direction += 1;
        }
        
        if (direction !== 0) {
            this.paddle.move(direction, this.canvasWidth);
            // Disable mouse control when using keyboard
            this.useMouseControl = false;
            this.useTouchControl = false;
        }
    }

    // Update canvas width for responsive design
    updateCanvasWidth(width) {
        this.canvasWidth = width;
    }
}