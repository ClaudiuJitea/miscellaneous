import pygame
import math
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (Sleek Theme)
BLACK = (0, 0, 0)
WHITE = (230, 230, 230) # Off-white for a softer look
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 255)
NEON_GREEN = (57, 255, 20)
DARK_GRAY = (40, 40, 40) # For subtle UI elements or asteroid variations
ORANGE_THRUST = (255, 165, 0)
RED_EXPLOSION = (255, 69, 0)

# Player settings
PLAYER_SIZE = 20
PLAYER_ACCELERATION = 0.25
PLAYER_DECELERATION = 0.99 # Friction
PLAYER_TURN_SPEED = 5
PLAYER_MAX_SPEED = 7
PLAYER_GUN_COOLDOWN = 200  # milliseconds
PLAYER_INVINCIBILITY_DURATION = 2000 # milliseconds after respawn
PLAYER_START_LIVES = 3

# Bullet settings
BULLET_SPEED = 10
BULLET_LIFESPAN = 50  # frames

# Asteroid settings
ASTEROID_SIZES = {3: 40, 2: 25, 1: 15} # size_level: radius
ASTEROID_MIN_SPEED = 0.5
ASTEROID_MAX_SPEED = 2.5
ASTEROID_POINTS = {3: 20, 2: 50, 1: 100}
INITIAL_ASTEROID_COUNT = 4
ASTEROID_VERTICES_MIN = 7
ASTEROID_VERTICES_MAX = 12

