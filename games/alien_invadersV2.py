import pygame
import random
import sys
import math
import time

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Game States
INTRO = 0
ENDLESS_PLAY = 1
BOSS_ACTIVE = 2
GAME_OVER = 3

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
LIGHT_GREEN = (150, 255, 150)
BRIGHT_RED = (255, 0, 0)  # For Laser
LIGHT_BLUE = (100, 150, 255)  # For Triple Shot
DARK_GREEN = (0, 100, 0)  # For Homing Missile

# Player Settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 20
PLAYER_SPEED_X = 6
PLAYER_SPEED_Y = 4
PLAYER_COLOR = CYAN
PLAYER_GUN_HEIGHT = 5
PLAYER_INITIAL_LIVES = 3
PLAYER_Y_LIMIT_TOP = SCREEN_HEIGHT * 0.6

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
LASER_BULLET_SPEED = 15
LASER_BULLET_COLOR = BRIGHT_RED
LASER_BULLET_HEIGHT = 18
LASER_BULLET_WIDTH = 5

# Missile Settings
MISSILE_SPEED = 7
MISSILE_TURN_RATE = 5  # Degrees per frame
MISSILE_LIFETIME = 3000  # ms
MISSILE_WIDTH = 8
MISSILE_HEIGHT = 16
MISSILE_COLOR = DARK_GREEN

# --- Weapon Type Constants ---
WEAPON_STANDARD = "standard"
WEAPON_SPREAD = "spread_shot"
WEAPON_TRIPLE = "triple_shot"
WEAPON_LASER = "laser_shot"
WEAPON_HOMING = "homing_missile"

# --- Endless Mode Settings ---
INITIAL_ALIEN_SPAWN_RATE = 1.0  # Seconds between spawns initially
MIN_ALIEN_SPAWN_RATE = 0.2  # Fastest spawn rate
SPAWN_RATE_DECREASE_PER_BOSS = 0.1  # How much spawn rate decreases
INITIAL_ALIEN_SPEED = 1.5
MAX_ALIEN_SPEED = 4.0
ALIEN_SPEED_INCREASE_PER_BOSS = 0.25
ALIEN_SHOOT_CHANCE_INCREASE_PER_BOSS = 0.0005  # Increase base shoot chance
# --- Corrected: Added missing constants ---
BOSS_SCORE_THRESHOLD_BASE = 500
BOSS_SCORE_THRESHOLD_INCREMENT = 750  # Score needed for next boss increases
# --- End Correction ---

# Alien Settings
ALIEN_WIDTH = 35
ALIEN_HEIGHT = 25
ALIEN_TANK_HEALTH = 3
ALIEN_BASE_SHOOT_CHANCE = 0.0015
ALIEN_SHOOTER_MULTIPLIER = 3.0

# Boss Settings
BOSS_WIDTH = 100
BOSS_HEIGHT = 50
BOSS_BASE_HEALTH = 30
BOSS_HEALTH_INCREMENT_PER_BOSS = 15
BOSS_SPEED_BASE = 2.5
BOSS_SPEED_INCREMENT_PER_BOSS = 0.3
BOSS_SHOOT_CHANCE = 0.025
BOSS_COLOR = PURPLE
BOSS_SWOOP_SPEED_Y = 2
BOSS_SWOOP_RANGE = 100
BOSS_LASER_CHARGE_TIME = 1500  # ms
BOSS_LASER_DURATION = 500  # ms
BOSS_LASER_WIDTH = 15
BOSS_LASER_COLOR = RED
BOSS_MINION_SPAWN_COUNT = 3
BOSS_TELEPORT_COOLDOWN = 6000  # ms

# Power-up Settings
POWERUP_WIDTH = 25
POWERUP_HEIGHT = 25
POWERUP_SPEED = 3
POWERUP_BASE_SPAWN_CHANCE = 0.0012
POWERUP_LIFE_SPAWN_MOD = 0.2
POWERUP_DURATION = 15000  # Duration for timed effects (shield, rapid)

POWERUP_TIMED_EFFECTS = ["rapid_fire", "shield", "extra_life"]
POWERUP_WEAPONS = [WEAPON_SPREAD, WEAPON_TRIPLE, WEAPON_LASER, WEAPON_HOMING]
ALL_POWERUP_TYPES = POWERUP_TIMED_EFFECTS + POWERUP_WEAPONS

POWERUP_COLORS = {
    # Timed Effects
    "rapid_fire": YELLOW,
    "shield": BLUE,
    "extra_life": LIGHT_GREEN,
    # Weapons (Gifts)
    WEAPON_SPREAD: ORANGE,
    WEAPON_TRIPLE: LIGHT_BLUE,
    WEAPON_LASER: BRIGHT_RED,
    WEAPON_HOMING: DARK_GREEN,
}

