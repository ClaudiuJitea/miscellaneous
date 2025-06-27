import pygame
import pygame.font
import random
import math
import json
import sys
from pathlib import Path

# Initialize Pygame
pygame.init()

# Game Constants
WIDTH = 1280
HEIGHT = 720
FPS = 60
COLORS = {
    "primary": "#2C3E50",
    "secondary": "#E74C3C", 
    "accent": "#3498DB",
    "background": "#1A1A1A",
    "highlight": "#ECF0F1"
}

class Game:
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Brick Breaker")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize fonts with handwriting style options
        handwriting_fonts = ["Ink Free", "Bradley Hand ITC", "Segoe Script", "Comic Sans MS", "Brush Script MT"]
        for font_name in handwriting_fonts:
            if font_name.lower() in [f.lower() for f in pygame.font.get_fonts()]:
                self.score_font = pygame.font.SysFont(font_name, 42)
                self.title_font = pygame.font.SysFont(font_name, 54)
                break
        else:
            # If none of the handwriting fonts are available, use the system default
            self.score_font = pygame.font.Font(None, 42)
            self.title_font = pygame.font.Font(None, 54)
        
        self.icon_font = pygame.font.SysFont("arial", 24)  # Font for power-up icons
        
        # Initialize game objects
        self.paddle = Paddle()
        self.ball = Ball()
        self.bricks = []
        self.particles = ParticleSystem()
        self.powerups = []
        self.active_powerups = {}  # Change to dict to track individual timers
        self.laser_cooldown = 0
        self.laser_timer = 0  # Add timer for automatic shooting
        self.laser_interval = FPS  # Shoot every second (60 frames)
        self.original_paddle_width = 200
        self.extra_balls = []
        
        # Initialize bricks
        brick_cols = 10
        brick_rows = 5
        brick_width = WIDTH // brick_cols - 10
        brick_height = 30
        brick_colors = [
            COLORS["secondary"],
            COLORS["accent"],
            COLORS["highlight"]
        ]
        
        for row in range(brick_rows):
            for col in range(brick_cols):
                x = col * (brick_width + 10) + 5
                y = row * (brick_height + 10) + 50
                durability = random.choice([1, 2, 3])
                brick = Brick(x, y, brick_width, brick_height, durability)
                self.bricks.append(brick)
        
        # Add game state flags
        self.game_over = False
        self.score = 0
        self.lives = 3
        self.level = 1
        
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            
            if not self.game_over:
                self.update()
            
            self.render()
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        self.running = False
                elif event.key == pygame.K_SPACE:  # Add space key to launch ball
                    self.ball.start_moving()
                    
    def reset_game(self):
        # Reset game state
        self.game_over = False
        self.score = 0
        self.lives = 3
        
        # Reset paddle and ball
        self.paddle = Paddle()
        self.ball = Ball()
        
        # Reset bricks
        self.bricks = []
        brick_cols = 10
        brick_rows = 5
        brick_width = WIDTH // brick_cols - 10
        brick_height = 30
        
        for row in range(brick_rows):
            for col in range(brick_cols):
                x = col * (brick_width + 10) + 5
                y = row * (brick_height + 10) + 50
                durability = random.choice([1, 2, 3])
                brick = Brick(x, y, brick_width, brick_height, durability)
                self.bricks.append(brick)
        
        # Reset power-ups
        self.powerups = []
        self.active_powerups = {}
        self.laser_cooldown = 0
        self.laser_timer = 0
        self.laser_interval = FPS
        self.original_paddle_width = 200
        self.extra_balls = []
        
    def update(self):
        # Update game objects
        self.paddle.update()
        if self.ball.update(self.paddle.rect):
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.ball.reset()
                
        # Update extra balls if they exist
        for ball in self.extra_balls[:]:
            if ball.update(self.paddle.rect):
                self.extra_balls.remove(ball)
                
        # Update active power-ups timers
        current_time = pygame.time.get_ticks()
        for powerup_type in list(self.active_powerups.keys()):
            if current_time - self.active_powerups[powerup_type] >= 10000:  # 10 seconds in milliseconds
                self.deactivate_powerup(powerup_type)
                
        # Update falling power-ups
        for powerup in self.powerups[:]:
            if not powerup.active and powerup.rect.colliderect(self.paddle.rect):
                self.activate_powerup(powerup)
                self.powerups.remove(powerup)
            elif powerup.rect.bottom >= HEIGHT:
                self.powerups.remove(powerup)
            else:
                powerup.update()
                
        # Update laser timer and fire automatically if active
        if 'laser' in self.active_powerups:
            self.laser_timer += 1
            if self.laser_timer >= self.laser_interval:
                self.fire_laser()
                self.laser_timer = 0  # Reset timer after firing
                
        # Update laser cooldown
        if self.laser_cooldown > 0:
            self.laser_cooldown -= 1
                
        self.particles.update()
        self.check_collisions()
        
    def render(self):
        # Clear screen
        self.screen.fill(pygame.Color(COLORS["background"]))
        
        # Draw game objects
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        for brick in self.bricks:
            brick.draw(self.screen)
        self.particles.draw(self.screen)
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(self.screen)
            
        # Draw extra balls
        for ball in self.extra_balls:
            ball.draw(self.screen)
            
        # Draw lasers if active
        if 'laser' in self.active_powerups:
            # Draw left laser
            pygame.draw.line(
                self.screen,
                pygame.Color(COLORS["secondary"]),
                (self.paddle.rect.left, 0),
                (self.paddle.rect.left, self.paddle.rect.top),
                3
            )
            # Draw right laser
            pygame.draw.line(
                self.screen,
                pygame.Color(COLORS["secondary"]),
                (self.paddle.rect.right, 0),
                (self.paddle.rect.right, self.paddle.rect.top),
                3
            )
            
        # Draw power-up indicators with remaining time
        if self.active_powerups:
            y_offset = 40
            current_time = pygame.time.get_ticks()
            for powerup_type, start_time in self.active_powerups.items():
                remaining_time = 10 - (current_time - start_time) // 1000
                text = self.score_font.render(
                    f"{powerup_type.title()} Active! ({remaining_time}s)", 
                    True, 
                    pygame.Color(COLORS["highlight"])
                )
                self.screen.blit(text, (20, y_offset))
                y_offset += 30
        
        if not self.game_over:
            # Draw HUD
            score_text = self.score_font.render(f"Score: {self.score}", True, pygame.Color(COLORS["highlight"]))
            self.screen.blit(score_text, (20, 5))
            
            lives_text = self.score_font.render(f"Lives: {self.lives}", True, pygame.Color(COLORS["highlight"]))
            self.screen.blit(lives_text, (WIDTH - 150, 5))
        else:
            # Draw game over screen
            game_over_text = self.title_font.render("Game Over!", True, pygame.Color(COLORS["secondary"]))
            score_text = self.score_font.render(f"Final Score: {self.score}", True, pygame.Color(COLORS["highlight"]))
            restart_text = self.score_font.render("Press R to Restart or Q to Quit", True, pygame.Color(COLORS["highlight"]))
            
            game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 90))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(score_text, score_rect)
            self.screen.blit(restart_text, restart_rect)
        
        # Update display
        pygame.display.flip()
        
    def check_collisions(self):
        # Ball-paddle collision
        if self.ball.rect.colliderect(self.paddle.rect):
            self.ball.bounce_y()
            
        # Ball-brick collisions
        for brick in self.bricks[:]:
            if self.ball.rect.colliderect(brick.rect):
                brick.hit()
                self.ball.bounce_y()
                if brick.destroyed:
                    self.bricks.remove(brick)
                    self.score += 10
                    self.particles.spawn(brick.rect.center)
                    # 20% chance to spawn a power-up
                    if random.random() < 0.2:
                        self.powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, self.icon_font))
                    
    def activate_powerup(self, powerup):
        current_time = pygame.time.get_ticks()
        self.active_powerups[powerup.type] = current_time
        
        if powerup.type == 'expand':
            self.paddle.width = self.original_paddle_width * 1.5
            self.paddle.rect.width = self.paddle.width
            
        elif powerup.type == 'multiball':
            for _ in range(2):  # Add 2 extra balls
                new_ball = Ball()
                new_ball.rect.center = self.ball.rect.center
                new_ball.dx = random.choice([-1, 1]) * self.ball.speed
                new_ball.dy = -self.ball.speed
                new_ball.waiting = False
                self.extra_balls.append(new_ball)
                
    def deactivate_powerup(self, powerup_type):
        if powerup_type in self.active_powerups:
            del self.active_powerups[powerup_type]
            
            if powerup_type == 'expand':
                self.paddle.width = self.original_paddle_width
                self.paddle.rect.width = self.paddle.width
                
            elif powerup_type == 'multiball':
                self.extra_balls.clear()
                
    def fire_laser(self):
        self.laser_cooldown = 5  # Short cooldown for visual effect
        
        # Fire from left edge
        left_x = self.paddle.rect.left
        hit_brick = False
        for brick in self.bricks[:]:
            if (brick.rect.left <= left_x <= brick.rect.right and 
                brick.rect.bottom > 0):  # Only hit bricks above the paddle
                brick.hit()
                if brick.destroyed:
                    self.bricks.remove(brick)
                    self.score += 10
                    self.particles.spawn(brick.rect.center)
                    hit_brick = True
                    break
                    
        # Fire from right edge
        right_x = self.paddle.rect.right
        hit_brick = False
        for brick in self.bricks[:]:
            if (brick.rect.left <= right_x <= brick.rect.right and 
                brick.rect.bottom > 0):  # Only hit bricks above the paddle
                brick.hit()
                if brick.destroyed:
                    self.bricks.remove(brick)
                    self.score += 10
                    self.particles.spawn(brick.rect.center)
                    hit_brick = True
                    break
                    