# --- Helper Functions ---
def draw_text(surface, text, size, x, y, color=WHITE, font_name=None):
    if font_name is None:
        font = pygame.font.Font(pygame.font.match_font('arial'), size) # Default nice font
    else:
        font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def get_random_asteroid_spawn_pos(player_pos):
    """Ensure asteroids don't spawn too close to the player."""
    while True:
        pos = pygame.math.Vector2(random.randrange(SCREEN_WIDTH), random.randrange(SCREEN_HEIGHT))
        if player_pos is None or pos.distance_to(player_pos) > 150: # Min distance from player
            return pos

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.Surface((PLAYER_SIZE * 2, PLAYER_SIZE * 2), pygame.SRCALPHA)
        # Draw a sleek triangle ship
        points = [
            (PLAYER_SIZE, 0),                           # Nose
            (0, PLAYER_SIZE * 1.5),                     # Bottom-left
            (PLAYER_SIZE * 0.5, PLAYER_SIZE * 1.2),     # Indent for thruster
            (PLAYER_SIZE * 1.5, PLAYER_SIZE * 1.2),     # Indent for thruster
            (PLAYER_SIZE * 2, PLAYER_SIZE * 1.5)        # Bottom-right
        ]
        pygame.draw.polygon(self.original_image, NEON_CYAN, points)
        
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0  # Pointing upwards
        self.last_shot_time = 0
        self.lives = PLAYER_START_LIVES
        self.is_invincible = False
        self.invincibility_timer = 0
        self.last_update_time_invincibility = pygame.time.get_ticks() # Init here
        self.is_accelerating = False

    def rotate(self, angle_degrees):
        self.angle = (self.angle + angle_degrees) % 360
        self.image = pygame.transform.rotate(self.original_image, -self.angle) # Pygame rotates counter-clockwise
        self.rect = self.image.get_rect(center=self.pos)

    def thrust(self):
        self.is_accelerating = True
        rad_angle = math.radians(self.angle)
        acceleration = pygame.math.Vector2(math.sin(rad_angle), -math.cos(rad_angle)) * PLAYER_ACCELERATION
        self.velocity += acceleration
        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

    def shoot(self, bullets_group, particles_group):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > PLAYER_GUN_COOLDOWN:
            self.last_shot_time = current_time
            rad_angle = math.radians(self.angle)
            # Calculate bullet start position (tip of the ship)
            offset_distance = PLAYER_SIZE 
            bullet_start_pos = self.pos + pygame.math.Vector2(math.sin(rad_angle), -math.cos(rad_angle)) * offset_distance
            
            bullet = Bullet(bullet_start_pos, self.angle)
            bullets_group.add(bullet)
            
            # Muzzle flash particle
            for _ in range(3): # Small burst
                 particles_group.add(Particle(bullet_start_pos, ORANGE_THRUST, random.uniform(1,3), random.uniform(5,10), self.angle + random.uniform(-30,30), spread_angle=30))


    def update(self, particles_group): # This one correctly uses particles_group
        self.velocity *= PLAYER_DECELERATION # Apply friction
        self.pos += self.velocity
        
        # Screen wrapping
        if self.pos.x < 0: self.pos.x = SCREEN_WIDTH
        if self.pos.x > SCREEN_WIDTH: self.pos.x = 0
        if self.pos.y < 0: self.pos.y = SCREEN_HEIGHT
        if self.pos.y > SCREEN_HEIGHT: self.pos.y = 0
        
        self.rect.center = self.pos

        if self.is_invincible:
            # Calculate time elapsed since last update for invincibility timer
            current_ticks = pygame.time.get_ticks()
            elapsed_time = current_ticks - self.last_update_time_invincibility
            self.invincibility_timer -= elapsed_time
            
            if self.invincibility_timer <= 0:
                self.is_invincible = False
                self.image.set_alpha(255) # Ensure fully visible when invincibility ends
            else:
                # Blinking effect
                if (current_ticks // 200) % 2 == 0:
                     self.image.set_alpha(255)
                else:
                     self.image.set_alpha(100)
        else:
            self.image.set_alpha(255) # Ensure fully visible if not invincible
        
        self.last_update_time_invincibility = pygame.time.get_ticks() # Update for next frame's calculation

        if self.is_accelerating:
            self.add_thrust_particles(particles_group)
            self.is_accelerating = False # Reset for next frame


    def add_thrust_particles(self, particles_group):
        rad_angle = math.radians(self.angle)
        # Position particles at the "rear" of the ship
        offset_distance = PLAYER_SIZE * 0.8
        particle_pos = self.pos - pygame.math.Vector2(math.sin(rad_angle), -math.cos(rad_angle)) * offset_distance
        
        for _ in range(2): # Create a couple of particles per frame of thrust
            particles_group.add(Particle(particle_pos, ORANGE_THRUST, 
                                         size=random.uniform(2, 5), 
                                         lifespan=random.uniform(10, 20),
                                         angle=self.angle + 180 + random.uniform(-20, 20), # Opposite direction
                                         speed_multiplier=0.5,
                                         spread_angle=20))


    def reset_position(self):
        self.pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0
        self.rotate(0) # To update image and rect
        self.is_invincible = True
        self.invincibility_timer = PLAYER_INVINCIBILITY_DURATION
        self.last_update_time_invincibility = pygame.time.get_ticks()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, angle):
        super().__init__()
        self.image = pygame.Surface((4, 10), pygame.SRCALPHA) # Thin rectangle
        self.image.fill(NEON_GREEN)
        self.original_image = self.image
        self.image = pygame.transform.rotate(self.original_image, -angle)
        self.rect = self.image.get_rect(center=pos)
        
        self.pos = pygame.math.Vector2(pos)
        rad_angle = math.radians(angle)
        self.velocity = pygame.math.Vector2(math.sin(rad_angle), -math.cos(rad_angle)) * BULLET_SPEED
        self.lifespan = BULLET_LIFESPAN

    def update(self): # Takes no extra arguments
        self.pos += self.velocity
        self.rect.center = self.pos
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()

        # Screen wrapping
        if self.rect.right < 0: self.pos.x = SCREEN_WIDTH + self.rect.width / 2
        if self.rect.left > SCREEN_WIDTH: self.pos.x = -self.rect.width / 2
        if self.rect.bottom < 0: self.pos.y = SCREEN_HEIGHT + self.rect.height / 2
        if self.rect.top > SCREEN_HEIGHT: self.pos.y = -self.rect.height / 2


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, pos, size_level, initial_velocity=None):
        super().__init__()
        self.size_level = size_level
        self.radius = ASTEROID_SIZES[self.size_level]
        
        self.points = []
        num_vertices = random.randint(ASTEROID_VERTICES_MIN, ASTEROID_VERTICES_MAX)
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi
            r = self.radius * random.uniform(0.7, 1.3)
            x = r * math.cos(angle) + self.radius 
            y = r * math.sin(angle) + self.radius
            self.points.append((x, y))

        self.image = pygame.Surface((self.radius * 2.6, self.radius * 2.6), pygame.SRCALPHA) 
        pygame.draw.polygon(self.image, NEON_MAGENTA, self.points, 2) 
        self.original_image = self.image 
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        if initial_velocity:
            self.velocity = initial_velocity
        else:
            random_angle = random.uniform(0, 360)
            speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)
            self.velocity = pygame.math.Vector2(speed, 0).rotate(random_angle)
        
        self.rotation_speed = random.uniform(-1, 1) * 2 
        self.angle = 0

    def update(self, *args): # <<< --- CORRECTED HERE: Added *args
        self.pos += self.velocity
        
        if self.pos.x < -self.radius: self.pos.x = SCREEN_WIDTH + self.radius
        if self.pos.x > SCREEN_WIDTH + self.radius: self.pos.x = -self.radius
        if self.pos.y < -self.radius: self.pos.y = SCREEN_HEIGHT + self.radius
        if self.pos.y > SCREEN_HEIGHT + self.radius: self.pos.y = -self.radius
        
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def split(self, asteroids_group, particles_group):
        if self.size_level > 1:
            for _ in range(2): 
                vel_offset = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1)).normalize() * 0.5
                new_vel = self.velocity + vel_offset
                new_asteroid = Asteroid(self.pos, self.size_level - 1, initial_velocity=new_vel)
                all_sprites.add(new_asteroid) # Add to all_sprites for general update and drawing
                asteroids_group.add(new_asteroid)
        
        for _ in range(int(self.radius * 0.5)): 
            particles_group.add(Particle(self.pos, RED_EXPLOSION, 
                                         size=random.uniform(1,4), 
                                         lifespan=random.uniform(20,40),
                                         speed_multiplier=random.uniform(0.5, 1.5)))
        self.kill()


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, color, size, lifespan, angle=None, speed_multiplier=1.0, spread_angle=360):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.color = color
        self.size = size
        self.lifespan = lifespan
        self.max_lifespan = lifespan 

        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.size, self.size), self.size)
        self.rect = self.image.get_rect(center=self.pos)

        if angle is None: 
            direction_angle = random.uniform(0, 360)
        else: 
            direction_angle = angle + random.uniform(-spread_angle / 2, spread_angle / 2)

        speed = random.uniform(1, 3) * speed_multiplier
        self.velocity = pygame.math.Vector2(speed, 0).rotate(direction_angle)

    def update(self): # Takes no extra arguments
        self.pos += self.velocity
        self.rect.center = self.pos
        self.lifespan -= 1

        alpha = max(0, int(255 * (self.lifespan / self.max_lifespan)))
        self.image.set_alpha(alpha)

        if self.lifespan <= 0:
            self.kill()


