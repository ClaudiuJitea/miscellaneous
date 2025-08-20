# Audio Files

This directory contains audio files for the Brick Breaker game.

## Required Audio Files

The game expects the following audio files:

### Sound Effects
- `paddle-hit.mp3` - Ball hitting paddle
- `brick-break.mp3` - Brick destruction
- `wall-bounce.mp3` - Ball bouncing off walls
- `powerup-collect.mp3` - Power-up collection
- `laser-shoot.mp3` - Laser firing
- `explosion.mp3` - Explosive brick effect
- `game-over.mp3` - Game over sound
- `level-complete.mp3` - Level completion

### Background Music
- `background-music.mp3` - Main game background music (synthwave/retro style)

## Audio Format
- Format: MP3 or OGG
- Sample Rate: 44.1kHz recommended
- Bit Rate: 128kbps or higher
- Duration: Sound effects should be 0.5-2 seconds, background music can loop

## Implementation Notes
- Audio files are loaded via HTML5 `<audio>` elements in index.html
- Volume levels are controlled via the Utils.playSound() function
- Background music should be designed to loop seamlessly
- All audio should have a retro/synthwave aesthetic to match the game's visual style

## Placeholder
Currently using placeholder audio elements. Replace with actual audio files for full experience.