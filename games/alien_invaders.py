import pygame
import random
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MAX_LEVELS = 3

# Game States
INTRO = 0
PLAYING_WAVE = 1
BOSS_FIGHT = 2
GAME_OVER = 3
PLAYER_WON = 4
LEVEL_TRANSITION = 5

# Colors
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 20)
WHITE = (220, 220, 220)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)
BLUE = (0, 100, 255)
LIGHT_GREEN = (150, 255, 150)  # Extra Life powerup

# Player Settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 20
PLAYER_SPEED = 6
PLAYER_COLOR = CYAN
PLAYER_GUN_HEIGHT = 5
PLAYER_INITIAL_LIVES = 3

# Bullet Settings
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
PLAYER_BULLET_SPEED = 10
ALIEN_BULLET_SPEED = 5
BOSS_BULLET_SPEED = 6
PLAYER_BULLET_COLOR = WHITE
ALIEN_BULLET_COLOR = RED
BOSS_BULLET_COLOR = ORANGE
PLAYER_BASE_COOLDOWN = 300
PLAYER_RAPID_COOLDOWN = 100

# Alien Settings
ALIEN_COLS = 9
ALIEN_ROWS = 4
ALIEN_WIDTH = 35
ALIEN_HEIGHT = 25
ALIEN_H_SPACE = 15
ALIEN_V_SPACE = 15
ALIEN_TOP_MARGIN = 50
ALIEN_BASE_MOVE_SPEED = 1
ALIEN_DROP_DISTANCE = 10
ALIEN_BASE_SHOOT_CHANCE = 0.001  # Base chance (Grunt)
ALIEN_SHOOTER_MULTIPLIER = 3.0  # Shooter shoots this much more often
ALIEN_TANK_HEALTH = 3
ALIEN_INITIAL_MOVE_INTERVAL = 600
ALIEN_MIN_MOVE_INTERVAL = 60

# Boss Settings
BOSS_WIDTH = 100
BOSS_HEIGHT = 50
BOSS_BASE_HEALTH = 25  # Slightly higher base
BOSS_SPEED = 3
BOSS_SHOOT_CHANCE = 0.025  # Base chance, modified by pattern
BOSS_COLOR = PURPLE
BOSS_SWOOP_SPEED_Y = 2
BOSS_SWOOP_RANGE = 100  # How far down it swoops

# Power-up Settings
POWERUP_WIDTH = 25
POWERUP_HEIGHT = 25
POWERUP_SPEED = 3
POWERUP_BASE_SPAWN_CHANCE = 0.0007  # Base chance
POWERUP_LIFE_SPAWN_MOD = 0.2  # Extra life is much rarer
POWERUP_DURATION = 15000  # 15 seconds
POWERUP_TYPES = ["rapid_fire", "shield", "spread_shot", "pierce_shot", "extra_life"]
POWERUP_COLORS = {
    "rapid_fire": YELLOW,
    "shield": BLUE,
    "spread_shot": ORANGE,
    "pierce_shot": WHITE,
    "extra_life": LIGHT_GREEN,
}