# --- Classes ---


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_orig = pygame.Surface(
            [PLAYER_WIDTH, PLAYER_HEIGHT + PLAYER_GUN_HEIGHT], pygame.SRCALPHA
        )
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
        self.speed_y = 0
        self.lives = PLAYER_INITIAL_LIVES
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

        self.active_weapon = WEAPON_STANDARD
        self.timed_effect_type = None
        self.timed_effect_end_time = 0

        self.last_shot_time = 0
        self.shoot_cooldown = PLAYER_BASE_COOLDOWN

    def update(self):
        now = pygame.time.get_ticks()
        self.handle_timed_effects(now)
        self.handle_invincibility(now)

        if self.hidden:
            return

        self.handle_movement()
        self.handle_shooting(now)

    def handle_timed_effects(self, now):
        if (
            self.timed_effect_type
            and self.timed_effect_type != "extra_life"
            and now > self.timed_effect_end_time
        ):
            self.deactivate_timed_effect()

        self.shoot_cooldown = (
            PLAYER_RAPID_COOLDOWN
            if self.timed_effect_type == "rapid_fire"
            else PLAYER_BASE_COOLDOWN
        )

        if self.timed_effect_type == "shield":
            self.image = self.image_orig.copy()
            shield_rect = self.image.get_rect().inflate(8, 8)
            alpha = 150 + math.sin(now * 0.01) * 100
            shield_color_alpha = (*BLUE, int(max(0, min(255, alpha))))
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
        elif not self.hidden:
            self.image = self.image_orig.copy()

    def handle_invincibility(self, now):
        if self.hidden and now - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2
            self.rect.bottom = SCREEN_HEIGHT - 20
            self.image.set_alpha(255)

        if self.hidden:
            visible = (now // 100) % 2 == 0
            self.image.set_alpha(255 if visible else 0)

    def handle_movement(self):
        self.speed_x = 0
        self.speed_y = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT] or keystate[pygame.K_a]:
            self.speed_x = -PLAYER_SPEED_X
        if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
            self.speed_x = PLAYER_SPEED_X
        if keystate[pygame.K_UP] or keystate[pygame.K_w]:
            self.speed_y = -PLAYER_SPEED_Y
        if keystate[pygame.K_DOWN] or keystate[pygame.K_s]:
            self.speed_y = PLAYER_SPEED_Y

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(PLAYER_Y_LIMIT_TOP, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

    def handle_shooting(self, now):
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_SPACE] and now - self.last_shot_time > self.shoot_cooldown:
            self.shoot()
            self.last_shot_time = now

    def shoot(self):
        if self.hidden:
            return

        center_x, top_y = self.rect.centerx, self.rect.top

        if self.active_weapon == WEAPON_STANDARD:
            bullet = Bullet(
                center_x,
                top_y,
                -PLAYER_BULLET_SPEED,
                PLAYER_BULLET_COLOR,
                piercing=False,
            )
            all_sprites.add(bullet)
            player_bullets.add(bullet)

        elif self.active_weapon == WEAPON_SPREAD:
            b1 = Bullet(
                center_x,
                top_y,
                -PLAYER_BULLET_SPEED * 1.1,
                PLAYER_BULLET_COLOR,
                dx=0,
                piercing=False,
            )
            b2 = Bullet(
                center_x - 8,
                top_y + 5,
                -PLAYER_BULLET_SPEED * 0.9,
                PLAYER_BULLET_COLOR,
                dx=-3,
                piercing=False,
            )
            b3 = Bullet(
                center_x + 8,
                top_y + 5,
                -PLAYER_BULLET_SPEED * 0.9,
                PLAYER_BULLET_COLOR,
                dx=3,
                piercing=False,
            )
            all_sprites.add(b1, b2, b3)
            player_bullets.add(b1, b2, b3)

        elif self.active_weapon == WEAPON_TRIPLE:
            offset = PLAYER_WIDTH // 4
            b1 = Bullet(
                center_x,
                top_y,
                -PLAYER_BULLET_SPEED,
                PLAYER_BULLET_COLOR,
                piercing=False,
            )
            b2 = Bullet(
                center_x - offset,
                top_y,
                -PLAYER_BULLET_SPEED,
                PLAYER_BULLET_COLOR,
                piercing=False,
            )
            b3 = Bullet(
                center_x + offset,
                top_y,
                -PLAYER_BULLET_SPEED,
                PLAYER_BULLET_COLOR,
                piercing=False,
            )
            all_sprites.add(b1, b2, b3)
            player_bullets.add(b1, b2, b3)

        elif self.active_weapon == WEAPON_LASER:
            laser = Bullet(
                center_x, top_y, -LASER_BULLET_SPEED, LASER_BULLET_COLOR, piercing=True
            )
            laser.image = pygame.Surface([LASER_BULLET_WIDTH, LASER_BULLET_HEIGHT])
            laser.image.fill(LASER_BULLET_COLOR)
            laser.rect = laser.image.get_rect(centerx=center_x, bottom=top_y)
            all_sprites.add(laser)
            player_bullets.add(laser)

        elif self.active_weapon == WEAPON_HOMING:
            missile = Missile(center_x, top_y, aliens)
            all_sprites.add(missile)
            player_bullets.add(missile)

    def activate_powerup(self, type):
        if type == "extra_life":
            print("Activated powerup: Extra Life!")
            self.lives += 1
        elif type in POWERUP_WEAPONS:
            self.set_weapon(type)
            if self.timed_effect_type:
                self.deactivate_timed_effect()
        elif type in POWERUP_TIMED_EFFECTS:
            self.activate_timed_effect(type)

    def set_weapon(self, weapon_type):
        if self.active_weapon != weapon_type:
            print(f"Activated weapon: {weapon_type}")
            self.active_weapon = weapon_type

    def activate_timed_effect(self, effect_type):
        if self.timed_effect_type == effect_type:
            print(f"Refreshed effect: {effect_type}")
            self.timed_effect_end_time = pygame.time.get_ticks() + POWERUP_DURATION
        else:
            if self.timed_effect_type and self.timed_effect_type != "extra_life":
                self.deactivate_timed_effect()
            print(f"Activated effect: {effect_type}")
            self.timed_effect_type = effect_type
            self.timed_effect_end_time = pygame.time.get_ticks() + POWERUP_DURATION

    def deactivate_timed_effect(self):
        if self.timed_effect_type and self.timed_effect_type != "extra_life":
            print(f"Deactivated effect: {self.timed_effect_type}")
            if self.timed_effect_type == "rapid_fire":
                self.shoot_cooldown = PLAYER_BASE_COOLDOWN
            elif self.timed_effect_type == "shield":
                if not self.hidden:
                    self.image = self.image_orig.copy()
            self.timed_effect_type = None
            self.timed_effect_end_time = 0

    def hide(self):
        if self.timed_effect_type == "shield":
            print("Shield protected player!")
            self.deactivate_timed_effect()
            return False

        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT + 200)
        self.active_weapon = WEAPON_STANDARD
        self.deactivate_timed_effect()
        return True

    def reset_state(self):
        self.lives = PLAYER_INITIAL_LIVES
        self.hidden = False
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.image.set_alpha(255)
        self.active_weapon = WEAPON_STANDARD
        self.deactivate_timed_effect()


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, type, speed_y, shoot_mod):
        super().__init__()
        self.type = type
        self.health = 1
        self.shoot_chance_mod = shoot_mod
        color = MAGENTA

        if type == "shooter":
            color = ORANGE
        elif type == "tank":
            color = PURPLE
            self.health = ALIEN_TANK_HEALTH

        self.max_health = self.health
        self.speed_y = speed_y
        self.image_orig = pygame.Surface(
            [ALIEN_WIDTH, ALIEN_HEIGHT + 4], pygame.SRCALPHA
        )
        self.image_orig.set_colorkey(BLACK)
        pygame.draw.rect(
            self.image_orig, color, (0, 0, ALIEN_WIDTH, ALIEN_HEIGHT), border_radius=5
        )
        if type == "tank":
            pygame.draw.rect(
                self.image_orig,
                WHITE,
                (5, 5, ALIEN_WIDTH - 10, ALIEN_HEIGHT - 10),
                2,
                border_radius=3,
            )
        elif type == "shooter":
            pygame.draw.circle(
                self.image_orig, RED, (ALIEN_WIDTH // 2, ALIEN_HEIGHT // 2), 4
            )
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
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.hit_flash_timer = 0

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT + 10:
            self.kill()

        if self.type == "tank" and pygame.time.get_ticks() < self.hit_flash_timer:
            flash_image = self.image_orig.copy()
            brightness = 100
            flash_image.fill(
                (brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_ADD
            )
            self.image = flash_image
        else:
            self.image = self.image_orig.copy()

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            if random.random() < game_vars["powerup_spawn_chance"]:
                spawn_powerup(self.rect.centerx)
            self.kill()
            return True
        else:
            if self.type == "tank":
                self.hit_flash_timer = pygame.time.get_ticks() + 80
            return False

    def shoot(self):
        bullet = Bullet(
            self.rect.centerx, self.rect.bottom, ALIEN_BULLET_SPEED, ALIEN_BULLET_COLOR
        )
        all_sprites.add(bullet)
        alien_bullets.add(bullet)


class Boss(pygame.sprite.Sprite):
    def __init__(self, boss_number):
        super().__init__()
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
        self.rect = self.image.get_rect(
            centerx=SCREEN_WIDTH // 2, top=ALIEN_HEIGHT + 20
        )
        self.boss_number = boss_number

        self.health = (
            BOSS_BASE_HEALTH + (boss_number - 1) * BOSS_HEALTH_INCREMENT_PER_BOSS
        )
        self.max_health = self.health
        self.speed = BOSS_SPEED_BASE + (boss_number - 1) * BOSS_SPEED_INCREMENT_PER_BOSS
        print(
            f"Boss #{boss_number} spawned! Health: {self.health}, Speed: {self.speed:.2f}"
        )

        self.direction = 1
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_interval = random.randint(600, 1000)
        self.hit_flash_timer = 0

        self.phase = 1
        self.pattern = "side_to_side"
        self.pattern_timer = pygame.time.get_ticks()
        self.ability_timer = 0
        self.swoop_start_y = self.rect.y
        self.swoop_direction = 1
        self.teleport_timer = pygame.time.get_ticks()
        self.target_teleport_pos = None
        self.laser_target_x = SCREEN_WIDTH // 2

    def update(self):
        now = pygame.time.get_ticks()
        self.update_phase()
        self.update_pattern(now)
        self.execute_movement_and_abilities(now)
        self.handle_shooting(now)
        self.handle_flash(now)

    def update_phase(self):
        health_ratio = self.health / self.max_health
        if health_ratio < 0.33 and self.phase < 3:
            self.phase = 3
            print("Boss Phase 3!")
            self.speed *= 1.15
        elif health_ratio < 0.66 and self.phase < 2:
            self.phase = 2
            print("Boss Phase 2!")
            self.speed *= 1.1

    def update_pattern(self, now):
        time_since_change = now - self.pattern_timer
        change_interval = max(
            3500, 7000 - (self.boss_number - 1) * 500
        ) + random.randint(-500, 500)

        if self.pattern in ["laser_fire", "teleporting"]:
            return

        if time_since_change > change_interval:
            self.pattern_timer = now
            possible_patterns = ["side_to_side"]
            if self.phase >= 1:
                possible_patterns.append("swooping")
            if self.phase >= 2 or self.boss_number >= 2:
                possible_patterns.append("laser_charge")
            if self.phase >= 2 or self.boss_number >= 3:
                possible_patterns.append("minion_spawn")
            if self.phase >= 3 or self.boss_number >= 4:
                possible_patterns.append("teleport_charge")

            if len(possible_patterns) > 1 and self.pattern in [
                "swooping",
                "laser_charge",
                "minion_spawn",
                "teleport_charge",
            ]:
                try:
                    possible_patterns.remove(self.pattern)
                except ValueError:
                    pass

            self.pattern = random.choice(possible_patterns)
            print(f"Boss new pattern: {self.pattern}")

            if self.pattern == "swooping":
                self.swoop_start_y = self.rect.centery
                self.swoop_direction = 1
            elif self.pattern == "laser_charge":
                self.ability_timer = now + BOSS_LASER_CHARGE_TIME
                if (
                    player and player.alive()
                ):  # Ensure player exists before accessing rect
                    self.laser_target_x = player.rect.centerx
                else:
                    self.laser_target_x = (
                        SCREEN_WIDTH // 2
                    )  # Default target if player dead
                print("Charging Laser!")
            elif self.pattern == "minion_spawn":
                self.spawn_minions()
                self.pattern = "side_to_side"
                self.pattern_timer = now
            elif self.pattern == "teleport_charge":
                if now - self.teleport_timer > BOSS_TELEPORT_COOLDOWN:
                    self.ability_timer = now + 500
                    print("Charging Teleport!")
                else:
                    self.pattern = "side_to_side"
                    self.pattern_timer = now

    def execute_movement_and_abilities(self, now):
        if self.pattern not in ["laser_charge", "laser_fire", "teleporting"]:
            self.rect.x += self.speed * self.direction
            if self.rect.right > SCREEN_WIDTH - 10:
                self.rect.right = SCREEN_WIDTH - 10
                self.direction = -1
            elif self.rect.left < 10:
                self.rect.left = 10
                self.direction = 1

        if self.pattern == "swooping":
            self.rect.y += BOSS_SWOOP_SPEED_Y * self.swoop_direction
            if (
                self.swoop_direction == 1
                and self.rect.centery > self.swoop_start_y + BOSS_SWOOP_RANGE
            ):
                self.swoop_direction = -1
            elif self.swoop_direction == -1 and self.rect.centery < self.swoop_start_y:
                self.rect.centery = self.swoop_start_y
                self.pattern = "side_to_side"
                self.pattern_timer = now
        elif self.pattern == "laser_charge":
            self.rect.x += self.speed * self.direction * 0.3
            if now > self.ability_timer:
                self.pattern = "laser_fire"
                self.ability_timer = now + BOSS_LASER_DURATION
                self.fire_laser()
        elif self.pattern == "laser_fire":
            if now > self.ability_timer:
                self.pattern = "side_to_side"
                self.pattern_timer = now
                for sprite in boss_bullets:
                    if hasattr(sprite, "is_laser") and sprite.is_laser:
                        sprite.kill()
        elif self.pattern == "teleport_charge":
            if now > self.ability_timer:
                self.pattern = "teleporting"
                new_x = random.randint(
                    BOSS_WIDTH // 2 + 20, SCREEN_WIDTH - BOSS_WIDTH // 2 - 20
                )
                new_y = random.randint(ALIEN_HEIGHT + 20, SCREEN_HEIGHT // 3)
                self.target_teleport_pos = (new_x, new_y)
                self.image.set_alpha(0)
                self.ability_timer = now + 300
        elif self.pattern == "teleporting":
            if now > self.ability_timer:
                if self.target_teleport_pos:  # Ensure target pos exists
                    self.rect.center = self.target_teleport_pos
                self.image.set_alpha(255)
                self.pattern = "side_to_side"
                self.pattern_timer = now
                self.teleport_timer = now
        else:
            base_y = ALIEN_HEIGHT + 20
            if self.rect.top > base_y + 5:
                self.rect.y -= 1
            elif self.rect.top < base_y - 5:
                self.rect.y += 1

    def handle_shooting(self, now):
        allowed_to_shoot = self.pattern not in [
            "laser_charge",
            "laser_fire",
            "teleport_charge",
            "teleporting",
        ]
        if allowed_to_shoot and now - self.last_shot_time > self.shoot_interval:
            self.shoot()
            self.last_shot_time = now
            base_interval = max(
                250, 800 - self.phase * 50 - (self.boss_number - 1) * 40
            )
            self.shoot_interval = random.randint(
                base_interval - 100, base_interval + 100
            )

    def handle_flash(self, now):
        if now < self.hit_flash_timer:
            inv_color = (255 - BOSS_COLOR[0], 255 - BOSS_COLOR[1], 255 - BOSS_COLOR[2])
            flash_surf = self.image_orig.copy()
            try:
                pa = pygame.PixelArray(flash_surf)
                pa.replace(BOSS_COLOR, inv_color)
                del pa
                self.image = flash_surf
            except Exception as e:
                brightness = 150
                alt_flash = self.image_orig.copy()
                alt_flash.fill(
                    (brightness, brightness, brightness),
                    special_flags=pygame.BLEND_RGB_ADD,
                )
                self.image = alt_flash
        elif self.pattern == "laser_charge":
            charge_progress = (self.ability_timer - now) / BOSS_LASER_CHARGE_TIME
            radius = (
                8 + max(0, (1.0 - charge_progress)) * 10
            )  # Ensure radius doesn't go negative
            temp_img = self.image_orig.copy()
            pygame.draw.circle(
                temp_img, RED, (BOSS_WIDTH // 2, BOSS_HEIGHT // 2), int(radius)
            )
            self.image = temp_img
        elif self.pattern == "teleport_charge":
            visible = (now // 50) % 2 == 0
            self.image.set_alpha(255 if visible else 100)
        elif self.pattern == "teleporting":
            self.image.set_alpha(0)
        else:
            self.image.set_alpha(255)
            self.image = self.image_orig.copy()

    def shoot(self):
        angle_spread = 5 + self.phase * 5
        b1 = Bullet(
            self.rect.centerx, self.rect.bottom, BOSS_BULLET_SPEED, BOSS_BULLET_COLOR
        )
        rad_l = math.radians(-angle_spread)
        dx_l = math.sin(rad_l) * BOSS_BULLET_SPEED * 0.5
        dy_l = math.cos(rad_l) * BOSS_BULLET_SPEED
        b2 = Bullet(
            self.rect.centerx - 15, self.rect.centery, dy_l, BOSS_BULLET_COLOR, dx=dx_l
        )
        rad_r = math.radians(angle_spread)
        dx_r = math.sin(rad_r) * BOSS_BULLET_SPEED * 0.5
        dy_r = math.cos(rad_r) * BOSS_BULLET_SPEED
        b3 = Bullet(
            self.rect.centerx + 15, self.rect.centery, dy_r, BOSS_BULLET_COLOR, dx=dx_r
        )
        all_sprites.add(b1, b2, b3)
        boss_bullets.add(b1, b2, b3)

    def fire_laser(self):
        print("Firing Laser!")
        laser_height = SCREEN_HEIGHT - self.rect.bottom
        laser_rect = pygame.Rect(0, self.rect.bottom, BOSS_LASER_WIDTH, laser_height)
        laser_rect.centerx = self.laser_target_x
        laser_surf = pygame.Surface(laser_rect.size, pygame.SRCALPHA)
        inner_rect = laser_rect.inflate(-BOSS_LASER_WIDTH * 0.4, 0)
        pygame.draw.rect(
            laser_surf, (255, 100, 100), laser_surf.get_rect(), border_radius=3
        )
        pygame.draw.rect(
            laser_surf,
            (255, 255, 255),
            inner_rect.move(-laser_rect.left, -laser_rect.top),
            border_radius=2,
        )
        laser_sprite = pygame.sprite.Sprite()
        laser_sprite.image = laser_surf
        laser_sprite.rect = laser_rect
        laser_sprite.is_laser = True
        all_sprites.add(laser_sprite)
        boss_bullets.add(laser_sprite)

    def spawn_minions(self):
        print("Spawning Minions!")
        count = BOSS_MINION_SPAWN_COUNT + (self.boss_number // 2)
        for i in range(count):
            offset_x = random.randint(-BOSS_WIDTH, BOSS_WIDTH)
            offset_y = random.randint(20, 50)
            minion_x = self.rect.centerx + offset_x
            minion_y = self.rect.bottom + offset_y
            minion_speed = max(
                1.0, game_vars.get("current_alien_speed", INITIAL_ALIEN_SPEED) * 0.7
            )
            m_type = random.choice(["grunt", "grunt", "shooter"])
            m_shoot_mod = ALIEN_SHOOTER_MULTIPLIER if m_type == "shooter" else 1.0
            minion = Alien(minion_x, minion_y, m_type, minion_speed, m_shoot_mod)
            all_sprites.add(minion)
            aliens.add(minion)

    def hit(self, damage=1):
        self.health -= damage
        self.hit_flash_timer = pygame.time.get_ticks() + 100
        if self.health <= 0:
            self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_y, color, dx=0, piercing=False):
        super().__init__()
        self.is_laser = False
        width = BULLET_WIDTH
        height = BULLET_HEIGHT
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        if speed_y < 0:
            self.rect.bottom = y
        else:
            self.rect.top = y
        self.rect.centerx = x
        self.speed_y = speed_y
        self.speed_x = dx
        self.piercing = piercing

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        if (
            self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT
            or self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
        ):
            self.kill()


class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_group):
        super().__init__()
        self.image_orig = pygame.Surface(
            [MISSILE_WIDTH, MISSILE_HEIGHT], pygame.SRCALPHA
        )
        pygame.draw.polygon(
            self.image_orig,
            MISSILE_COLOR,
            [
                (0, MISSILE_HEIGHT),
                (MISSILE_WIDTH / 2, 0),
                (MISSILE_WIDTH, MISSILE_HEIGHT),
            ],
        )
        pygame.draw.rect(
            self.image_orig, RED, (MISSILE_WIDTH / 2 - 1, MISSILE_HEIGHT - 3, 2, 3)
        )

        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.pos = pygame.Vector2(self.rect.center)
        self.vel = pygame.Vector2(0, -MISSILE_SPEED)
        self.target_group = target_group
        self.target = None
        self.turn_rate = (
            MISSILE_TURN_RATE  # Degrees per frame (use directly with rotate_ip)
        )
        self.spawn_time = pygame.time.get_ticks()
        self.find_target()

    def find_target(self):
        closest_dist_sq = float("inf")
        closest_alien = None
        for alien in self.target_group:
            if alien.alive():
                dist_sq = (
                    pygame.Vector2(alien.rect.center) - self.pos
                ).length_squared()
                if dist_sq < closest_dist_sq:
                    closest_dist_sq = dist_sq
                    closest_alien = alien
        self.target = closest_alien

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > MISSILE_LIFETIME:
            self.kill()
            return

        if self.target and not self.target.alive():
            self.target = None

        if not self.target:
            self.find_target()

        if self.target:
            target_vec = pygame.Vector2(self.target.rect.center) - self.pos
            target_dist = target_vec.length()

            if target_dist > 0:  # Avoid division by zero
                target_dir = target_vec.normalize()
                current_dir = self.vel.normalize()

                # Calculate angle difference
                dot_product = current_dir.dot(target_dir)
                dot_product = max(-1.0, min(1.0, dot_product))  # Clamp for safety
                angle_diff = math.degrees(math.acos(dot_product))

                # Determine rotation direction using cross product (in 2D)
                cross_product = (
                    current_dir.x * target_dir.y - current_dir.y * target_dir.x
                )
                turn_amount = min(angle_diff, self.turn_rate)  # Limit turn speed

                if cross_product < 0:  # Target is to the right (clockwise)
                    self.vel.rotate_ip(turn_amount)
                elif cross_product > 0:  # Target is to the left (counter-clockwise)
                    self.vel.rotate_ip(-turn_amount)

                # Ensure speed is constant after rotation
                self.vel.scale_to_length(MISSILE_SPEED)

        self.pos += self.vel
        self.rect.center = self.pos

        angle = self.vel.angle_to(pygame.Vector2(0, -1))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        if not screen.get_rect().colliderect(self.rect):
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, centerx, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface([POWERUP_WIDTH, POWERUP_HEIGHT], pygame.SRCALPHA)
        color = POWERUP_COLORS.get(type, WHITE)
        pygame.draw.rect(self.image, color, self.image.get_rect(), border_radius=4)

        p_font = pygame.font.Font(font_name, 18)
        text = "?"
        if type == "rapid_fire":
            text = "R"
        elif type == "shield":
            text = "S"
        elif type == "extra_life":
            text = "+1"
        elif type == WEAPON_SPREAD:
            text = "W"
        elif type == WEAPON_TRIPLE:
            text = "T"
        elif type == WEAPON_LASER:
            text = "L"
        elif type == WEAPON_HOMING:
            text = "H"

        text_surf = p_font.render(text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.image.get_rect().center)
        self.image.blit(text_surf, text_rect)

        self.rect = self.image.get_rect(centerx=centerx, bottom=0)

    def update(self):
        self.rect.y += POWERUP_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# --- Game Functions ---


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
    elif align == "center":
        text_rect.center = (x, y)
    surface.blit(text_surface, text_rect)


def draw_lives(surface, x, y, lives, img):
    if lives < 0:
        lives = 0
    try:
        if img and img.get_width() > 0 and img.get_height() > 0:
            life_img_small = pygame.transform.scale(
                img, (PLAYER_WIDTH // 2, (PLAYER_HEIGHT + PLAYER_GUN_HEIGHT) // 2)
            )
            for i in range(lives):
                img_rect = life_img_small.get_rect(
                    topleft=(x + (PLAYER_WIDTH // 2 + 5) * i, y)
                )
                surface.blit(life_img_small, img_rect)
        else:
            draw_text(surface, f"L: {lives}", 18, x, y, align="topleft")
    except Exception as e:
        draw_text(surface, f"L: {lives}", 18, x, y, align="topleft")


def draw_boss_health(surface, boss):
    if boss and boss.alive():
        fill = max(0, boss.health / boss.max_health)
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
        draw_text(
            surface,
            f"BOSS #{boss.boss_number}",
            14,
            SCREEN_WIDTH - bar_width / 2 - 10,
            28,
            WHITE,
        )


def draw_hud(surface, player):
    w_name = player.active_weapon.replace("_", " ").title()
    w_color = POWERUP_COLORS.get(player.active_weapon, WHITE)  # Get color for weapon
    draw_text(surface, f"WPN: {w_name}", 18, SCREEN_WIDTH / 2, 10, w_color)

    if player.timed_effect_type and player.timed_effect_type != "extra_life":
        now = pygame.time.get_ticks()
        remaining_time = (player.timed_effect_end_time - now) / 1000.0
        if remaining_time > 0:
            type_name = player.timed_effect_type.replace("_", " ").title()
            e_color = POWERUP_COLORS.get(
                player.timed_effect_type, YELLOW
            )  # Color for effect
            timer_text = f"{type_name}: {remaining_time:.1f}s"
            draw_text(surface, timer_text, 18, SCREEN_WIDTH / 2, 35, e_color)


def show_intro_screen():
    screen.fill(DARK_BLUE)
    draw_text(
        screen,
        "ENDLESS INVADERS: Weapons!",
        64,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 4 - 30,
        CYAN,
    )
    draw_text(
        screen,
        "Arrow Keys / WASD to Move, Space to Shoot",
        18,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 - 70,
    )
    draw_text(
        screen, "Collect Gifts!", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40, YELLOW
    )
    draw_text(
        screen,
        "Weapons (Permanent): W:Spread T:Triple L:Laser H:Homing",
        16,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 - 15,
    )
    draw_text(
        screen,
        "Effects (Timed):   R:Rapid Fire S:Shield +1:Life",
        16,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 + 5,
    )
    draw_text(
        screen,
        "Survive waves and defeat bosses!",
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


def show_game_over_screen(score, bosses_defeated):
    screen.fill(DARK_BLUE)
    draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED)
    draw_text(
        screen, f"Final Score: {score}", 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20
    )
    draw_text(
        screen,
        f"Bosses Defeated: {bosses_defeated}",
        26,
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2 + 20,
        YELLOW,
    )
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


def spawn_alien():
    now = pygame.time.get_ticks()
    spawn_interval_ms = (
        game_vars.get("current_alien_spawn_interval", INITIAL_ALIEN_SPAWN_RATE) * 1000
    )
    if now - game_vars.get("last_alien_spawn_time", 0) > spawn_interval_ms:
        game_vars["last_alien_spawn_time"] = now

        boss_factor = game_vars.get("bosses_defeated", 0) * 0.05
        grunt_chance = 0.6 - boss_factor
        shooter_chance = 0.3 + boss_factor * 0.5
        tank_chance = 0.1 + boss_factor * 0.5
        total_chance = max(
            0.1, grunt_chance + shooter_chance + tank_chance
        )  # Ensure total chance > 0
        roll = random.random() * total_chance

        if roll < grunt_chance:
            a_type = "grunt"
            a_shoot_mod = 1.0
        elif roll < grunt_chance + shooter_chance:
            a_type = "shooter"
            a_shoot_mod = ALIEN_SHOOTER_MULTIPLIER
        else:
            a_type = "tank"
            a_shoot_mod = 0.5

        x = random.randint(ALIEN_WIDTH // 2, SCREEN_WIDTH - ALIEN_WIDTH // 2)
        y = -ALIEN_HEIGHT
        speed = game_vars.get(
            "current_alien_speed", INITIAL_ALIEN_SPEED
        ) + random.uniform(-0.2, 0.2)

        alien = Alien(x, y, a_type, speed, a_shoot_mod)
        all_sprites.add(alien)
        aliens.add(alien)


def spawn_powerup(x_pos):
    p_type = random.choice(ALL_POWERUP_TYPES)
    if p_type == "extra_life" and random.random() > POWERUP_LIFE_SPAWN_MOD:
        possible_rerolls = [pt for pt in ALL_POWERUP_TYPES if pt != "extra_life"]
        if possible_rerolls:
            p_type = random.choice(possible_rerolls)

    powerup = PowerUp(x_pos, p_type)
    all_sprites.add(powerup)
    powerups.add(powerup)


def reset_game():
    global player, score, game_state, boss, aliens, all_sprites, player_bullets, alien_bullets, boss_bullets, powerups, boss_group, game_vars

    all_sprites.empty()
    player_bullets.empty()
    alien_bullets.empty()
    boss_bullets.empty()
    powerups.empty()
    aliens.empty()
    boss_group.empty()

    # Ensure any existing boss instance is fully gone
    if (
        "boss" in globals()
        and boss
        and isinstance(boss, pygame.sprite.Sprite)
        and boss.alive()
    ):
        boss.kill()
    boss = None  # Explicitly clear boss reference

    player = Player()
    all_sprites.add(player)
    score = 0

    game_vars = {
        "start_time": time.time(),
        "bosses_defeated": 0,
        "next_boss_score": BOSS_SCORE_THRESHOLD_BASE,  # Uses the added constant
        "last_alien_spawn_time": pygame.time.get_ticks(),
        "current_alien_spawn_interval": INITIAL_ALIEN_SPAWN_RATE,
        "current_alien_speed": INITIAL_ALIEN_SPEED,
        "current_alien_shoot_chance": ALIEN_BASE_SHOOT_CHANCE,
        "powerup_spawn_chance": POWERUP_BASE_SPAWN_CHANCE,
    }

    game_state = ENDLESS_PLAY


# --- Initialization ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Endless Invaders: Weapons!")
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
player = Player()  # Initial player needed for some UI elements potentially before reset
score = 0
game_state = INTRO
boss = None  # Define boss globally here
game_vars = {}  # Populated by reset_game


# --- Game Loop ---
running = True
while running:

    if game_state == INTRO:
        show_intro_screen()
        reset_game()
    elif game_state == GAME_OVER:
        if show_game_over_screen(score, game_vars.get("bosses_defeated", 0)):
            game_state = INTRO
        else:
            running = False

    elif game_state == ENDLESS_PLAY or game_state == BOSS_ACTIVE:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        all_sprites.update()

        # Recalculate difficulty based on potentially updated boss count
        boss_count = game_vars.get("bosses_defeated", 0)
        game_vars["current_alien_spawn_interval"] = max(
            MIN_ALIEN_SPAWN_RATE,
            INITIAL_ALIEN_SPAWN_RATE - boss_count * SPAWN_RATE_DECREASE_PER_BOSS,
        )
        game_vars["current_alien_speed"] = min(
            MAX_ALIEN_SPEED,
            INITIAL_ALIEN_SPEED + boss_count * ALIEN_SPEED_INCREASE_PER_BOSS,
        )
        game_vars["current_alien_shoot_chance"] = (
            ALIEN_BASE_SHOOT_CHANCE + boss_count * ALIEN_SHOOT_CHANCE_INCREASE_PER_BOSS
        )

        if game_state == ENDLESS_PLAY:
            spawn_alien()
            for alien in aliens:
                shoot_chance = game_vars.get(
                    "current_alien_shoot_chance", ALIEN_BASE_SHOOT_CHANCE
                )
                if random.random() < shoot_chance * alien.shoot_chance_mod:
                    alien.shoot()

            if score >= game_vars.get("next_boss_score", BOSS_SCORE_THRESHOLD_BASE):
                print(
                    f"Score {score} reached! Triggering Boss #{game_vars.get('bosses_defeated', 0) + 1}!"
                )
                game_state = BOSS_ACTIVE
                for alien in aliens:
                    alien.kill()
                for ab in alien_bullets:
                    ab.kill()
                boss = Boss(game_vars.get("bosses_defeated", 0) + 1)
                all_sprites.add(boss)
                boss_group.add(boss)

        elif game_state == BOSS_ACTIVE:
            if boss and not boss.alive() and not boss_group:  # Check boss death
                boss_num = boss.boss_number  # Store number before clearing boss
                boss_center_x = boss.rect.centerx  # Store center before clearing boss
                print(f"Boss #{boss_num} defeated!")
                score_bonus = 150 * boss_num
                score += score_bonus
                print(f"+{score_bonus} score bonus!")

                game_vars["bosses_defeated"] = game_vars.get("bosses_defeated", 0) + 1
                current_defeated = game_vars["bosses_defeated"]
                game_vars["next_boss_score"] = (
                    score
                    + BOSS_SCORE_THRESHOLD_BASE
                    + current_defeated * BOSS_SCORE_THRESHOLD_INCREMENT
                )
                print(f"Next boss at score: {game_vars['next_boss_score']}")

                if player:
                    player.deactivate_timed_effect()  # Keep weapon

                spawn_powerup(boss_center_x)
                spawn_powerup(boss_center_x - 40)
                spawn_powerup(boss_center_x + 40)

                boss = None  # Clear boss reference
                game_state = ENDLESS_PLAY
                game_vars["last_alien_spawn_time"] = now

        # --- Collision Detection ---
        # Player Projectiles vs Aliens
        for bullet in player_bullets:
            aliens_hit = pygame.sprite.spritecollide(bullet, aliens, False)
            for alien in aliens_hit:
                if alien.hit():
                    score += 10 + alien.max_health
                is_piercing = getattr(bullet, "piercing", False)
                if not is_piercing:
                    bullet.kill()
                    break

        # Player Projectiles vs Boss
        if game_state == BOSS_ACTIVE and boss and boss.alive():
            for bullet in player_bullets:
                is_piercing = getattr(bullet, "piercing", False)
                if pygame.sprite.collide_rect(bullet, boss):
                    boss.hit()
                    score += 2
                    if not is_piercing:
                        bullet.kill()

        # Enemy Bullets vs Player
        bullets_to_check = pygame.sprite.Group(alien_bullets, boss_bullets)
        if player and not player.hidden:
            player_hits = pygame.sprite.spritecollide(player, bullets_to_check, False)
            for bullet in player_hits:
                is_laser = hasattr(bullet, "is_laser") and bullet.is_laser
                damage_taken = False
                if is_laser:
                    if player.hide():
                        damage_taken = True
                    bullet.kill()  # Kill boss laser on hit for now
                else:
                    if player.hide():
                        damage_taken = True
                    bullet.kill()

                if damage_taken and player.lives <= 0:
                    game_state = GAME_OVER
                    break
            if game_state == GAME_OVER:
                continue

        # Player vs Powerups
        if player:
            powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
            for p_hit in powerup_hits:
                player.activate_powerup(p_hit.type)

        # Player vs Aliens Crash
        if player and not player.hidden:
            alien_crash = pygame.sprite.spritecollide(player, aliens, True)
            if alien_crash:
                if player.hide():
                    if player.lives <= 0:
                        game_state = GAME_OVER

        # --- Draw ---
        screen.fill(DARK_BLUE)
        for _ in range(40):
            star_x, star_y = random.randrange(SCREEN_WIDTH), random.randrange(
                SCREEN_HEIGHT
            )
            star_b = random.randint(60, 160)
            star_s = random.choice([1, 1, 2])
            pygame.draw.circle(
                screen, (star_b, star_b, star_b), (star_x, star_y), star_s
            )

        all_sprites.draw(screen)

        # UI
        draw_text(screen, f"SCORE: {score}", 20, 10, 35, WHITE, align="topleft")
        if player:
            draw_lives(screen, 10, 10, player.lives, player.image_orig)
            draw_hud(surface=screen, player=player)

        if game_state == ENDLESS_PLAY:
            draw_text(
                screen,
                f"Next Boss: {game_vars.get('next_boss_score', 'N/A')}",
                16,
                SCREEN_WIDTH - 10,
                SCREEN_HEIGHT - 20,
                YELLOW,
                align="topright",
            )
            draw_text(
                screen,
                f"Bosses: {game_vars.get('bosses_defeated', 0)}",
                16,
                SCREEN_WIDTH - 10,
                SCREEN_HEIGHT - 40,
                WHITE,
                align="topright",
            )
        elif game_state == BOSS_ACTIVE:
            draw_boss_health(screen, boss)

        pygame.display.flip()
        clock.tick(FPS)

# --- Quit ---
pygame.quit()
sys.exit()