class Paddle:
    def __init__(self):
        self.width = 200
        self.height = 20
        self.speed = 10
        self.rect = pygame.Rect(
            WIDTH//2 - self.width//2,
            HEIGHT - 50,
            self.width,
            self.height
        )
        # Add tilt animation properties
        self.tilt_angle = 0
        self.max_tilt = 15  # Maximum rotation angle in degrees
        self.tilt_speed = 2  # Speed of tilt change
        
    def update(self):
        keys = pygame.key.get_pressed()
        moving_left = keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_RIGHT]
        
        if moving_left:
            self.rect.x -= self.speed
            # Gradually tilt left
            self.tilt_angle = min(self.tilt_angle + self.tilt_speed, self.max_tilt)
        elif moving_right:
            self.rect.x += self.speed
            # Gradually tilt right
            self.tilt_angle = max(self.tilt_angle - self.tilt_speed, -self.max_tilt)
        else:
            # Return to neutral position
            if self.tilt_angle > 0:
                self.tilt_angle = max(0, self.tilt_angle - self.tilt_speed)
            elif self.tilt_angle < 0:
                self.tilt_angle = min(0, self.tilt_angle + self.tilt_speed)
            
        # Keep paddle on screen
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)
        
    def draw(self, surface):
        # Create a surface for the paddle
        paddle_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(
            paddle_surface,
            pygame.Color(COLORS["primary"]),
            (0, 0, self.width, self.height),
            border_radius=10
        )
        
        # Rotate the paddle surface
        rotated_surface = pygame.transform.rotate(paddle_surface, self.tilt_angle)
        # Get the new rect for positioning
        rotated_rect = rotated_surface.get_rect(center=self.rect.center)
        
        # Draw the rotated paddle
        surface.blit(rotated_surface, rotated_rect)
        
