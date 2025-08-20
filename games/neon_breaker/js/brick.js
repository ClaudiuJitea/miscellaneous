/**
 * Brick class for destructible game elements
 */

class Brick {
    constructor(x, y, type = 'normal', hitPoints = 1) {
        this.x = x;
        this.y = y;
        this.width = 80;
        this.height = 30;
        this.type = type;
        this.maxHitPoints = hitPoints;
        this.hitPoints = hitPoints;
        this.destroyed = false;
        this.powerUpChance = 0.15;
        
        // Visual properties
        this.glowIntensity = 0;
        this.glowDirection = 1;
        this.crackLevel = 0;
        this.shakeOffset = { x: 0, y: 0 };
        this.shakeIntensity = 0;
        
        // Get brick properties based on type
        this.properties = this.getBrickProperties(type, hitPoints);
    }

    getBrickProperties(type, hitPoints) {
        const brickTypes = {
            'normal': {
                colors: ['#00ffff', '#0099cc', '#006699'],
                score: 10,
                glowColor: '#00ffff',
                special: false
            },
            'strong': {
                colors: ['#ff6b6b', '#cc5555', '#994444'],
                score: 25,
                glowColor: '#ff6b6b',
                special: false
            },
            'metal': {
                colors: ['#c0c0c0', '#999999', '#666666'],
                score: 50,
                glowColor: '#ffffff',
                special: false
            },
            'explosive': {
                colors: ['#ffff00', '#ffcc00', '#ff9900'],
                score: 30,
                glowColor: '#ffff00',
                special: true,
                explosionRadius: 80
            },
            'regenerating': {
                colors: ['#00ff00', '#00cc00', '#009900'],
                score: 40,
                glowColor: '#00ff00',
                special: true,
                regenerateTime: 5000
            },
            'moving': {
                colors: ['#ff00ff', '#cc00cc', '#990099'],
                score: 35,
                glowColor: '#ff00ff',
                special: true,
                moveSpeed: 1,
                moveDirection: 1
            },
            'unbreakable': {
                colors: ['#444444', '#333333', '#222222'],
                score: 0,
                glowColor: '#666666',
                special: true
            }
        };
        
        const props = brickTypes[type] || brickTypes['normal'];
        
        // Adjust color based on hit points
        const colorIndex = Math.min(hitPoints - 1, props.colors.length - 1);
        props.currentColor = props.colors[colorIndex];
        
        return props;
    }

    update() {
        // Update glow effect
        this.glowIntensity += this.glowDirection * 0.02;
        if (this.glowIntensity >= 1) {
            this.glowIntensity = 1;
            this.glowDirection = -1;
        } else if (this.glowIntensity <= 0) {
            this.glowIntensity = 0;
            this.glowDirection = 1;
        }
        
        // Update shake effect
        if (this.shakeIntensity > 0) {
            this.shakeOffset.x = Utils.random(-this.shakeIntensity, this.shakeIntensity);
            this.shakeOffset.y = Utils.random(-this.shakeIntensity, this.shakeIntensity);
            this.shakeIntensity *= 0.9;
            
            if (this.shakeIntensity < 0.1) {
                this.shakeIntensity = 0;
                this.shakeOffset = { x: 0, y: 0 };
            }
        }
        
        // Special brick behaviors
        if (this.type === 'moving' && !this.destroyed) {
            this.x += this.properties.moveSpeed * this.properties.moveDirection;
            
            // Bounce off edges (assuming canvas width of 800)
            if (this.x <= 0 || this.x + this.width >= 800) {
                this.properties.moveDirection *= -1;
            }
        }
        
        // Regenerating brick
        if (this.type === 'regenerating' && this.destroyed && this.regenerateTimer) {
            this.regenerateTimer -= 16; // 60 FPS
            if (this.regenerateTimer <= 0) {
                this.regenerate();
            }
        }
    }

    draw(ctx) {
        if (this.destroyed && this.type !== 'regenerating') return;
        
        ctx.save();
        
        const drawX = this.x + this.shakeOffset.x;
        const drawY = this.y + this.shakeOffset.y;
        
        // Glow effect
        if (this.properties.special) {
            const glowSize = 3 + this.glowIntensity * 8;
            ctx.shadowColor = this.properties.glowColor;
            ctx.shadowBlur = glowSize;
        }
        
        // Regenerating brick transparency
        if (this.destroyed && this.type === 'regenerating') {
            const progress = 1 - (this.regenerateTimer / this.properties.regenerateTime);
            ctx.globalAlpha = progress * 0.7;
        }
        
        // Main brick body
        const gradient = ctx.createLinearGradient(drawX, drawY, drawX, drawY + this.height);
        gradient.addColorStop(0, this.properties.currentColor);
        gradient.addColorStop(0.5, this.lightenColor(this.properties.currentColor, 20));
        gradient.addColorStop(1, this.darkenColor(this.properties.currentColor, 30));
        
        ctx.fillStyle = gradient;
        ctx.fillRect(drawX, drawY, this.width, this.height);
        
        // Border
        ctx.strokeStyle = this.lightenColor(this.properties.currentColor, 40);
        ctx.lineWidth = 2;
        ctx.strokeRect(drawX, drawY, this.width, this.height);
        
        // Crack effects based on damage
        if (this.hitPoints < this.maxHitPoints && this.hitPoints > 0) {
            this.drawCracks(ctx, drawX, drawY);
        }
        
        // Special brick indicators
        this.drawSpecialIndicators(ctx, drawX, drawY);
        
        // Hit points indicator for strong bricks
        if (this.maxHitPoints > 1 && this.hitPoints > 0) {
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px Orbitron';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(
                this.hitPoints.toString(),
                drawX + this.width / 2,
                drawY + this.height / 2
            );
        }
        
