/**
 * Particle system for visual effects
 */

class Particle {
    constructor(x, y, vx, vy, color = '#00ffff', size = 3, life = 1.0) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.color = color;
        this.size = size;
        this.life = life;
        this.maxLife = life;
        this.decay = Utils.random(0.015, 0.03);
        this.gravity = 0.1;
        this.alpha = 1.0;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += this.gravity;
        
        this.life -= this.decay;
        this.alpha = this.life / this.maxLife;
        
        // Fade out as life decreases
        this.size = Math.max(0, this.size * 0.98);
        
        return this.life > 0;
    }

    draw(ctx) {
        if (this.life <= 0) return;
        
        ctx.save();
        ctx.globalAlpha = this.alpha;
        
        // Create glow effect
        ctx.shadowColor = this.color;
        ctx.shadowBlur = this.size * 2;
        
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
}

class ParticleSystem {
    constructor() {
        this.particles = [];
        this.maxParticles = 500;
    }

    // Create explosion effect
    createExplosion(x, y, count = 12, color = '#00ffff', intensity = 1) {
        for (let i = 0; i < count; i++) {
            const angle = (Math.PI * 2 * i) / count + Utils.random(-0.3, 0.3);
            const speed = Utils.random(2, 6) * intensity;
            const vx = Math.cos(angle) * speed;
            const vy = Math.sin(angle) * speed;
            const size = Utils.random(2, 5);
            const life = Utils.random(0.8, 1.2);
            
            this.addParticle(new Particle(x, y, vx, vy, color, size, life));
        }
    }

    // Create spark effect
    createSparks(x, y, count = 8, color = '#ffff00') {
        for (let i = 0; i < count; i++) {
            const angle = Utils.random(0, Math.PI * 2);
            const speed = Utils.random(1, 4);
            const vx = Math.cos(angle) * speed;
            const vy = Math.sin(angle) * speed - Utils.random(1, 3);
            const size = Utils.random(1, 3);
            const life = Utils.random(0.5, 1.0);
            
            this.addParticle(new Particle(x, y, vx, vy, color, size, life));
        }
    }

    // Create trail effect
    createTrail(x, y, vx, vy, color = '#00ffff', count = 3) {
        for (let i = 0; i < count; i++) {
            const offsetX = Utils.random(-2, 2);
            const offsetY = Utils.random(-2, 2);
            const trailVx = vx * 0.1 + Utils.random(-0.5, 0.5);
            const trailVy = vy * 0.1 + Utils.random(-0.5, 0.5);
            const size = Utils.random(1, 2);
            const life = Utils.random(0.3, 0.6);
            
            this.addParticle(new Particle(
                x + offsetX, y + offsetY, 
                trailVx, trailVy, 
                color, size, life
            ));
        }
    }

    // Create power-up collection effect
    createPowerUpEffect(x, y, color = '#ff6b6b') {
        // Central burst
        this.createExplosion(x, y, 16, color, 1.5);
        
        // Ring effect
        for (let i = 0; i < 8; i++) {
            const angle = (Math.PI * 2 * i) / 8;
            const ringX = x + Math.cos(angle) * 20;
            const ringY = y + Math.sin(angle) * 20;
            const vx = Math.cos(angle) * 2;
            const vy = Math.sin(angle) * 2;
            
            this.addParticle(new Particle(ringX, ringY, vx, vy, color, 3, 1.0));
        }
    }

    // Create brick destruction effect
    createBrickDestruction(x, y, width, height, color = '#00ffff') {
        // Main explosion
        this.createExplosion(x + width/2, y + height/2, 15, color, 1.2);
        
        // Corner particles
        const corners = [
            {x: x, y: y},
            {x: x + width, y: y},
            {x: x, y: y + height},
            {x: x + width, y: y + height}
        ];
        
        corners.forEach(corner => {
            for (let i = 0; i < 3; i++) {
                const vx = Utils.random(-3, 3);
                const vy = Utils.random(-4, -1);
                const size = Utils.random(2, 4);
                const life = Utils.random(0.8, 1.2);
                
                this.addParticle(new Particle(corner.x, corner.y, vx, vy, color, size, life));
            }
        });
        
        // Debris particles
        for (let i = 0; i < 8; i++) {
            const debrisX = x + Utils.random(0, width);
            const debrisY = y + Utils.random(0, height);
            const vx = Utils.random(-2, 2);
            const vy = Utils.random(-3, 1);
            const size = Utils.random(1, 3);
            const life = Utils.random(1.0, 1.5);
            
            this.addParticle(new Particle(debrisX, debrisY, vx, vy, color, size, life));
        }
    }

    // Create paddle hit effect
    createPaddleHit(x, y, ballVx, ballVy) {
        const color = '#ffffff';
        const count = 6;
        
        for (let i = 0; i < count; i++) {
            const angle = Math.atan2(-ballVy, ballVx) + Utils.random(-0.5, 0.5);
            const speed = Utils.random(1, 3);
            const vx = Math.cos(angle) * speed;
            const vy = Math.sin(angle) * speed;
            const size = Utils.random(2, 4);
            const life = Utils.random(0.4, 0.8);
            
            this.addParticle(new Particle(x, y, vx, vy, color, size, life));
        }
    }

    // Create wall bounce effect
    createWallBounce(x, y, normal) {
        const color = '#00cccc';
        const count = 4;
        
        for (let i = 0; i < count; i++) {
            const vx = normal.x * Utils.random(1, 3) + Utils.random(-1, 1);
            const vy = normal.y * Utils.random(1, 3) + Utils.random(-1, 1);
            const size = Utils.random(1, 3);
            const life = Utils.random(0.3, 0.6);
            
            this.addParticle(new Particle(x, y, vx, vy, color, size, life));
        }
    }

    // Create level complete effect
    createLevelComplete(canvasWidth, canvasHeight) {
        // Fireworks effect
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const x = Utils.random(canvasWidth * 0.2, canvasWidth * 0.8);
                const y = Utils.random(canvasHeight * 0.2, canvasHeight * 0.6);
                const colors = ['#00ffff', '#ff6b6b', '#ffff00', '#ff00ff', '#00ff00'];
                const color = colors[Utils.randomInt(0, colors.length - 1)];
                
                this.createExplosion(x, y, 20, color, 2);
            }, i * 200);
        }
    }

    // Add particle to system
    addParticle(particle) {
        if (this.particles.length >= this.maxParticles) {
            this.particles.shift(); // Remove oldest particle
        }
        this.particles.push(particle);
    }

    // Update all particles
    update() {
        this.particles = this.particles.filter(particle => particle.update());
    }

    // Draw all particles
    draw(ctx) {
        this.particles.forEach(particle => particle.draw(ctx));
    }

    // Clear all particles
    clear() {
        this.particles = [];
    }

    // Get particle count
    getCount() {
        return this.particles.length;
    }
}

// ParticleSystem class - instance created in app.js