class Ball:
    def __init__(self):
        self.radius = 10
        self.speed = 5
        self.rect = pygame.Rect(
            WIDTH//2 - self.radius,
            HEIGHT//2 - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        self.dx = 0
        self.dy = 0
        self.waiting = True  # New state to track if ball is waiting to start
        
    def update(self, paddle_rect=None):
        if self.waiting and paddle_rect:
            # If waiting, follow the paddle
            self.rect.centerx = paddle_rect.centerx
            self.rect.bottom = paddle_rect.top
            return False
            
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Wall collisions
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.bounce_x()
        if self.rect.top <= 0:
            self.bounce_y()
            
        # Bottom screen check
        if self.rect.bottom >= HEIGHT:
            return True  # Return True to indicate life lost
        return False
        
    def start_moving(self):
        if self.waiting:
            self.waiting = False
            self.dx = random.choice([-1, 1]) * self.speed
            self.dy = -self.speed
        
    def bounce_x(self):
        self.dx *= -1
        
    def bounce_y(self):
        self.dy *= -1
        
    def reset(self):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        self.dx = 0
        self.dy = 0
        self.waiting = True
        
    def draw(self, surface):
        pygame.draw.circle(
            surface,
            pygame.Color(COLORS["accent"]),
            self.rect.center,
            self.radius
        )
        
class Brick:
    def __init__(self, x, y, width, height, durability):
        self.rect = pygame.Rect(x, y, width, height)
        self.durability = durability
        self.destroyed = False
        
    def hit(self):
        self.durability -= 1
        if self.durability <= 0:
            self.destroyed = True
            
    def draw(self, surface):
        color = COLORS["secondary"] if self.durability > 1 else COLORS["highlight"]
        pygame.draw.rect(
            surface,
            pygame.Color(color),
            self.rect,
            border_radius=5
        )
        
class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def spawn(self, position):
        for _ in range(20):
            self.particles.append(Particle(position))
            
    def update(self):
        for particle in self.particles:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
                
    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)
            
class Particle:
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [
            random.uniform(-2, 2),
            random.uniform(-2, 2)
        ]
        self.size = random.randint(2, 5)
        self.color = random.choice([
            COLORS["accent"],
            COLORS["secondary"],
            COLORS["highlight"]
        ])
        self.lifetime = random.randint(20, 40)
        
    def update(self):
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.lifetime -= 1
        
    def draw(self, surface):
        pygame.draw.circle(
            surface,
            self.color,
            [int(p) for p in self.position],
            self.size
        )
        
class PowerUp:
    def __init__(self, x, y, icon_font):
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed = 3
        self.type = random.choice(['laser', 'expand', 'multiball'])
        self.active = False
        self.timer = 0
        self.duration = 10 * FPS  # 10 seconds * 60 FPS
        self.icon_font = icon_font  # Store the font reference
        
    def update(self):
        if not self.active:
            self.rect.y += self.speed
        elif self.active:
            self.timer += 1
            if self.timer >= self.duration:
                return True  # Power-up has expired
        return False
        
    def draw(self, surface):
        if not self.active:
            color = COLORS["highlight"]
            pygame.draw.rect(surface, pygame.Color(color), self.rect, border_radius=5)
            # Draw an icon or letter to indicate power-up type
            text = self.icon_font.render(self.type[0].upper(), True, pygame.Color(COLORS["primary"]))
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
        
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()