        ctx.restore();
    }

    drawCracks(ctx, x, y) {
        const crackIntensity = 1 - (this.hitPoints / this.maxHitPoints);
        const numCracks = Math.floor(crackIntensity * 4) + 1;
        
        ctx.strokeStyle = this.darkenColor(this.properties.currentColor, 60);
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.8;
        
        for (let i = 0; i < numCracks; i++) {
            ctx.beginPath();
            const startX = x + Utils.random(5, this.width - 5);
            const startY = y + Utils.random(2, this.height - 2);
            const endX = startX + Utils.random(-15, 15);
            const endY = startY + Utils.random(-8, 8);
            
            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
            ctx.stroke();
        }
    }

    drawSpecialIndicators(ctx, x, y) {
        let symbol = '';
        let symbolColor = '#ffffff';
        
        switch (this.type) {
            case 'explosive':
                symbol = '💥';
                break;
            case 'regenerating':
                symbol = '♻';
                symbolColor = '#00ff00';
                break;
            case 'moving':
                symbol = '↔';
                symbolColor = '#ff00ff';
                break;
            case 'unbreakable':
                symbol = '🛡';
                symbolColor = '#666666';
                break;
        }
        
        if (symbol) {
            ctx.fillStyle = symbolColor;
            ctx.font = '12px Arial';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'top';
            ctx.fillText(symbol, x + this.width - 3, y + 2);
        }
    }

    // Hit the brick
    hit(damage = 1) {
        if (this.type === 'unbreakable') {
            return { destroyed: false, score: 0, special: false };
        }
        
        this.hitPoints -= damage;
        this.shakeIntensity = 3;
        
        // Update color based on remaining hit points
        if (this.hitPoints > 0) {
            const colorIndex = Math.min(this.hitPoints - 1, this.properties.colors.length - 1);
            this.properties.currentColor = this.properties.colors[colorIndex];
        }
        
        if (this.hitPoints <= 0) {
            return this.destroy();
        }
        
        return { destroyed: false, score: 0, special: false };
    }

    // Destroy the brick
    destroy() {
        this.destroyed = true;
        
        // Create destruction particles
        window.particleSystem?.createBrickDestruction(
            this.x, this.y, this.width, this.height, 
            this.properties.currentColor
        );
        
        // Handle special brick effects
        let specialEffect = false;
        if (this.type === 'explosive') {
            specialEffect = { type: 'explosion', radius: this.properties.explosionRadius };
        } else if (this.type === 'regenerating') {
            this.regenerateTimer = this.properties.regenerateTime;
            specialEffect = { type: 'regenerate' };
        }
        
        return {
            destroyed: true,
            score: this.properties.score,
            special: specialEffect
        };
    }

    // Regenerate the brick
    regenerate() {
        this.destroyed = false;
        this.hitPoints = this.maxHitPoints;
        this.properties.currentColor = this.properties.colors[this.maxHitPoints - 1];
        this.regenerateTimer = null;
        
        // Create regeneration effect
        window.particleSystem?.createPowerUpEffect(
            this.x + this.width/2, 
            this.y + this.height/2, 
            this.properties.glowColor
        );
    }

    // Check collision with ball
    checkCollision(ball) {
        if (this.destroyed && this.type !== 'regenerating') return false;
        
        return Utils.circleRectIntersect(
            { x: ball.x, y: ball.y, radius: ball.radius },
            { x: this.x, y: this.y, width: this.width, height: this.height }
        );
    }

    // Get collision side
    getCollisionSide(ball) {
        return Utils.getCollisionSide(ball, {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height
        });
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

    // Get brick bounds for collision
    getBounds() {
        return {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height
        };
    }

    // Check if brick is in explosion radius
    isInExplosionRadius(explosionX, explosionY, radius) {
        const centerX = this.x + this.width / 2;
        const centerY = this.y + this.height / 2;
        const distance = Utils.distance(centerX, centerY, explosionX, explosionY);
        return distance <= radius;
    }
}