/**
 * Utility functions for the Brick Breaker game
 */

// Math utilities
const Utils = {
    // Clamp a value between min and max
    clamp: (value, min, max) => {
        return Math.min(Math.max(value, min), max);
    },

    // Linear interpolation
    lerp: (start, end, factor) => {
        return start + (end - start) * factor;
    },

    // Distance between two points
    distance: (x1, y1, x2, y2) => {
        const dx = x2 - x1;
        const dy = y2 - y1;
        return Math.sqrt(dx * dx + dy * dy);
    },

    // Normalize angle to 0-2π range
    normalizeAngle: (angle) => {
        while (angle < 0) angle += Math.PI * 2;
        while (angle >= Math.PI * 2) angle -= Math.PI * 2;
        return angle;
    },

    // Random number between min and max
    random: (min, max) => {
        return Math.random() * (max - min) + min;
    },

    // Random integer between min and max (inclusive)
    randomInt: (min, max) => {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    // Check if two rectangles intersect
    rectIntersect: (rect1, rect2) => {
        return rect1.x < rect2.x + rect2.width &&
               rect1.x + rect1.width > rect2.x &&
               rect1.y < rect2.y + rect2.height &&
               rect1.y + rect1.height > rect2.y;
    },

    // Check if a circle intersects with a rectangle
    circleRectIntersect: (circle, rect) => {
        const distX = Math.abs(circle.x - rect.x - rect.width / 2);
        const distY = Math.abs(circle.y - rect.y - rect.height / 2);

        if (distX > (rect.width / 2 + circle.radius)) return false;
        if (distY > (rect.height / 2 + circle.radius)) return false;

        if (distX <= (rect.width / 2)) return true;
        if (distY <= (rect.height / 2)) return true;

        const dx = distX - rect.width / 2;
        const dy = distY - rect.height / 2;
        return (dx * dx + dy * dy <= (circle.radius * circle.radius));
    },

    // Get collision side for ball-rectangle collision
    getCollisionSide: (ball, rect) => {
        const ballCenterX = ball.x;
        const ballCenterY = ball.y;
        const rectCenterX = rect.x + rect.width / 2;
        const rectCenterY = rect.y + rect.height / 2;

        const dx = ballCenterX - rectCenterX;
        const dy = ballCenterY - rectCenterY;

        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);

        const halfWidth = rect.width / 2;
        const halfHeight = rect.height / 2;

        if (absDx / halfWidth > absDy / halfHeight) {
            return dx > 0 ? 'right' : 'left';
        } else {
            return dy > 0 ? 'bottom' : 'top';
        }
    },

    // Create particle effect
    createParticles: (x, y, count = 8, color = '#00ffff') => {
        const particles = [];
        for (let i = 0; i < count; i++) {
            particles.push({
                x: x,
                y: y,
                vx: Utils.random(-3, 3),
                vy: Utils.random(-3, 3),
                life: 1.0,
                decay: Utils.random(0.02, 0.05),
                size: Utils.random(2, 6),
                color: color
            });
        }
        return particles;
    },

    // Screen shake effect
    screenShake: (duration = 500) => {
        const canvas = document.getElementById('gameCanvas');
        canvas.classList.add('screen-shake');
        setTimeout(() => {
            canvas.classList.remove('screen-shake');
        }, duration);
    },

    // Format score with leading zeros
    formatScore: (score) => {
        return score.toString().padStart(6, '0');
    },

    // Save to local storage
    saveToStorage: (key, data) => {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    },

    // Load from local storage
    loadFromStorage: (key, defaultValue = null) => {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (e) {
            console.warn('Could not load from localStorage:', e);
            return defaultValue;
        }
    },

    // Play sound with volume control
    playSound: (soundId, volume = 0.5) => {
        try {
            const sound = document.getElementById(soundId);
            if (sound) {
                sound.volume = volume;
                sound.currentTime = 0;
                sound.play().catch(e => console.warn('Could not play sound:', e));
            }
        } catch (e) {
            console.warn('Sound error:', e);
        }
    },

    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Color utilities
    hexToRgb: (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    },

    // Create gradient
    createGradient: (ctx, x1, y1, x2, y2, colors) => {
        const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
        colors.forEach((color, index) => {
            gradient.addColorStop(index / (colors.length - 1), color);
        });
        return gradient;
    },

    // Easing functions
    easeInOut: (t) => {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    },

    easeOut: (t) => {
        return 1 - Math.pow(1 - t, 3);
    },

    // Performance monitoring
    fps: {
        frames: 0,
        lastTime: 0,
        current: 0,
        update: function() {
            this.frames++;
            const now = performance.now();
            if (now - this.lastTime >= 1000) {
                this.current = Math.round((this.frames * 1000) / (now - this.lastTime));
                this.frames = 0;
                this.lastTime = now;
            }
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}