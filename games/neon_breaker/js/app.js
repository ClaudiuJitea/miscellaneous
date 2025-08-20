/**
 * Main application entry point
 * Initializes the game and global systems
 */

// Global particle system instance
window.particleSystem = null;

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Initialize particle system
        window.particleSystem = new ParticleSystem();
        
        // Initialize game
        window.game = new Game('gameCanvas');
        
        // Add debug mode toggle (for development)
        window.DEBUG = false;
        
        // Add keyboard shortcut for debug mode
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.code === 'KeyD') {
                window.DEBUG = !window.DEBUG;
                console.log('Debug mode:', window.DEBUG ? 'ON' : 'OFF');
            }
        });
        
        // Handle visibility change (pause when tab is not active)
        document.addEventListener('visibilitychange', () => {
            if (window.game && window.game.state === 'playing') {
                if (document.hidden) {
                    window.game.togglePause();
                }
            }
        });
        
        // Prevent context menu on canvas
        const canvas = document.getElementById('gameCanvas');
        canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
        
        // Handle touch events for mobile
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
        });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
        });
        
        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
        });
        
        console.log('Brick Breaker game initialized successfully!');
        
    } catch (error) {
        console.error('Failed to initialize game:', error);
        
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            text-align: center;
            z-index: 10000;
        `;
        errorDiv.innerHTML = `
            <h3>Game Initialization Error</h3>
            <p>Failed to start the game. Please refresh the page.</p>
            <p><small>${error.message}</small></p>
        `;
        document.body.appendChild(errorDiv);
    }
});

// Handle window resize
window.addEventListener('resize', Utils.debounce(() => {
    if (window.game) {
        window.game.resizeCanvas();
    }
}, 250));

// Handle window focus/blur for audio management
window.addEventListener('focus', () => {
    // Resume audio context if needed
    if (window.AudioContext || window.webkitAudioContext) {
        // Audio management can be added here
    }
});

window.addEventListener('blur', () => {
    // Pause game if playing
    if (window.game && window.game.state === 'playing') {
        window.game.togglePause();
    }
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Game, ParticleSystem };
}