# --- Classes ---


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_orig = pygame.Surface(
            [PLAYER_WIDTH, PLAYER_HEIGHT + PLAYER_GUN_HEIGHT], pygame.SRCALPHA
        )
        # ... (drawing code remains the same) ...
        points = [
            (0, PLAYER_HEIGHT),
            (PLAYER_WIDTH // 2, 0),
            (PLAYER_WIDTH, PLAYER_HEIGHT),
        ]
        pygame.draw.polygon(self.image_orig, PLAYER_COLOR, points)
        gun_rect = pygame.Rect(
            PLAYER_WIDTH // 2 - 2, PLAYER_HEIGHT, 4, PLAYER_GUN_HEIGHT
        )
        pygame.draw.rect(self.image_orig, PLAYER_COLOR, gun_rect)

        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect(
            centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 20
        )
        self.speed_x = 0
        self.lives = PLAYER_INITIAL_LIVES
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

        self.powerup_type = None
        self.powerup_end_time = 0
        self.last_shot_time = 0
        self.shoot_cooldown = PLAYER_BASE_COOLDOWN
        self.piercing = False  # For pierce_shot powerup

    def update(self):
        now = pygame.time.get_ticks()
        self.handle_powerups(now)
        self.handle_invincibility(now)

        if self.hidden:
            return  # Skip rest if hidden

        self.handle_movement()
        self.handle_shooting(now)

    def handle_powerups(self, now):
        if (
            self.powerup_type
            and self.powerup_type != "extra_life"
            and now > self.powerup_end_time
        ):
            self.deactivate_powerup()

        self.shoot_cooldown = (
            PLAYER_RAPID_COOLDOWN
            if self.powerup_type == "rapid_fire"
            else PLAYER_BASE_COOLDOWN
        )
        self.piercing = self.powerup_type == "pierce_shot"

        if self.powerup_type == "shield":
            self.image = self.image_orig.copy()
            shield_rect = self.image.get_rect().inflate(8, 8)
            alpha = 150 + math.sin(now * 0.01) * 100  # Pulsing alpha
            shield_color_alpha = (*BLUE, int(max(0, min(255, alpha))))
            # Draw filled shield for better visibility
            temp_shield_surf = pygame.Surface(shield_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                temp_shield_surf,
                shield_color_alpha,
                temp_shield_surf.get_rect(),
                border_radius=7,
            )
            self.image.blit(
                temp_shield_surf,
                temp_shield_surf.get_rect(center=self.image.get_rect().center),
            )
            # pygame.draw.rect(self.image, BLUE, shield_rect, 2, border_radius=5) # Outline instead?
        elif not self.hidden:  # Avoid resetting image while hidden flicker is active
            self.image = self.image_orig.copy()

    def handle_invincibility(self, now):
        if self.hidden and now - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2
            self.rect.bottom = SCREEN_HEIGHT - 20
            self.image.set_alpha(255)  # Ensure visible

        if self.hidden:
            visible = (now // 100) % 2 == 0
            self.image.set_alpha(255 if visible else 0)

    def handle_movement(self):
        self.speed_x = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT] or keystate[pygame.K_a]:
            self.speed_x = -PLAYER_SPEED
        if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
            self.speed_x = PLAYER_SPEED
        self.rect.x += self.speed_x
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)

    def handle_shooting(self, now):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE] and now - self.last_shot_time > self.shoot_cooldown:
            self.shoot()
            self.last_shot_time = now

    def shoot(self):
        if not self.hidden:
            center_x, top_y = self.rect.centerx, self.rect.top
            if self.powerup_type == "spread_shot":
                # Center bullet
                b1 = Bullet(
                    center_x,
                    top_y,
                    -PLAYER_BULLET_SPEED,
                    PLAYER_BULLET_COLOR,
                    dx=0,
                    piercing=self.piercing,
                )
                # Left bullet
                b2 = Bullet(
                    center_x - 5,
                    top_y,
                    -PLAYER_BULLET_SPEED * 0.9,
                    PLAYER_BULLET_COLOR,
                    dx=-2,
                    piercing=self.piercing,
                )
                # Right bullet
                b3 = Bullet(
                    center_x + 5,
                    top_y,
                    -PLAYER_BULLET_SPEED * 0.9,
                    PLAYER_BULLET_COLOR,
                    dx=2,
                    piercing=self.piercing,
                )
                all_sprites.add(b1, b2, b3)
                player_bullets.add(b1, b2, b3)
            else:
                # Standard single shot
                bullet = Bullet(
                    center_x,
                    top_y,
                    -PLAYER_BULLET_SPEED,
                    PLAYER_BULLET_COLOR,
                    dx=0,
                    piercing=self.piercing,
                )
                all_sprites.add(bullet)
                player_bullets.add(bullet)

    def activate_powerup(self, type):
        if type == "extra_life":
            print("Activated powerup: Extra Life!")
            self.lives += 1
            # Don't set timer or type for instant effects
        else:
            print(f"Activated powerup: {type}")
            # If activating a new timed powerup while another is active, deactivate old one first
            if self.powerup_type and self.powerup_type != "extra_life":
                self.deactivate_powerup()  # Cleanly remove old effects

            self.powerup_type = type
            self.powerup_end_time = pygame.time.get_ticks() + POWERUP_DURATION

    def deactivate_powerup(self):
        print(f"Deactivated powerup: {self.powerup_type}")
        self.powerup_type = None
        self.piercing = False  # Ensure piercing stops
        self.shoot_cooldown = PLAYER_BASE_COOLDOWN
        if not self.hidden:  # Avoid interfering with hidden flicker
            self.image = self.image_orig.copy()

    def hide(self):
        if self.powerup_type == "shield":
            print("Shield protected player!")
            self.deactivate_powerup()  # Shield breaks on hit
            # Optional: Add shield break effect
            return False  # Not hidden

        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT + 200)
        self.deactivate_powerup()  # Lose powerup on hit
        return True

    def reset_state(self):
        self.lives = PLAYER_INITIAL_LIVES
        self.hidden = False
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.image.set_alpha(255)
        self.deactivate_powerup()


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, type, level):
        super().__init__()
        self.type = type
        self.level = level
        self.health = 1
        self.shoot_chance_mod = 1.0
        color = MAGENTA  # Default Grunt

        if type == "shooter":
            color = ORANGE
            self.shoot_chance_mod = ALIEN_SHOOTER_MULTIPLIER
        elif type == "tank":
            color = PURPLE
            self.health = ALIEN_TANK_HEALTH + (
                level // 2
            )  # Tanks get tougher in later levels
            self.shoot_chance_mod = 0.5  # Tanks shoot less

        self.max_health = self.health
        self.image_orig = pygame.Surface(
            [ALIEN_WIDTH, ALIEN_HEIGHT + 4], pygame.SRCALPHA
        )
        self.image_orig.set_colorkey(BLACK)
        # Draw based on type/color
        pygame.draw.rect(
            self.image_orig, color, (0, 0, ALIEN_WIDTH, ALIEN_HEIGHT), border_radius=5
        )
        # Add unique visual cues?
        if type == "tank":
            pygame.draw.rect(
                self.image_orig,
                WHITE,
                (5, 5, ALIEN_WIDTH - 10, ALIEN_HEIGHT - 10),
                2,
                border_radius=3,
            )  # Inner border
        elif type == "shooter":
            pygame.draw.circle(
                self.image_orig, RED, (ALIEN_WIDTH // 2, ALIEN_HEIGHT // 2), 4
            )  # Red center dot
        else:  # Grunt eyes
            pygame.draw.circle(
                self.image_orig, BLACK, (ALIEN_WIDTH // 3, ALIEN_HEIGHT // 3), 3
            )
            pygame.draw.circle(
                self.image_orig, BLACK, (ALIEN_WIDTH * 2 // 3, ALIEN_HEIGHT // 3), 3
            )

        pygame.draw.line(
            self.image_orig,
            color,
            (ALIEN_WIDTH * 0.2, ALIEN_HEIGHT),
            (ALIEN_WIDTH * 0.4, ALIEN_HEIGHT + 4),
            2,
        )
        pygame.draw.line(
            self.image_orig,
            color,
            (ALIEN_WIDTH * 0.8, ALIEN_HEIGHT),
            (ALIEN_WIDTH * 0.6, ALIEN_HEIGHT + 4),
            2,
        )
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hit_flash_timer = 0

    def update(self, dx=0, dy=0):
        self.rect.x += dx
        self.rect.y += dy

        # Health/Hit flash
        if self.type == "tank" and pygame.time.get_ticks() < self.hit_flash_timer:
            # Simple brightness flash
            flash_image = self.image_orig.copy()
            brightness = 100  # Amount to add
            flash_image.fill(
                (brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_ADD
            )
            self.image = flash_image
        else:
            self.image = self.image_orig.copy()  # Reset

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True  # Alien died
        else:
            # Flash if tank took damage but didn't die
            if self.type == "tank":
                self.hit_flash_timer = pygame.time.get_ticks() + 80  # Flash briefly
            return False  # Alien survived

    def shoot(self):
        # Maybe different bullet types per alien later?
        bullet = Bullet(
            self.rect.centerx, self.rect.bottom, ALIEN_BULLET_SPEED, ALIEN_BULLET_COLOR
        )
        all_sprites.add(bullet)
        alien_bullets.add(bullet)


class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        # ... (original drawing code) ...
        self.image_orig = pygame.Surface([BOSS_WIDTH, BOSS_HEIGHT], pygame.SRCALPHA)
        self.image_orig.set_colorkey(BLACK)
        pygame.draw.rect(
            self.image_orig,
            BOSS_COLOR,
            (0, 10, BOSS_WIDTH, BOSS_HEIGHT - 20),
            border_radius=8,
        )
        pygame.draw.rect(
            self.image_orig,
            BOSS_COLOR,
            (20, 0, BOSS_WIDTH - 40, BOSS_HEIGHT),
            border_radius=8,
        )
        pygame.draw.circle(self.image_orig, RED, (BOSS_WIDTH // 2, BOSS_HEIGHT // 2), 8)
        pygame.draw.polygon(
            self.image_orig,
            BOSS_COLOR,
            [(0, 10), (-10, BOSS_HEIGHT // 2), (0, BOSS_HEIGHT - 10)],
        )
        pygame.draw.polygon(
            self.image_orig,
            BOSS_COLOR,
            [
                (BOSS_WIDTH, 10),
                (BOSS_WIDTH + 10, BOSS_HEIGHT // 2),
                (BOSS_WIDTH, BOSS_HEIGHT - 10),
            ],
        )

        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH // 2, top=ALIEN_TOP_MARGIN)
        self.level = level
        self.health = BOSS_BASE_HEALTH + (level - 1) * 7  # Scale health more
        self.max_health = self.health
        self.speed = BOSS_SPEED + (level - 1) * 0.5  # Scale speed
        self.direction = 1
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_interval = random.randint(500, 900)
        self.hit_flash_timer = 0

        # Pattern state
        self.phase = 1
        self.pattern = "side_to_side"  # 'swooping', 'burst_fire'
        self.pattern_timer = pygame.time.get_ticks()
        self.swoop_start_y = self.rect.y
        self.swoop_direction = 1

    def update(self):
        now = pygame.time.get_ticks()
        self.update_phase()
        self.update_pattern(now)
        self.execute_movement(now)
        self.handle_shooting(now)
        self.handle_flash(now)

    def update_phase(self):
        health_ratio = self.health / self.max_health
        if health_ratio < 0.33 and self.phase < 3:
            self.phase = 3
            print("Boss Phase 3!")
            self.speed *= 1.2  # Speed up more
        elif health_ratio < 0.66 and self.phase < 2:
            self.phase = 2
            print("Boss Phase 2!")
            self.speed *= 1.15  # Speed up

    def update_pattern(self, now):
        # Change pattern periodically or based on phase
        time_since_change = now - self.pattern_timer
        change_interval = 5000 + random.randint(-1000, 1000)  # ~5 seconds

        if time_since_change > change_interval:
            self.pattern_timer = now
            possible_patterns = ["side_to_side"]
            if self.phase >= 2:
                possible_patterns.append("swooping")
            if self.phase >= 3:
                possible_patterns.append(
                    "burst_fire"
                )  # Burst replaces normal shooting temporarily

            # Avoid immediate repeat of swooping/burst
            if len(possible_patterns) > 1 and self.pattern in [
                "swooping",
                "burst_fire",
            ]:
                possible_patterns.remove(self.pattern)

            self.pattern = random.choice(possible_patterns)
            print(f"Boss new pattern: {self.pattern}")

            if self.pattern == "swooping":
                self.swoop_start_y = ALIEN_TOP_MARGIN + 20  # Reset start Y
                self.swoop_direction = 1  # Start going down
            elif self.pattern == "burst_fire":
                # Trigger an immediate burst when pattern starts
                self.shoot(burst=True)
                self.shoot_interval = 1500  # Longer cooldown after burst

    def execute_movement(self, now):
        # Base side-to-side
        self.rect.x += self.speed * self.direction
        if self.rect.right > SCREEN_WIDTH - 10:
            self.rect.right = SCREEN_WIDTH - 10
            self.direction = -1
        elif self.rect.left < 10:
            self.rect.left = 10
            self.direction = 1

        # Swooping modification
        if self.pattern == "swooping":
            self.rect.y += BOSS_SWOOP_SPEED_Y * self.swoop_direction
            if (
                self.swoop_direction == 1
                and self.rect.y > self.swoop_start_y + BOSS_SWOOP_RANGE
            ):
                self.swoop_direction = -1  # Go up
            elif self.swoop_direction == -1 and self.rect.y < self.swoop_start_y:
                self.rect.y = self.swoop_start_y  # Snap back to top
                self.swoop_direction = 1  # Go down next time
                # Maybe end swoop pattern after one cycle?
                # self.pattern = 'side_to_side'
                # self.pattern_timer = now
        else:
            # Gently return to normal height if not swooping
            if self.rect.y > ALIEN_TOP_MARGIN + 5:
                self.rect.y -= 1
            elif self.rect.y < ALIEN_TOP_MARGIN - 5:
                self.rect.y += 1

    def handle_shooting(self, now):
        if (
            self.pattern != "burst_fire"
            and now - self.last_shot_time > self.shoot_interval
        ):
            self.shoot()
            self.last_shot_time = now
            # Adjust interval based on phase
            base_interval = 700 - self.phase * 100
            self.shoot_interval = random.randint(
                max(200, base_interval - 150), base_interval + 150
            )

    def handle_flash(self, now):
        if now < self.hit_flash_timer:
            inv_color = (255 - BOSS_COLOR[0], 255 - BOSS_COLOR[1], 255 - BOSS_COLOR[2])
            flash_surf = self.image_orig.copy()
            pa = pygame.PixelArray(flash_surf)
            pa.replace(BOSS_COLOR, inv_color)
            del pa
            self.image = flash_surf
        else:
            self.image = self.image_orig.copy()

    def shoot(self, burst=False):
        fire_count = 1
        speed = BOSS_BULLET_SPEED
        interval = 0  # Time between burst shots

        if burst:
            fire_count = random.randint(4, 6)
            interval = 80  # ms between burst shots
            print("Boss Burst Fire!")
        else:
            # Standard triple shot
            fire_count = 3
            interval = 0  # Fire simultaneously

        for i in range(fire_count):
            # Use pygame.time.set_timer for delayed shots? Simpler: just create them now.
            # Real delay needs a more complex shooting scheduler.
            if i == 0 or fire_count == 1:  # Center shot
                bullet = Bullet(
                    self.rect.centerx, self.rect.bottom, speed, BOSS_BULLET_COLOR
                )
            elif i % 2 != 0:  # Left alternating
                offset = (i + 1) // 2 * 20
                bullet = Bullet(
                    self.rect.centerx - offset,
                    self.rect.centery,
                    speed,
                    BOSS_BULLET_COLOR,
                )
            else:  # Right alternating
                offset = i // 2 * 20
                bullet = Bullet(
                    self.rect.centerx + offset,
                    self.rect.centery,
                    speed,
                    BOSS_BULLET_COLOR,
                )

            all_sprites.add(bullet)
            boss_bullets.add(bullet)

    def hit(self, damage=1):
        self.health -= damage
        self.hit_flash_timer = pygame.time.get_ticks() + 100
        if self.health <= 0:
            self.kill()  # Remove from all groups


# --- Bullet Class Modified ---
class Bullet(pygame.sprite.Sprite):
    def __init__(
        self, x, y, speed_y, color, dx=0, piercing=False
    ):  # Added dx, piercing
        super().__init__()
        self.image = pygame.Surface([BULLET_WIDTH, BULLET_HEIGHT])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        if speed_y < 0:
            self.rect.bottom = y
        else:
            self.rect.top = y
        self.rect.centerx = x
        self.speed_y = speed_y
        self.speed_x = dx  # Store horizontal speed
        self.piercing = piercing

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x  # Apply horizontal movement
        # Remove if off-screen (consider horizontal bounds too if dx is large)
        if (
            self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT
            or self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
        ):
            self.kill()


# --- PowerUp Class Modified ---
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, centerx, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface([POWERUP_WIDTH, POWERUP_HEIGHT], pygame.SRCALPHA)
        color = POWERUP_COLORS.get(type, WHITE)
        pygame.draw.rect(self.image, color, self.image.get_rect(), border_radius=4)
        # Letter indicator
        p_font = pygame.font.Font(font_name, 18)
        text = "?"
        if type == "rapid_fire":
            text = "R"
        elif type == "shield":
            text = "S"
        elif type == "spread_shot":
            text = "W"  # Wide
        elif type == "pierce_shot":
            text = "P"
        elif type == "extra_life":
            text = "+1"
        text_surf = p_font.render(text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.image.get_rect().center)
        self.image.blit(text_surf, text_rect)

        self.rect = self.image.get_rect(centerx=centerx, bottom=0)

    def update(self):
        self.rect.y += POWERUP_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# --- Game Functions (Mostly unchanged, create_aliens and setup_level modified) ---

# ... (draw_text, draw_lives, draw_boss_health, draw_powerup_timer - unchanged) ...
# ... (show_intro_screen, show_game_over_screen, show_win_screen, show_level_transition - unchanged) ...


def draw_text(surface, text, size, x, y, color=WHITE, align="midtop"):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "midtop":
        text_rect.midtop = (x, y)
    elif align == "topleft":
        text_rect.topleft = (x, y)
    elif align == "topright":
        text_rect.topright = (x, y)
    surface.blit(text_surface, text_rect)


def draw_lives(surface, x, y, lives, img):
    if lives < 0:
        lives = 0
    try:
        if img.get_width() > 0 and img.get_height() > 0:
            life_img_small = pygame.transform.scale(
                img, (PLAYER_WIDTH // 2, (PLAYER_HEIGHT + PLAYER_GUN_HEIGHT) // 2)
            )
            for i in range(lives):
                img_rect = life_img_small.get_rect(
                    topleft=(x + (PLAYER_WIDTH // 2 + 5) * i, y)
                )
                surface.blit(life_img_small, img_rect)
    except Exception as e:
        print(f"Error drawing lives: {e}")
        draw_text(surface, f"Lives: {lives}", 18, x, y, align="topleft")


def draw_boss_health(surface, boss):
    if boss and boss.alive():
        fill = max(0, boss.health / boss.max_health)  # Ensure fill is not negative
        bar_width = 150
        bar_height = 15
        fill_width = int(bar_width * fill)
        outline_rect = pygame.Rect(
            SCREEN_WIDTH - bar_width - 10, 10, bar_width, bar_height
        )
        fill_rect = pygame.Rect(
            SCREEN_WIDTH - bar_width - 10, 10, fill_width, bar_height
        )
        bar_color = GREEN if fill > 0.6 else YELLOW if fill > 0.3 else RED
        pygame.draw.rect(surface, bar_color, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)


def draw_powerup_timer(surface, player):
    if player.powerup_type and player.powerup_type != "extra_life":
        now = pygame.time.get_ticks()
        remaining_time = (player.powerup_end_time - now) / 1000.0
        if remaining_time > 0:
            type_name = player.powerup_type.replace("_", " ").title()
            timer_text = f"{type_name}: {remaining_time:.1f}s"
            draw_text(
                surface,
                timer_text,
                18,
                SCREEN_WIDTH / 2,
                35,
                POWERUP_COLORS.get(player.powerup_type, YELLOW),
            )


# --- (Screens: Intro, Game Over, Win, Level Transition - Same as before) ---
def show_intro_screen():
    screen.fill(DARK_BLUE)
    draw_text(
        screen, "SLEEK INVADERS++", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 - 20, CYAN
    )
    draw_text(
        screen,
        "Arrow Keys / A/D to Move, Space to Shoot",
        20,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 - 50,
    )
    draw_text(
        screen,
        "New Aliens! New Powerups! Tougher Bosses!",
        20,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 - 20,
        YELLOW,
    )
    draw_text(
        screen,
        "W: Spread, P: Pierce, R: Rapid, S: Shield, +1: Life",
        18,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 + 10,
    )
    draw_text(
        screen,
        f"Clear {MAX_LEVELS} levels to Win!",
        18,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 3 / 4 - 10,
    )
    draw_text(
        screen,
        "Press any key to start",
        18,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 3 / 4 + 20,
    )
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS / 4)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                waiting = False


def show_game_over_screen(score):
    # ... (same as before) ...
    screen.fill(DARK_BLUE)
    draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED)
    draw_text(screen, f"Final Score: {score}", 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    draw_text(
        screen,
        "Press [R] to Play Again or [Q] to Quit",
        22,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 3 / 4,
    )
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS / 4)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    waiting = False
                    return True
    return False


def show_win_screen(score):
    # ... (same as before) ...
    screen.fill(DARK_BLUE)
    draw_text(screen, "YOU WIN!", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, GREEN)
    draw_text(screen, f"Final Score: {score}", 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    draw_text(
        screen,
        "Press [R] to Play Again or [Q] to Quit",
        22,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT * 3 / 4,
    )
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS / 4)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    waiting = False
                    return True
    return False


def show_level_transition(level):
    # ... (same as before) ...
    screen.fill(DARK_BLUE)
    draw_text(
        screen, f"LEVEL {level}", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50, WHITE
    )
    pygame.display.flip()
    pygame.time.wait(1500)


# --- Modified Functions ---
def create_aliens(level):
    aliens_group = pygame.sprite.Group()
    rows = ALIEN_ROWS
    cols = ALIEN_COLS
    start_x = (SCREEN_WIDTH - (cols * ALIEN_WIDTH + (cols - 1) * ALIEN_H_SPACE)) // 2

    for r in range(rows):
        alien_type = "grunt"  # Default
        # Assign types based on row (example)
        if r == 0:  # Top row maybe tanks later?
            if level >= 2:
                alien_type = "tank"
        elif r == rows - 1:  # Bottom row shooters?
            alien_type = "shooter"
        elif r == 1 and level >= 3:  # Second row tanks on level 3+
            alien_type = "tank"

        # Randomness factor per level?
        if random.random() < 0.1 * level:  # Small chance to upgrade type
            if alien_type == "grunt":
                alien_type = "shooter"
            elif alien_type == "shooter":
                alien_type = "tank"

        for c in range(cols):
            x = start_x + c * (ALIEN_WIDTH + ALIEN_H_SPACE)
            y = ALIEN_TOP_MARGIN + r * (ALIEN_HEIGHT + ALIEN_V_SPACE)
            alien = Alien(x, y, alien_type, level)
            aliens_group.add(alien)
            all_sprites.add(alien)
    return aliens_group


def setup_level(level):
    global player, aliens, boss, score, alien_direction, alien_timer, alien_move_interval, game_state, current_level

    current_level = level
    all_sprites.empty()
    player_bullets.empty()
    alien_bullets.empty()
    boss_bullets.empty()
    powerups.empty()
    aliens.empty()
    if boss and boss.alive():
        boss.kill()
    boss_group.empty()  # Clear the single group too

    player.rect.centerx = SCREEN_WIDTH // 2
    player.rect.bottom = SCREEN_HEIGHT - 20
    player.hidden = False
    player.image.set_alpha(255)
    # Don't reset powerups between levels? Or reset them? Let's keep them for now.
    # player.deactivate_powerup() # Uncomment to clear powerups between levels
    all_sprites.add(player)

    aliens = create_aliens(level)

    alien_direction = 1
    alien_timer = pygame.time.get_ticks()
    alien_move_interval = max(
        ALIEN_MIN_MOVE_INTERVAL, ALIEN_INITIAL_MOVE_INTERVAL - (level - 1) * 50
    )  # Faster interval scaling
    print(f"Level {level} - Alien Move Interval: {alien_move_interval}")

    game_state = PLAYING_WAVE


# --- Initialization ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sleek Invaders++")
clock = pygame.time.Clock()
font_name = (
    pygame.font.match_font("consolas", True, False) or pygame.font.get_default_font()
)

# --- Sprite Groups ---
all_sprites = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
alien_bullets = pygame.sprite.Group()
boss_bullets = pygame.sprite.Group()
aliens = pygame.sprite.Group()
powerups = pygame.sprite.Group()
boss_group = pygame.sprite.GroupSingle()

# --- Game Variables ---
player = Player()
all_sprites.add(player)
score = 0
current_level = 1
game_state = INTRO
boss = None
alien_direction = 1
alien_timer = 0
alien_move_interval = ALIEN_INITIAL_MOVE_INTERVAL
alien_base_move_speed = ALIEN_BASE_MOVE_SPEED

# --- Game Loop ---
running = True
while running:
    if game_state == INTRO:
        show_intro_screen()
        setup_level(1)
        score = 0
        player.reset_state()

    elif game_state == GAME_OVER:
        if show_game_over_screen(score):
            game_state = INTRO
        else:
            running = False

    elif game_state == PLAYER_WON:
        if show_win_screen(score):
            game_state = INTRO
        else:
            running = False

    # --- Main Game Logic ---
    elif game_state == PLAYING_WAVE or game_state == BOSS_FIGHT:
        # --- Input ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update ---
        all_sprites.update()  # Player, Bullets, Aliens(move=0), Powerups, Boss

        # --- Wave Logic ---
        if game_state == PLAYING_WAVE:
            # Alien Movement (same as before, check game over)
            now = pygame.time.get_ticks()
            # ... (movement code identical to previous version) ...
            move_aliens_this_frame = False
            if now - alien_timer > alien_move_interval:
                move_aliens_this_frame = True
                alien_timer = now

            move_dx, move_dy, max_alien_y = 0, 0, 0
            if move_aliens_this_frame:
                current_move_speed = ALIEN_BASE_MOVE_SPEED
                move_dx = alien_direction * current_move_speed
                boundary_hit = False
                for alien in aliens:
                    next_x = alien.rect.x + move_dx
                    if (
                        next_x + ALIEN_WIDTH > SCREEN_WIDTH and alien_direction > 0
                    ) or (next_x < 0 and alien_direction < 0):
                        boundary_hit = True
                    if alien.rect.bottom > max_alien_y:
                        max_alien_y = alien.rect.bottom

                if boundary_hit:
                    alien_direction *= -1
                    move_dx = 0
                    move_dy = ALIEN_DROP_DISTANCE
                    max_alien_y += move_dy
                else:
                    move_dy = 0

                for alien in aliens:
                    alien.update(move_dx, move_dy)

                if max_alien_y >= player.rect.top and player.lives > 0:
                    print("Aliens reached player!")
                    player.lives = 0
                    game_state = GAME_OVER

            # Alien Shooting (uses alien type modifier)
            base_shoot_chance = ALIEN_BASE_SHOOT_CHANCE * (
                1 + (current_level - 1) * 0.15
            )
            for alien in aliens:
                if random.random() < base_shoot_chance * alien.shoot_chance_mod:
                    alien.shoot()

            # Power-up Spawning (rarer extra life)
            spawn_roll = random.random()
            if spawn_roll < POWERUP_BASE_SPAWN_CHANCE:
                p_type = random.choice(POWERUP_TYPES)
                # Make extra life rarer
                if p_type == "extra_life" and random.random() > POWERUP_LIFE_SPAWN_MOD:
                    # Reroll if extra life failed rarity check
                    p_type = random.choice(
                        [pt for pt in POWERUP_TYPES if pt != "extra_life"]
                    )

                p_x = random.randint(
                    POWERUP_WIDTH // 2, SCREEN_WIDTH - POWERUP_WIDTH // 2
                )
                powerup = PowerUp(p_x, p_type)
                all_sprites.add(powerup)
                powerups.add(powerup)

            # Check Wave Clear -> Boss Fight
            if not aliens:
                print(f"Level {current_level} wave cleared! Boss time!")
                game_state = BOSS_FIGHT
                boss = Boss(current_level)
                all_sprites.add(boss)
                boss_group.add(boss)

        # --- Boss Logic ---
        elif game_state == BOSS_FIGHT:
            # Check Boss Defeated -> Next Level or Win
            if not boss_group and boss and not boss.alive():  # Boss killed itself
                print(f"Level {current_level} Boss defeated!")
                score += 100 * current_level
                player.deactivate_powerup()  # Clear powerups after boss for fresh start? Optional.
                if current_level >= MAX_LEVELS:
                    game_state = PLAYER_WON
                else:
                    next_level = current_level + 1
                    show_level_transition(next_level)
                    setup_level(next_level)  # Sets state back to PLAYING_WAVE

        # --- Shared Collision Logic ---
        # Player Bullets vs Aliens (Manual check for health/piercing)
        for bullet in player_bullets:
            aliens_hit = pygame.sprite.spritecollide(
                bullet, aliens, False
            )  # Don't kill aliens yet
            for alien in aliens_hit:
                if alien.hit():  # hit() returns True if alien died
                    score += 10
                # Only kill bullet if it's not piercing OR it hit a tank (stops on tanks?)
                # Let's allow piercing through tanks too for now.
                if not bullet.piercing:
                    bullet.kill()
                    break  # Bullet is gone, check next bullet

        # Player Bullets vs Boss
        if boss and boss.alive():
            boss_hits = pygame.sprite.spritecollide(
                boss, player_bullets, not player.piercing
            )  # Kill bullets unless piercing
            for _ in boss_hits:  # Iterate through hits (even if bullet wasn't killed)
                boss.hit()
                score += 5
                # If piercing, the same bullet might register multiple hits if it stays on the boss

        # Alien/Boss Bullets vs Player
        bullets_to_check = pygame.sprite.Group(alien_bullets, boss_bullets)
        if not player.hidden:
            player_hits = pygame.sprite.spritecollide(
                player, bullets_to_check, True
            )  # Kill bullets
            if player_hits:
                if player.hide():  # Returns True if player took damage (not shielded)
                    player.lives -= 1
                    if player.lives <= 0:
                        game_state = GAME_OVER

        # Player vs Powerups
        powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
        for p_hit in powerup_hits:
            player.activate_powerup(p_hit.type)

    # --- Draw ---
    screen.fill(DARK_BLUE)
    # ... (Star drawing same as before) ...
    for _ in range(40):
        star_x = random.randrange(SCREEN_WIDTH)
        star_y = random.randrange(SCREEN_HEIGHT)
        star_b = random.randint(60, 160)
        star_s = random.choice([1, 1, 2])
        pygame.draw.circle(screen, (star_b, star_b, star_b), (star_x, star_y), star_s)

    all_sprites.draw(screen)
    # UI Drawing (Score, Level, Lives, Powerup Timer, Boss Health)
    draw_text(screen, f"SCORE: {score}", 20, SCREEN_WIDTH / 2, 10, WHITE)
    draw_text(screen, f"LEVEL: {current_level}", 20, 10, 10, WHITE, align="topleft")
    if player:
        draw_lives(screen, 10, 35, player.lives, player.image_orig)
    draw_powerup_timer(screen, player)
    if game_state == BOSS_FIGHT:
        draw_boss_health(screen, boss)

    pygame.display.flip()
    clock.tick(FPS)

# --- Quit ---
pygame.quit()
sys.exit()
