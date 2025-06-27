import pygame
import sys
import math
import random
import time

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30

# Colors (Limited Palette)
COLOR_SKY = (122, 122, 255)
COLOR_GROUND = (0, 170, 0)
COLOR_ROAD = (100, 100, 100)
COLOR_RUMBLE_RED = (255, 0, 0)
COLOR_RUMBLE_WHITE = (255, 255, 255)
COLOR_LINE = (255, 255, 255)
COLOR_MOUNTAIN = (100, 100, 180)
COLOR_SNOW = (230, 230, 230)
COLOR_CAR = (255, 165, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_PARTICLE = (255, 165, 0)  # Orange-ish particles for collision sparks
COLOR_HEALTH_BAR = (0, 255, 0)
COLOR_DAMAGE_BAR = (255, 0, 0)
COLOR_GAME_OVER = (255, 0, 0)
OPPONENT_COLORS = [
    (200, 0, 0),
    (0, 0, 200),
    (0, 180, 180),
    (200, 0, 200),
    (180, 180, 0),
]

# Road Parameters
ROAD_WIDTH_MAX = SCREEN_WIDTH * 1.5
ROAD_WIDTH_MIN = SCREEN_WIDTH * 0.05
HORIZON_Y = SCREEN_HEIGHT // 2
SEGMENT_LENGTH = 10
RUMBLE_LENGTH = 4
MAX_VIEW_DISTANCE = 350 * SEGMENT_LENGTH
MAX_ANIMATION_SPEED = 180

# Player Parameters
MAX_SPEED = 250
ACCELERATION = 0.8
BRAKING = -2.5
FRICTION = -0.2
COLLISION_SLOWDOWN_FACTOR = 0.40  # Increased slightly, lose more speed on hit
COLLISION_COOLDOWN = 0.5  # Time between registering hits from same car
COLLISION_BUMP_MAGNITUDE = 20.0
COLLISION_BUMP_DECAY = 0.75
MAX_HEALTH = 100
HEALTH_REGEN_RATE = 1.5  # Slightly reduced regen
DAMAGE_PER_COLLISION = 15  # Reduced base damage slightly
# --- Turning / Steering Parameters ---
STEERING_RESPONSE_FACTOR = 4.5  # How quickly the car aims towards the target direction
STEERING_DAMPING = (
    0.12  # How quickly lateral movement slows down (tendency to straighten)
)
CENTRIFUGAL_FACTOR = 0.0006  # How much speed pushes the car outwards in turns

# Game State
score = 0
speed = 0
position = 0.0
visual_position = 0.0
lap = 0
unit = 0
player_x_offset = 0.0
target_player_x_offset = 0.0  # Where the player *wants* to steer
road_x_offset = 0.0
last_collision_time = 0.0
collision_bump_offset_x = 0.0
game_over = False
health = MAX_HEALTH
# Removed last_damage_time, is_invulnerable

# Opponent Cars
opponents = []
MAX_OPPONENTS = 4  # Slightly more opponents possible
# Removed OPPONENT_BLOCK_DISTANCE, OPPONENT_BLOCK_FACTOR
OPPONENT_CENTERING_FACTOR = 0.008  # Renamed, but used for general lane changing speed
INITIAL_MIN_SPACING = SEGMENT_LENGTH * 80
RESPAWN_DISTANCE_MIN = MAX_VIEW_DISTANCE * 0.9
RESPAWN_DISTANCE_MAX = MAX_VIEW_DISTANCE * 1.2
COLLISION_CHECK_Z = (
    SEGMENT_LENGTH * 3.0
)  # How close opponent needs to be for collision check

# Cloud Data
clouds = []
NUM_CLOUDS = 5

# Base Car Dimensions (used for Rect calculations)
BASE_CAR_WIDTH = 80
BASE_CAR_HEIGHT = 40

# Particle Effect System
particles = []
MAX_PARTICLES = 30
PARTICLE_LIFETIME = 0.8

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Retro Racer Realistic Turn")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 30, bold=True)
small_font = pygame.font.SysFont("monospace", 18)

# Initialize sound effects (Keep existing sound loading)
try:
    collision_sound = pygame.mixer.Sound(
        "c:\\Users\\claud\\Desktop\\dev\\collision.wav"
    )
    engine_sound = pygame.mixer.Sound("c:\\Users\\claud\\Desktop\\dev\\engine.wav")
    game_over_sound = pygame.mixer.Sound(
        "c:\\Users\\claud\\Desktop\\dev\\game_over.wav"
    )
    sounds_loaded = True
    engine_sound.set_volume(0.6)  # Adjust volume if needed
    collision_sound.set_volume(0.8)
except Exception as e:
    sounds_loaded = False
    print(
        f"Warning: Sound files not found or error loading them: {e}. Game will run without sound."
    )


# --- Initialization Functions ---
def initialize_clouds():
    clouds.clear()
    [
        clouds.append(
            {
                "x": random.randint(-SCREEN_WIDTH // 2, SCREEN_WIDTH),
                "y": random.randint(30, HORIZON_Y - 60),
                "w": random.randint(60, 150),
                "h": random.randint(15, 30),
                "speed": random.uniform(0.2, 1.0),
            }
        )
        for _ in range(NUM_CLOUDS)
    ]


def initialize_opponents():
    opponents.clear()
    colors_available = OPPONENT_COLORS[:]
    last_z = 0
    for i in range(MAX_OPPONENTS):
        if not colors_available:
            colors_available = OPPONENT_COLORS[:]  # Reuse colors if needed
        color = random.choice(colors_available)
        colors_available.remove(color)

        min_z = last_z + INITIAL_MIN_SPACING
        if i == 0:  # Ensure first opponent isn't too close initially
            min_z = SEGMENT_LENGTH * 80  # Increased initial distance
        z_pos = random.uniform(min_z, min_z + INITIAL_MIN_SPACING * 1.5)
        last_z = z_pos

        initial_offset = random.uniform(-0.7, 0.7)
        opponents.append(
            {
                "z": z_pos,
                "x_offset": initial_offset,
                "speed": random.uniform(
                    MAX_SPEED * 0.65, MAX_SPEED * 0.85
                ),  # Adjusted speed range
                "color": color,
                "target_x_offset": initial_offset,  # Target lane starts same as current
                "time_since_target_change": random.uniform(
                    0.0, 3.0
                ),  # Randomize initial change timer
            }
        )


# --- Helper Functions ---
def draw_background():
    # Keep existing background drawing
    screen.fill(COLOR_SKY)
    for cloud in clouds:
        main_rect = pygame.Rect(cloud["x"], cloud["y"], cloud["w"], cloud["h"])
        offset1_rect = pygame.Rect(
            cloud["x"] + cloud["w"] * 0.2,
            cloud["y"] - cloud["h"] * 0.3,
            cloud["w"] * 0.6,
            cloud["h"],
        )
        offset2_rect = pygame.Rect(
            cloud["x"] + cloud["w"] * 0.4,
            cloud["y"] + cloud["h"] * 0.3,
            cloud["w"] * 0.7,
            cloud["h"],
        )
        pygame.draw.ellipse(screen, COLOR_RUMBLE_WHITE, main_rect)
        pygame.draw.ellipse(screen, COLOR_RUMBLE_WHITE, offset1_rect)
        pygame.draw.ellipse(screen, COLOR_RUMBLE_WHITE, offset2_rect)
    pygame.draw.rect(
        screen, COLOR_GROUND, (0, HORIZON_Y, SCREEN_WIDTH, SCREEN_HEIGHT - HORIZON_Y)
    )
    mountain_points = [
        (0, HORIZON_Y),
        (50, HORIZON_Y - 30),
        (100, HORIZON_Y),
        (150, HORIZON_Y - 50),
        (200, HORIZON_Y),
        (250, HORIZON_Y - 20),
        (300, HORIZON_Y),
        (350, HORIZON_Y - 80),
        (400, HORIZON_Y - 150),
        (450, HORIZON_Y - 80),
        (500, HORIZON_Y),
        (550, HORIZON_Y - 40),
        (600, HORIZON_Y),
        (650, HORIZON_Y - 60),
        (700, HORIZON_Y),
        (750, HORIZON_Y - 25),
        (SCREEN_WIDTH, HORIZON_Y),
    ]
    pygame.draw.polygon(screen, COLOR_MOUNTAIN, mountain_points)
    snow_points = [
        (375, HORIZON_Y - 110),
        (400, HORIZON_Y - 150),
        (425, HORIZON_Y - 110),
        (415, HORIZON_Y - 100),
        (385, HORIZON_Y - 100),
    ]
    pygame.draw.polygon(screen, COLOR_SNOW, snow_points)


def draw_road():
    # Keep existing road drawing logic
    for y in range(HORIZON_Y, SCREEN_HEIGHT):
        scale = (y - HORIZON_Y) / (SCREEN_HEIGHT - HORIZON_Y)
        scale_pow = scale**3  # Use power for more dramatic perspective near horizon
        road_w = ROAD_WIDTH_MIN + (ROAD_WIDTH_MAX - ROAD_WIDTH_MIN) * scale_pow
        rumble_w = road_w * 0.05
        line_w = road_w * 0.02

        # Apply road curvature/offset based on road_x_offset
        screen_center_x = SCREEN_WIDTH / 2 + road_x_offset * SCREEN_WIDTH * (
            1 - scale
        )  # Road shifts based on player turning input influence

        depth_factor = (
            (1 - scale) * MAX_VIEW_DISTANCE * 0.1
        )  # Approximate depth based on y
        segment_index = int((visual_position + depth_factor) / SEGMENT_LENGTH)

        # Rumble strip coloring
        rumble_color = (
            COLOR_RUMBLE_RED
            if (segment_index // RUMBLE_LENGTH) % 2 == 0
            else COLOR_RUMBLE_WHITE
        )
        # Center line coloring (dashed)
        line_color = (
            COLOR_LINE
            if (segment_index // (RUMBLE_LENGTH * 2)) % 2 == 0
            else COLOR_ROAD
        )  # Longer dashes

        # Calculate road edges
        road_x1 = screen_center_x - road_w / 2
        road_x2 = screen_center_x + road_w / 2
        rumble_x1 = road_x1 - rumble_w
        rumble_x2 = road_x2 + rumble_w

        # Draw rumble strips
        pygame.draw.line(
            screen, rumble_color, (rumble_x1, y), (road_x1, y), max(1, int(rumble_w))
        )
        pygame.draw.line(
            screen, rumble_color, (road_x2, y), (rumble_x2, y), max(1, int(rumble_w))
        )

        # Draw road surface (simple line per scanline for this pseudo-3D style)
        pygame.draw.line(screen, COLOR_ROAD, (road_x1, y), (road_x2, y), 1)

        # Draw center line if wide enough
        if line_w > 0.5 and line_color != COLOR_ROAD:
            line_x1 = screen_center_x - line_w / 2
            line_x2 = screen_center_x + line_w / 2
            pygame.draw.line(
                screen, line_color, (line_x1, y), (line_x2, y), max(1, int(line_w))
            )


def get_screen_params_and_rect(z_distance, x_offset):
    # Keep existing perspective calculation
    if not (0 < z_distance < MAX_VIEW_DISTANCE):
        return None, None

    # Simplified perspective calculation (more linear further away)
    perspective_factor = z_distance / MAX_VIEW_DISTANCE
    screen_y_scale = (1 - perspective_factor) ** 0.8  # Adjust power for scaling feel
    screen_y = HORIZON_Y + (SCREEN_HEIGHT - HORIZON_Y) * screen_y_scale

    # Recalculate road properties at this specific screen_y to place the car correctly
    scale_at_y = (screen_y - HORIZON_Y) / (SCREEN_HEIGHT - HORIZON_Y)
    scale_pow_at_y = scale_at_y**3
    road_w_at_y = ROAD_WIDTH_MIN + (ROAD_WIDTH_MAX - ROAD_WIDTH_MIN) * scale_pow_at_y

    # Screen center at this y, considering the road's offset/curve
    screen_center_x_at_y = SCREEN_WIDTH / 2 + road_x_offset * SCREEN_WIDTH * (
        1 - scale_at_y
    )

    # Final screen X position of the car center
    screen_x = screen_center_x_at_y + x_offset * (
        road_w_at_y / 2
    )  # x_offset is relative (-1 to 1)

    # Sprite scale based on depth
    sprite_scale = scale_at_y * 1.0  # Adjust base scale factor if needed

    # Calculate car rect based on screen position and scale
    car_width = BASE_CAR_WIDTH * sprite_scale
    car_height = BASE_CAR_HEIGHT * sprite_scale

    rect_left = screen_x - car_width / 2
    rect_top = screen_y - car_height  # Anchor point is bottom-center
    car_rect = pygame.Rect(rect_left, rect_top, car_width, car_height)

    params = {"x": screen_x, "y": screen_y, "scale": sprite_scale}
    return params, car_rect


def draw_f1_car(params, color, bump_offset=0.0):
    # Keep existing car drawing logic
    if params is None or params["scale"] < 0.01:
        return
    scale = params["scale"]
    car_x, car_y = params["x"] + bump_offset, params["y"]  # Apply bump offset here
    car_width, car_height = BASE_CAR_WIDTH * scale, BASE_CAR_HEIGHT * scale

    # Ensure minimum drawable size to avoid errors with zero dimensions
    if car_width < 1 or car_height < 1:
        return

    draw_x, draw_y = (
        car_x - car_width / 2,
        car_y - car_height,
    )  # Top-left corner for drawing

    # --- Car Body Parts (scaled) ---
    body_rect = pygame.Rect(
        draw_x + car_width * 0.1, draw_y, car_width * 0.8, car_height * 0.8
    )
    wing_rect = pygame.Rect(
        draw_x, draw_y + car_height * 0.6, car_width, car_height * 0.3
    )
    nose_poly = [
        (body_rect.left, body_rect.top + body_rect.height * 0.2),
        (body_rect.centerx, body_rect.top - car_height * 0.2),  # Pointed nose
        (body_rect.right, body_rect.top + body_rect.height * 0.2),
    ]
    driver_rect = pygame.Rect(
        body_rect.centerx - car_width * 0.08,
        body_rect.top + car_height * 0.1,
        car_width * 0.16,
        car_height * 0.2,
    )

    # Draw main parts
    pygame.draw.rect(screen, color, wing_rect)
    pygame.draw.rect(screen, color, body_rect)
    pygame.draw.polygon(screen, color, nose_poly)
    pygame.draw.rect(screen, COLOR_BLACK, driver_rect)  # Driver helmet/cockpit area

    # --- Wheels (scaled) ---
    wheel_width, wheel_height = car_width * 0.2, car_height * 0.5
    # Rear Wheels
    pygame.draw.rect(
        screen,
        COLOR_BLACK,
        (
            draw_x - wheel_width * 0.8,
            draw_y + car_height * 0.5,
            wheel_width,
            wheel_height,
        ),
    )
    pygame.draw.rect(
        screen,
        COLOR_BLACK,
        (
            draw_x + car_width - wheel_width * 0.2,
            draw_y + car_height * 0.5,
            wheel_width,
            wheel_height,
        ),
    )
    # Front Wheels (slightly smaller/different position)
    f_wheel_width, f_wheel_height = wheel_width * 0.8, wheel_height * 0.8
    pygame.draw.rect(
        screen,
        COLOR_BLACK,
        (
            draw_x + car_width * 0.05,
            draw_y - f_wheel_height * 0.1,
            f_wheel_width,
            f_wheel_height,
        ),
    )
    pygame.draw.rect(
        screen,
        COLOR_BLACK,
        (
            draw_x + car_width * 0.95 - f_wheel_width,
            draw_y - f_wheel_height * 0.1,
            f_wheel_width,
            f_wheel_height,
        ),
    )


def draw_opponents_and_hud(opponents_draw_info):
    # Draw opponents first (those further away)
    for item in opponents_draw_info:
        draw_f1_car(
            item["params"], item["color"], 0.0
        )  # No bump offset for opponents visually

    # Draw HUD elements
    score_text = font.render(f"SCORE {int(score)}", True, COLOR_TEXT)
    unit_text = font.render(f"UNIT {int(unit)}", True, COLOR_TEXT)  # Lap progress
    lap_text = font.render(f"LAP {lap+1}", True, COLOR_TEXT)
    speed_text = font.render(f"SPEED {int(speed)}MPH", True, COLOR_TEXT)
    hi_text = font.render("HI", True, COLOR_TEXT)  # Placeholder/Style text

    screen.blit(score_text, (20, 10))
    screen.blit(unit_text, (SCREEN_WIDTH // 2 - unit_text.get_width() // 2 - 50, 10))
    screen.blit(lap_text, (SCREEN_WIDTH - lap_text.get_width() - 180, 10))
    screen.blit(speed_text, (SCREEN_WIDTH - speed_text.get_width() - 20, 40))
    screen.blit(hi_text, (SCREEN_WIDTH // 2 - hi_text.get_width() // 2 - 50, 40))

    # Draw Health Bar
    health_bar_width = 200
    health_bar_height = 15
    health_bar_x = 20
    health_bar_y = 50
    health_percentage = max(
        0, health / MAX_HEALTH
    )  # Ensure percentage doesn't go below 0
    current_health_width = health_bar_width * health_percentage

    pygame.draw.rect(
        screen,
        COLOR_DAMAGE_BAR,
        (health_bar_x, health_bar_y, health_bar_width, health_bar_height),
    )
    pygame.draw.rect(
        screen,
        COLOR_HEALTH_BAR,
        (health_bar_x, health_bar_y, current_health_width, health_bar_height),
    )

    health_text = small_font.render(
        f"HEALTH: {int(max(0, health))}", True, COLOR_TEXT
    )  # Display non-negative health
    screen.blit(health_text, (health_bar_x + health_bar_width + 10, health_bar_y))

    # Removed powerup drawing section


def draw_player_car_and_joystick():
    # Calculate player car's base screen position based on offset
    # The visual offset is exaggerated compared to the logical road offset
    screen_offset = player_x_offset * (
        SCREEN_WIDTH / 3.0
    )  # How much offset translates to screen pixels
    base_player_screen_x = SCREEN_WIDTH / 2 + screen_offset

    # Player car is always drawn at the bottom, fixed scale
    player_params = {"x": base_player_screen_x, "y": SCREEN_HEIGHT - 10, "scale": 1.0}

    # Draw the player car with potential collision bump offset
    draw_f1_car(player_params, COLOR_CAR, collision_bump_offset_x)

    # Draw decorative joystick graphic (unchanged)
    base_x, base_y = SCREEN_WIDTH - 70, SCREEN_HEIGHT - 70
    base_w, base_h = 50, 15
    stick_w, stick_h = 10, 30
    button_r = 8
    pygame.draw.rect(
        screen, COLOR_RUMBLE_WHITE, (base_x, base_y, base_w, base_h), border_radius=3
    )
    stick_x = base_x + base_w / 2 - stick_w / 2
    stick_y = base_y - stick_h + base_h / 3
    pygame.draw.rect(screen, COLOR_RUMBLE_RED, (stick_x, stick_y, stick_w, stick_h))
    pygame.draw.circle(
        screen, COLOR_RUMBLE_RED, (int(stick_x + stick_w / 2), int(stick_y)), button_r
    )


def check_collisions_accurate(player_rect, visible_opponents_info):
    global speed, last_collision_time, collision_bump_offset_x, health
    current_time = time.time()

    # Removed invulnerability check

    if player_rect is None:
        return  # Safety check

    player_collided_this_frame = False
    for opp_info in visible_opponents_info:
        # Only check collision for opponents very close in Z distance
        if 0 < opp_info["z"] < COLLISION_CHECK_Z:
            if player_rect.colliderect(opp_info["rect"]):
                # Calculate overlap for severity (optional, simple check is fine too)
                overlap_rect = player_rect.clip(opp_info["rect"])
                # overlap_area = overlap_rect.width * overlap_rect.height
                # player_area = player_rect.width * player_rect.height
                # collision_severity = min(1.0, overlap_area / max(1, player_area)) # Avoid division by zero
                collision_severity = 0.8  # Use a fixed severity for simplicity for now

                # Determine bump direction
                if player_rect.centerx < opp_info["rect"].centerx:
                    # Player hit opponent on their left side (or rear-left) -> bump player right
                    collision_bump_offset_x = (
                        COLLISION_BUMP_MAGNITUDE * collision_severity
                    )
                else:
                    # Player hit opponent on their right side (or rear-right) -> bump player left
                    collision_bump_offset_x = (
                        -COLLISION_BUMP_MAGNITUDE * collision_severity
                    )

                # Apply effects only if cooldown has passed
                if current_time >= last_collision_time + COLLISION_COOLDOWN:
                    speed *= (
                        1.0 - COLLISION_SLOWDOWN_FACTOR * collision_severity
                    )  # Slow down based on severity
                    last_collision_time = current_time

                    # Apply damage (can depend on relative speed too, simplified here)
                    damage = (
                        DAMAGE_PER_COLLISION * collision_severity
                    )  # * (max(10, speed) / MAX_SPEED) # Optional speed factor
                    health -= damage
                    # Removed setting last_damage_time and is_invulnerable

                    # Create particle burst at collision point
                    create_collision_particles(
                        overlap_rect.centerx, overlap_rect.centery
                    )

                    if sounds_loaded:
                        collision_sound.play()

                player_collided_this_frame = True
                break  # Handle only one collision per frame for simplicity

    # If no collision this frame, allow bump offset to decay naturally elsewhere
    # (This happens in the main loop now)


def create_collision_particles(x, y):
    # Keep existing particle creation
    num_particles = random.randint(8, 15)  # Slightly more sparks
    for _ in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        p_speed = random.uniform(80, 180)  # Slightly faster particles
        size = random.randint(2, 5)
        lifetime = random.uniform(0.2, 0.6)  # Shorter lifetime for sparks

        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * p_speed,
                "vy": math.sin(angle) * p_speed,
                "size": size,
                "color": COLOR_PARTICLE,
                "created": time.time(),
                "lifetime": lifetime,
            }
        )
        if len(particles) > MAX_PARTICLES * 2:  # Prune if too many instantly
            particles.pop(0)


def update_particles(delta_time):
    # Keep existing particle update, add gravity maybe? (Optional)
    current_time = time.time()
    i = 0
    while i < len(particles):
        p = particles[i]
        age = current_time - p["created"]

        if age > p["lifetime"]:
            particles.pop(i)
        else:
            p["x"] += p["vx"] * delta_time
            p["y"] += p["vy"] * delta_time
            # Optional: Add gravity
            # p['vy'] += 98.1 * delta_time # Simple gravity
            # p['y'] += p['vy'] * delta_time

            # Fade out size
            fade_factor = 1.0 - (age / p["lifetime"])
            current_size = p["size"] * fade_factor
            p["current_size"] = max(1, int(current_size))  # Store int size for drawing

            i += 1
    # Trim particle list occasionally if it grows too large
    if len(particles) > MAX_PARTICLES:
        particles[:] = particles[-MAX_PARTICLES:]


def draw_particles():
    # Keep existing particle drawing
    for p in particles:
        # Use stored current_size if available, otherwise calculate on the fly
        size_to_draw = p.get(
            "current_size",
            int(max(1, p["size"] * (1 - (time.time() - p["created"]) / p["lifetime"]))),
        )
        if size_to_draw > 0:
            pygame.draw.circle(
                screen, p["color"], (int(p["x"]), int(p["y"])), size_to_draw
            )


def draw_game_over():
    # Keep existing game over screen
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black overlay
    screen.blit(overlay, (0, 0))

    game_over_text = font.render("GAME OVER", True, COLOR_GAME_OVER)
    score_text = font.render(f"FINAL SCORE: {int(score)}", True, COLOR_TEXT)
    restart_text = small_font.render("Press SPACE to restart", True, COLOR_TEXT)

    screen.blit(
        game_over_text,
        (
            SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
            SCREEN_HEIGHT // 2 - game_over_text.get_height() - 20,
        ),
    )
    screen.blit(
        score_text,
        (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2),
    )
    screen.blit(
        restart_text,
        (
            SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
            SCREEN_HEIGHT // 2 + score_text.get_height() + 20,
        ),
    )


def reset_game():
    global score, speed, position, visual_position, lap, unit, player_x_offset, target_player_x_offset
    global road_x_offset, last_collision_time, collision_bump_offset_x, game_over
    global health, particles  # Removed last_damage_time, is_invulnerable

    score = 0
    speed = 0
    position = 0.0
    visual_position = 0.0
    lap = 0
    unit = 0
    player_x_offset = 0.0
    target_player_x_offset = 0.0  # Reset target offset
    road_x_offset = 0.0
    last_collision_time = 0.0
    collision_bump_offset_x = 0.0
    game_over = False
    health = MAX_HEALTH
    particles.clear()

    initialize_clouds()
    initialize_opponents()

    if sounds_loaded:
        engine_sound.stop()
        engine_sound.play(-1)  # Restart engine sound


# --- Main Game Loop ---
initialize_clouds()
initialize_opponents()
running = True
lap_distance = 15000  # Distance for one lap

if sounds_loaded:
    engine_sound.play(-1)  # Loop engine sound

while running:
    delta_time = clock.tick(FPS) / 1000.0
    # Clamp delta_time to prevent physics issues if frame rate drops drastically
    delta_time = min(delta_time, 0.1)
    current_time = time.time()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_over:
            reset_game()  # Restart game on SPACE if game over

    # --- Game Over State ---
    if game_over:
        # Keep drawing background and road for context, then overlay Game Over
        draw_background()
        draw_road()
        # Draw opponents/player frozen? Or skip? Let's skip for cleaner game over.
        draw_game_over()
        pygame.display.flip()
        continue  # Skip the rest of the game loop

    # --- Input Handling ---
    keys = pygame.key.get_pressed()
    steer_input = 0
    accel_input = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        steer_input = -1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        steer_input = 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        accel_input = 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        accel_input = -1

    # --- Player Physics & State Update ---
    # Acceleration/Braking/Friction
    if accel_input > 0:
        speed += ACCELERATION * (
            1.0 - speed / MAX_SPEED
        )  # Accel less effective near max speed
    elif accel_input < 0:
        speed += BRAKING  # Braking is constant force
    else:
        speed += FRICTION  # Friction always applies
    speed = max(0, min(speed, MAX_SPEED))

    # --- Steering Update (New Logic) ---
    old_player_x_offset = player_x_offset  # Store previous offset for camera adjustment

    # 1. Determine target offset based on input
    # Target slightly wider than max road edge allows self-correction feel when hitting edge
    target_player_x_offset = steer_input * 1.1

    # 2. Smoothly move current offset towards target (Lerp)
    diff = target_player_x_offset - player_x_offset
    player_x_offset += diff * STEERING_RESPONSE_FACTOR * delta_time

    # 3. Apply centrifugal force (push outwards on turns) - depends on speed and how hard we are turning
    # Approximated by steer_input magnitude and speed
    # More sophisticated would be rate of change of offset, but this is simpler
    centrifugal_push = steer_input * (speed / MAX_SPEED) * speed * CENTRIFUGAL_FACTOR
    player_x_offset += centrifugal_push * delta_time

    # 4. Apply damping / tendency to straighten out (like lateral friction)
    # Reduces sideways drift when not actively steering or counter-steering
    player_x_offset *= 1.0 - STEERING_DAMPING * delta_time

    # 5. Clamp player offset (prevent going too far off road visually)
    # Allow slightly off-road (-1.2 to 1.2) for effect before hard clamp
    player_x_offset = max(-1.2, min(player_x_offset, 1.2))

    # --- Road Offset Update (Camera) ---
    # Link camera shift more to the actual player movement for smoother feel
    road_offset_change = (
        player_x_offset - old_player_x_offset
    ) * 0.1  # Camera follows player lateral movement slightly
    road_x_offset -= road_offset_change
    # Damp the road offset so it returns to center slowly
    road_x_offset *= 0.98  # Slightly slower damping than before

    # Position Update (Distance traveled)
    position += speed * delta_time * 5  # Arbitrary scaling factor for distance units
    visual_increment = min(speed, MAX_ANIMATION_SPEED)  # Road animation speed capped
    visual_position += visual_increment * delta_time * 5

    # Lap logic
    if position >= lap_distance:
        position -= lap_distance
        visual_position -= lap_distance  # Keep visual position relative
        lap += 1
    unit = int((position / lap_distance) * 1000)  # Progress within the lap (0-999)

    # Score Update
    score += speed * 0.01 * delta_time * 60  # Score based on speed

    # --- Opponent Update ---
    visible_opponents_info = []
    for i in range(len(opponents)):
        opp = opponents[i]

        # --- Opponent AI (New Logic) ---
        opp["time_since_target_change"] += delta_time

        # Decide if opponent should change target lane (e.g., every few seconds)
        if opp["time_since_target_change"] > random.uniform(
            3.0, 6.0
        ):  # Change lane less frequently
            opp["target_x_offset"] = random.uniform(
                -0.8, 0.8
            )  # Target a random lane position
            opp["time_since_target_change"] = 0.0

        # Simple movement towards target offset
        move_factor = OPPONENT_CENTERING_FACTOR * (
            opp["speed"] / MAX_SPEED
        )  # Scale movement by relative speed
        target_offset = opp["target_x_offset"]

        # Move towards the target lane position
        if opp["x_offset"] < target_offset:
            opp["x_offset"] = min(
                opp["x_offset"] + move_factor * delta_time * 100, target_offset
            )  # Apply delta_time
        elif opp["x_offset"] > target_offset:
            opp["x_offset"] = max(
                opp["x_offset"] - move_factor * delta_time * 100, target_offset
            )  # Apply delta_time

        # Clamp opponent offset (keep them generally on the road)
        opp["x_offset"] = max(-0.9, min(0.9, opp["x_offset"]))

        # --- Opponent Z Position Update ---
        # Opponent Z position changes based on relative speed to player
        opp["z"] += (opp["speed"] - speed) * delta_time * 5  # Factor 5 for visual speed

        # Respawn logic (if too far behind or too far ahead)
        if opp["z"] < -INITIAL_MIN_SPACING * 0.5 or opp["z"] > MAX_VIEW_DISTANCE * 1.5:
            opp["z"] = random.uniform(
                RESPAWN_DISTANCE_MIN, RESPAWN_DISTANCE_MAX
            )  # Respawn ahead
            opp["x_offset"] = random.uniform(-0.7, 0.7)
            opp["target_x_offset"] = opp["x_offset"]  # Reset target when respawning
            opp["time_since_target_change"] = random.uniform(0.0, 3.0)  # Reset timer

        # --- Get Screen Coords for Visible Opponents ---
        params, opp_rect = get_screen_params_and_rect(opp["z"], opp["x_offset"])
        if params and opp_rect:
            visible_opponents_info.append(
                {
                    "params": params,
                    "rect": opp_rect,
                    "z": opp["z"],
                    "color": opp["color"],
                }
            )

    # --- Collision Detection ---
    # Calculate player's current screen rect for collision
    player_screen_offset = player_x_offset * (SCREEN_WIDTH / 3.0)
    current_player_center_x = (
        SCREEN_WIDTH / 2 + player_screen_offset + collision_bump_offset_x
    )
    player_bottom_y = SCREEN_HEIGHT - 10
    # Use base dimensions as player is always at screen bottom scale 1.0
    player_rect = pygame.Rect(
        current_player_center_x - BASE_CAR_WIDTH / 2,
        player_bottom_y - BASE_CAR_HEIGHT,
        BASE_CAR_WIDTH,
        BASE_CAR_HEIGHT,
    )
    check_collisions_accurate(player_rect, visible_opponents_info)

    # --- Update Collision Bump Offset ---
    # Decay the visual bump effect
    if collision_bump_offset_x != 0:
        collision_bump_offset_x *= COLLISION_BUMP_DECAY ** (
            delta_time * 60
        )  # Frame-rate independent decay
        if abs(collision_bump_offset_x) < 0.5:
            collision_bump_offset_x = 0.0

    # --- Health Regen ---
    # Regenerate health slowly over time if not recently hit (using collision cooldown time)
    if (
        current_time > last_collision_time + 3.0 and health < MAX_HEALTH
    ):  # 3 second delay after last hit
        health += HEALTH_REGEN_RATE * delta_time
        health = min(health, MAX_HEALTH)

    # --- Check Game Over Condition ---
    if health <= 0:
        game_over = True
        if sounds_loaded:
            engine_sound.stop()
            game_over_sound.play()

    # --- Particle Update ---
    update_particles(delta_time)

    # --- Cloud Update ---
    for cloud in clouds:
        # Clouds move based on their speed + slight parallax effect from player speed
        cloud["x"] += cloud["speed"] * (1 + speed / MAX_SPEED * 0.1) * delta_time * 100
        if cloud["x"] > SCREEN_WIDTH:
            cloud["x"] = -cloud["w"] - random.randint(0, 50)
            cloud["y"] = random.randint(30, HORIZON_Y - 60)

    # --- Drawing ---
    draw_background()
    draw_road()

    # Sort opponents by depth (y-coordinate) so closer ones draw on top
    visible_opponents_info.sort(
        key=lambda item: item["params"]["y"], reverse=False
    )  # Furthest first

    draw_opponents_and_hud(visible_opponents_info)
    draw_particles()
    draw_player_car_and_joystick()  # Player car drawn last (on top)

    # --- Display Update ---
    pygame.display.flip()

# --- Cleanup ---
pygame.quit()
sys.exit()
