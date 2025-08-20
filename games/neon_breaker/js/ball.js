/**
 * Ball class with physics and collision detection
 */

class Ball {
    constructor(x, y, radius = 12) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.vx = 0;
        this.vy = 0;
        this.speed = 5;
        this.maxSpeed = 12;
        this.minSpeed = 3;
        
        // Visual properties
        this.trail = [];
        this.maxTrailLength = 8;
        this.glowIntensity = 0;
        this.glowDirection = 1;
        
        // Game state
        this.launched = false;
        this.stuck = false;
        this.stuckOffset = 0;
        
        // Special abilities
        this.penetrating = false;
        this.penetratingTimer = 0;
        
        // Color and effects
        this.color = '#ffffff';
        this.glowColor = '#00ffff';
    }

    // Launch the ball
    launch(angle = -Math.PI/2, speed = null) {
        this.launched = true;
        this.stuck = false;
        
        const launchSpeed = speed || this.speed;
        this.vx = Math.cos(angle) * launchSpeed;
        this.vy = Math.sin(angle) * launchSpeed;
    }

    // Update ball position and effects
    update(canvasWidth, canvasHeight, powerUpManager) {
        if (!this.launched || this.stuck) {
            return;
        }
        
        // Apply power-up effects
        const speedMultiplier = powerUpManager.getEffectValue('ball_speed', 1);
        this.penetrating = powerUpManager.hasEffect('penetrating');
        
        // Update position
        this.x += this.vx * speedMultiplier;
        this.y += this.vy * speedMultiplier;
        
        // Update trail
        this.updateTrail();
        
        // Update glow effect
        this.updateGlow();
        
        // Wall collisions
        this.handleWallCollisions(canvasWidth, canvasHeight);
        
        // Speed limiting
        this.limitSpeed();
    }

    updateTrail() {
        // Add current position to trail
        this.trail.push({ x: this.x, y: this.y });
        
        // Limit trail length
        if (this.trail.length > this.maxTrailLength) {
            this.trail.shift();
        }
    }

    updateGlow() {
        this.glowIntensity += this.glowDirection * 0.05;
        if (this.glowIntensity >= 1) {
            this.glowIntensity = 1;
            this.glowDirection = -1;
        } else if (this.glowIntensity <= 0) {
            this.glowIntensity = 0;
            this.glowDirection = 1;
        }
    }

    handleWallCollisions(canvasWidth, canvasHeight) {
        let collided = false;
        
        // Left wall
        if (this.x - this.radius <= 0) {
            this.x = this.radius;
            this.vx = Math.abs(this.vx);
            collided = true;
            window.particleSystem?.createWallBounce(this.x, this.y, { x: 1, y: 0 });
        }
        
        // Right wall
        if (this.x + this.radius >= canvasWidth) {
            this.x = canvasWidth - this.radius;
            this.vx = -Math.abs(this.vx);
            collided = true;
            window.particleSystem?.createWallBounce(this.x, this.y, { x: -1, y: 0 });
        }
        
        // Top wall
        if (this.y - this.radius <= 0) {
            this.y = this.radius;
            this.vy = Math.abs(this.vy);
            collided = true;
            window.particleSystem?.createWallBounce(this.x, this.y, { x: 0, y: 1 });
        }
        
        if (collided) {
            Utils.playSound('paddleHitSound', 0.3);
        }
    }

    limitSpeed() {
        const currentSpeed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        
        if (currentSpeed > this.maxSpeed) {
            const ratio = this.maxSpeed / currentSpeed;
            this.vx *= ratio;
            this.vy *= ratio;
        } else if (currentSpeed < this.minSpeed && currentSpeed > 0) {
            const ratio = this.minSpeed / currentSpeed;
            this.vx *= ratio;
            this.vy *= ratio;
        }
        
        // Prevent ball from getting stuck horizontally
        if (Math.abs(this.vy) < 0.5) {
            this.vy = this.vy > 0 ? 0.5 : -0.5;
        }
    }

    // Handle paddle collision
    handlePaddleCollision(paddle, powerUpManager) {
        const paddleBounds = paddle.getBounds();
        
        // Check if ball is colliding with paddle
        if (!Utils.circleRectIntersect(
            { x: this.x, y: this.y, radius: this.radius },
            paddleBounds
        )) {
            return false;
        }
        
        // Check if ball is moving towards paddle
        if (this.vy <= 0) return false;
        
        // Sticky paddle effect
        if (powerUpManager.hasEffect('sticky_paddle') && !this.stuck) {
            this.stickToPaddle(paddle);
            return true;
        }
        
        // Calculate collision point
        const relativeIntersectX = (this.x - (paddleBounds.x + paddleBounds.width / 2)) / (paddleBounds.width / 2);
        const normalizedRelativeIntersection = Utils.clamp(relativeIntersectX, -1, 1);
        
        // Calculate new angle based on where ball hit paddle
        const bounceAngle = normalizedRelativeIntersection * Math.PI / 3; // Max 60 degrees
        
        // Calculate new velocity
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        this.vx = Math.sin(bounceAngle) * speed;
        this.vy = -Math.abs(Math.cos(bounceAngle) * speed); // Always bounce up
        
        // Position ball above paddle
        this.y = paddleBounds.y - this.radius;
        
        // Create paddle hit effect
        window.particleSystem?.createPaddleHit(this.x, this.y, this.vx, this.vy);
        Utils.playSound('paddleHitSound', 0.5);
        
        return true;
    }

    // Stick ball to paddle
    stickToPaddle(paddle) {
        this.stuck = true;
        this.launched = false;
        this.stuckOffset = this.x - (paddle.x + paddle.width / 2);
        this.y = paddle.y - this.radius;
        this.vx = 0;
        this.vy = 0;
    }

    // Update position when stuck to paddle
    updateStuckPosition(paddle) {
        if (this.stuck) {
            this.x = paddle.x + paddle.width / 2 + this.stuckOffset;
            this.y = paddle.y - this.radius;
            
            // Keep ball within paddle bounds
            const minX = paddle.x + this.radius;
            const maxX = paddle.x + paddle.width - this.radius;
            this.x = Utils.clamp(this.x, minX, maxX);
        }
    }

    // Handle brick collision
    handleBrickCollision(brick) {
        if (!brick.checkCollision(this)) {
            return null;
        }
        
        const side = brick.getCollisionSide(this);
        
        // Don't bounce if penetrating
        if (!this.penetrating) {
            // Reflect velocity based on collision side
            switch (side) {
                case 'left':
                case 'right':
                    this.vx = -this.vx;
                    break;
                case 'top':
                case 'bottom':
                    this.vy = -this.vy;
                    break;
            }
            
            // Move ball out of brick
            this.moveOutOfBrick(brick, side);
        }
        
        // Hit the brick
        const result = brick.hit();
        
        if (result.destroyed) {
            Utils.playSound('brickBreakSound', 0.4);
        }
        
        return result;
    }

    moveOutOfBrick(brick, side) {
        const bounds = brick.getBounds();
        
        switch (side) {
            case 'left':
                this.x = bounds.x - this.radius;
                break;
            case 'right':
                this.x = bounds.x + bounds.width + this.radius;
                break;
            case 'top':
                this.y = bounds.y - this.radius;
                break;
            case 'bottom':
                this.y = bounds.y + bounds.height + this.radius;
                break;
        }
    }

    // Draw the ball
    draw(ctx) {
        ctx.save();
        
        // Draw trail
        this.drawTrail(ctx);
        
        // Glow effect
        const glowSize = 5 + this.glowIntensity * 10;
        ctx.shadowColor = this.glowColor;
        ctx.shadowBlur = glowSize;
        
        // Main ball
        const gradient = ctx.createRadialGradient(
            this.x - this.radius * 0.3, this.y - this.radius * 0.3, 0,
            this.x, this.y, this.radius
        );
        gradient.addColorStop(0, '#ffffff');
        gradient.addColorStop(0.7, this.color);
        gradient.addColorStop(1, this.darkenColor(this.color, 30));
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.beginPath();
        ctx.arc(
            this.x - this.radius * 0.4, 
            this.y - this.radius * 0.4, 
            this.radius * 0.3, 
            0, Math.PI * 2
        );
        ctx.fill();
        
        // Special effects
        if (this.penetrating) {
            this.drawPenetratingEffect(ctx);
        }
        
        ctx.restore();
    }

    drawTrail(ctx) {
        if (this.trail.length < 2) return;
        
        ctx.globalAlpha = 0.3;
        
        for (let i = 0; i < this.trail.length - 1; i++) {
            const alpha = i / this.trail.length;
            const size = this.radius * alpha * 0.5;
            
            ctx.globalAlpha = alpha * 0.3;
            ctx.fillStyle = this.glowColor;
            ctx.beginPath();
            ctx.arc(this.trail[i].x, this.trail[i].y, size, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.globalAlpha = 1;
    }

    drawPenetratingEffect(ctx) {
        // Rotating energy rings
        const time = Date.now() * 0.01;
        
        for (let i = 0; i < 3; i++) {
            const radius = this.radius + 5 + i * 3;
            const rotation = time + i * Math.PI / 3;
            
            ctx.strokeStyle = '#32cd32';
            ctx.lineWidth = 2;
            ctx.globalAlpha = 0.6 - i * 0.2;
            
            ctx.beginPath();
            for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 6) {
                const x = this.x + Math.cos(angle + rotation) * radius;
                const y = this.y + Math.sin(angle + rotation) * radius;
                
                if (angle === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.closePath();
            ctx.stroke();
        }
    }

    // Check if ball is below paddle (game over condition)
    isBelowPaddle(paddleY) {
        return this.y - this.radius > paddleY;
    }

    // Reset ball position
    reset(x, y) {
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.launched = false;
        this.stuck = false;
        this.trail = [];
        this.penetrating = false;
    }

    // Clone ball for multi-ball power-up
    clone() {
        const newBall = new Ball(this.x, this.y, this.radius);
        newBall.launched = this.launched;
        newBall.speed = this.speed;
        
        // Give it a slightly different angle
        const angle = Math.atan2(this.vy, this.vx) + Utils.random(-0.5, 0.5);
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        
        newBall.vx = Math.cos(angle) * speed;
        newBall.vy = Math.sin(angle) * speed;
        
        return newBall;
    }

    // Get ball bounds for collision
    getBounds() {
        return {
            x: this.x - this.radius,
            y: this.y - this.radius,
            width: this.radius * 2,
            height: this.radius * 2
        };
    }

    // Color utility
    darkenColor(color, percent) {
        const rgb = Utils.hexToRgb(color);
        if (!rgb) return color;
        
        const factor = 1 - percent / 100;
        return `rgb(${rgb.r * factor}, ${rgb.g * factor}, ${rgb.b * factor})`;
    }

    // Set ball color
    setColor(color, glowColor = null) {
        this.color = color;
        this.glowColor = glowColor || color;
    }
}