# --- Game Initialization ---
pygame.init()
pygame.mixer.init() 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sleek Asteroids")
clock = pygame.time.Clock()

# --- Game Variables ---
score = 0
game_over = False
show_start_screen = True

# Sprite Groups
all_sprites = pygame.sprite.Group()
asteroids = pygame.sprite.Group()
bullets = pygame.sprite.Group()
particles = pygame.sprite.Group() 

player = Player() # Create player instance first
all_sprites.add(player)


def spawn_initial_asteroids(player_pos=None):
    for _ in range(INITIAL_ASTEROID_COUNT):
        pos = get_random_asteroid_spawn_pos(player_pos)
        asteroid = Asteroid(pos, 3) 
        all_sprites.add(asteroid)
        asteroids.add(asteroid)

def reset_game():
    global score, game_over, show_start_screen, player
    score = 0
    game_over = False
    show_start_screen = True 

    all_sprites.empty()
    asteroids.empty()
    bullets.empty()
    particles.empty()
    
    player = Player()
    all_sprites.add(player)
    
def next_level():
    global score 
    bullets.empty() 
    particles.empty() 
    spawn_initial_asteroids(player.pos)


# --- Game Loop ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if show_start_screen or game_over:
                if event.key == pygame.K_RETURN:
                    if game_over:
                        reset_game() 
                    else: 
                        show_start_screen = False
                        game_over = False 
                        player.lives = PLAYER_START_LIVES 
                        player.reset_position() 
                        score = 0 
                        spawn_initial_asteroids(player.pos)

    if show_start_screen:
        screen.fill(BLACK)
        draw_text(screen, "SLEEK ASTEROIDS", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, NEON_CYAN)
        draw_text(screen, "Arrows to Move, Space to Shoot", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
        draw_text(screen, "Press ENTER to Start", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75, WHITE)
        pygame.display.flip()
        continue 

    if game_over:
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, NEON_MAGENTA)
        draw_text(screen, f"Final Score: {score}", 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
        draw_text(screen, "Press ENTER to Play Again", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75, WHITE)
        pygame.display.flip()
        continue 

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.rotate(PLAYER_TURN_SPEED)
    if keys[pygame.K_RIGHT]:
        player.rotate(-PLAYER_TURN_SPEED)
    if keys[pygame.K_UP]:
        player.thrust()
    if keys[pygame.K_SPACE]:
        player.shoot(bullets, particles)

    # Update
    all_sprites.update(particles) # Player uses particles, Asteroid now ignores it
    bullets.update()
    particles.update()

    # Check for collisions
    if not player.is_invincible:
        # Player-Asteroid collision
        hits = pygame.sprite.spritecollide(player, asteroids, False, pygame.sprite.collide_circle_ratio(0.85)) 
        for hit_asteroid in hits:
            player.lives -= 1
            hit_asteroid.split(asteroids, particles) # Asteroid breaks (and kills itself)
            
            for _ in range(30):
                 particles.add(Particle(player.pos, RED_EXPLOSION, random.uniform(2,5), random.uniform(30,60)))
            
            if player.lives <= 0:
                game_over = True
            else:
                player.reset_position()


    # Bullets-Asteroids collision
    # groupcollide: bullet_group, asteroid_group, dokill_bullet, dokill_asteroid, collision_detection_func
    bullet_hits = pygame.sprite.groupcollide(bullets, asteroids, True, False, pygame.sprite.collide_circle_ratio(0.9))
    for bullet, hit_asteroids_list in bullet_hits.items():
        for asteroid_hit in hit_asteroids_list:
            score += ASTEROID_POINTS[asteroid_hit.size_level]
            asteroid_hit.split(asteroids, particles) # This also kills the original asteroid

    if not asteroids and not game_over and not show_start_screen:
        next_level()

    # Draw / Render
    screen.fill(BLACK)
    
    for _ in range(50): 
        star_pos = (random.randrange(SCREEN_WIDTH), random.randrange(SCREEN_HEIGHT))
        star_size = random.randint(1,2)
        star_brightness = random.randint(50,150)
        pygame.draw.circle(screen, (star_brightness, star_brightness, star_brightness), star_pos, star_size)

    all_sprites.draw(screen)
    bullets.draw(screen)
    particles.draw(screen)

    draw_text(screen, f"Score: {score}", 24, SCREEN_WIDTH / 2, 10, WHITE)
    
    # Draw lives as ship icons
    icon_base_x = 10
    icon_y_top = 35 # y-coordinate for the tip of the ship icon
    icon_y_bottom = 50 # y-coordinate for the bottom points
    icon_y_indent = 47
    icon_width = 20
    icon_spacing = 25

    for i in range(player.lives):
        x_offset = i * icon_spacing
        ship_icon_points = [
            (icon_base_x + x_offset + icon_width / 2, icon_y_top),  # Nose
            (icon_base_x + x_offset, icon_y_bottom),                # Bottom-left
            (icon_base_x + x_offset + icon_width * 0.25, icon_y_indent), # Indent left
            (icon_base_x + x_offset + icon_width * 0.75, icon_y_indent), # Indent right
            (icon_base_x + x_offset + icon_width, icon_y_bottom)    # Bottom-right
        ]
        # Blink lives icons if player is invincible
        is_visible = True
        if player.is_invincible and (pygame.time.get_ticks() // 200) % 2 != 0:
            is_visible = False
        
        if is_visible:
            pygame.draw.polygon(screen, NEON_CYAN, ship_icon_points)
        else: # Draw outline if blinking
            pygame.draw.polygon(screen, NEON_CYAN, ship_icon_points, 1)


    pygame.display.flip()

pygame.quit()