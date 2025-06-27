import pygame
import sys
import random
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 60
CORNER_RADIUS = 30 # Define corner radius for the frame

# --- Define the actual playable grid boundaries (inside the frame) ---
# --- MODIFICATION: Shrink bounds by one more cell for visual clearance ---
PLAYABLE_GRID_X_MIN = 1 # Column 0 is frame
PLAYABLE_GRID_Y_MIN = 1 # Row 0 is frame
PLAYABLE_GRID_X_MAX = GRID_WIDTH - 2  # Column GRID_WIDTH-1 is frame
PLAYABLE_GRID_Y_MAX = GRID_HEIGHT - 2 # Row GRID_HEIGHT-1 is frame
# --- END MODIFICATION ---

# Colors
BACKGROUND = (18, 18, 30)
FRAME_COLOR = (24, 24, 40) # Slightly lighter than background for the frame
SNAKE_COLOR = (0, 204, 150)
FOOD_COLOR = (255, 99, 71)
GRID_COLOR = (30, 30, 45)
TEXT_COLOR = (240, 240, 240)
SCORE_COLOR = (255, 255, 100)
BUTTON_COLOR = (66, 135, 245)
BUTTON_HOVER_COLOR = (86, 155, 255) # Corrected value

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sleek Snake Game")
clock = pygame.time.Clock()

# Font
font_small = pygame.font.SysFont('Arial', 24)
font_medium = pygame.font.SysFont('Arial', 36)
font_large = pygame.font.SysFont('Arial', 48)

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.length = 1
        # --- MODIFICATION: Start snake within *new* playable bounds ---
        # Ensure starting position isn't right at the edge of the new bounds
        start_x = random.randint(PLAYABLE_GRID_X_MIN + 1, PLAYABLE_GRID_X_MAX - 1)
        start_y = random.randint(PLAYABLE_GRID_Y_MIN + 1, PLAYABLE_GRID_Y_MAX - 1)
        self.positions = [(start_x, start_y)]
        # --- END MODIFICATION ---

        self.direction = random.choice([
            (0, -1),  # Up
            (0, 1),   # Down
            (1, 0),   # Right
            (-1, 0)   # Left
        ])
        self.score = 0
        self.grow_pending = 3
        self.color_offset = 0
        self.color_direction = 1

    def get_head_position(self):
        return self.positions[0]

    def update(self):
        self.color_offset += 0.05 * self.color_direction
        if self.color_offset > 30: self.color_direction = -1
        elif self.color_offset < 0: self.color_direction = 1

        head = self.get_head_position()
        x, y = self.direction
        new_head = (head[0] + x, head[1] + y)

        # --- Check against playable grid boundaries (uses the tighter constants) ---
        if (new_head[0] < PLAYABLE_GRID_X_MIN or new_head[0] > PLAYABLE_GRID_X_MAX or
            new_head[1] < PLAYABLE_GRID_Y_MIN or new_head[1] > PLAYABLE_GRID_Y_MAX):
            return False  # Game over - hit the inner wall (frame area)
        # ---

        if new_head in self.positions: return False # Game over - hit self

        self.positions.insert(0, new_head)

        if self.grow_pending > 0: self.grow_pending -= 1
        else: self.positions.pop()

        return True

    def grow(self):
        self.grow_pending += 2
        self.score += 10

    def render(self, surface):
        # (No changes needed in snake rendering itself)
        for i, p in enumerate(self.positions):
            draw_x, draw_y = p[0] * GRID_SIZE, p[1] * GRID_SIZE
            rect = pygame.Rect(draw_x, draw_y, GRID_SIZE, GRID_SIZE)
            shrink_factor = 0.9 if i == len(self.positions) - 1 else 0.95
            inner_rect = pygame.Rect(rect.x + rect.width * (1 - shrink_factor) / 2, rect.y + rect.height * (1 - shrink_factor) / 2, rect.width * shrink_factor, rect.height * shrink_factor)
            r = max(0, min(255, SNAKE_COLOR[0] + int(self.color_offset)))
            g = max(0, min(255, SNAKE_COLOR[1] + int(self.color_offset)))
            b = max(0, min(255, SNAKE_COLOR[2] - int(self.color_offset)))
            pygame.draw.rect(surface, (r, g, b), rect, border_radius=8)
            inner_b = max(0, min(255, b + 50))
            pygame.draw.rect(surface, (r, g, inner_b), inner_rect, border_radius=6)
            if i == 0:
                eye_size = GRID_SIZE // 5; offset = GRID_SIZE // 3
                if self.direction == (0, -1): eye1_pos, eye2_pos = (rect.x + offset, rect.y + offset), (rect.x + rect.width - offset - eye_size, rect.y + offset)
                elif self.direction == (0, 1): eye1_pos, eye2_pos = (rect.x + offset, rect.y + rect.height - offset - eye_size), (rect.x + rect.width - offset - eye_size, rect.y + rect.height - offset - eye_size)
                elif self.direction == (-1, 0): eye1_pos, eye2_pos = (rect.x + offset, rect.y + offset), (rect.x + offset, rect.y + rect.height - offset - eye_size)
                else: eye1_pos, eye2_pos = (rect.x + rect.width - offset - eye_size, rect.y + offset), (rect.x + rect.width - offset - eye_size, rect.y + rect.height - offset - eye_size)
                pygame.draw.rect(surface, (255, 255, 255), (eye1_pos[0], eye1_pos[1], eye_size, eye_size), border_radius=eye_size//2)
                pygame.draw.rect(surface, (255, 255, 255), (eye2_pos[0], eye2_pos[1], eye_size, eye_size), border_radius=eye_size//2)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = FOOD_COLOR
        self.randomize_position()
        self.pulse = 0
        self.pulse_dir = 1

    def randomize_position(self):
        # --- MODIFICATION: Ensure food spawns within *new* playable bounds ---
        self.position = (random.randint(PLAYABLE_GRID_X_MIN, PLAYABLE_GRID_X_MAX),
                         random.randint(PLAYABLE_GRID_Y_MIN, PLAYABLE_GRID_Y_MAX))
        # --- END MODIFICATION ---

    def update(self):
        self.pulse += 0.1 * self.pulse_dir
        if self.pulse > 1: self.pulse_dir = -1
        elif self.pulse < 0: self.pulse_dir = 1

    def render(self, surface):
        # (No changes needed in food rendering itself)
        draw_x, draw_y = self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE
        rect = pygame.Rect(draw_x, draw_y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        inner_rect = pygame.Rect(rect.x + rect.width * 0.2, rect.y + rect.height * 0.2, rect.width * 0.6, rect.height * 0.6)
        pulse_color = (min(255, self.color[0] + int(30 * self.pulse)), min(255, self.color[1] + int(30 * self.pulse)), min(255, self.color[2] + int(30 * self.pulse)))
        pygame.draw.rect(surface, pulse_color, inner_rect, border_radius=6)

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.state = "START"
        self.speed = 10
        self.last_update = 0
        self.update_interval = 1000 // self.speed

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.state == "START":
                    if event.key == pygame.K_SPACE: self.reset_game()
                elif self.state == "PLAYING":
                    # Arrow key handling (no changes)
                    current_dx, current_dy = self.snake.direction
                    if event.key == pygame.K_UP and self.snake.direction != (0, 1): self.snake.direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1): self.snake.direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0): self.snake.direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0): self.snake.direction = (1, 0)
                    # Speed handling (no changes)
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS: self.increase_speed()
                    elif event.key == pygame.K_MINUS: self.decrease_speed()
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_SPACE: self.reset_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "GAME_OVER": self.check_button_click()

    def increase_speed(self):
        if self.speed < 20: self.speed += 1; self.update_interval = 1000 // self.speed

    def decrease_speed(self):
        if self.speed > 5: self.speed -= 1; self.update_interval = 1000 // self.speed

    def check_button_click(self):
        mouse_pos = pygame.mouse.get_pos()
        # Use the same calculation as render_game_over_screen for accuracy
        # We know the final score text rect relative position, calculate button from there
        center_x = WIDTH // 2
        over_rect_bottom = HEIGHT // 3 + font_large.get_height() # Approximate
        score_rect_bottom = over_rect_bottom + 40 + font_medium.get_height() # Approximate
        button_rect = pygame.Rect(0, 0, 200, 50); button_rect.center = (center_x, score_rect_bottom + 10) # Adjust center Y based on score text approx pos
        if button_rect.collidepoint(mouse_pos): self.reset_game()


    def reset_game(self):
        self.snake.reset()
        self.food.randomize_position()
        # Ensure food doesn't spawn on snake (uses new bounds)
        while self.food.position in self.snake.positions:
             self.food.randomize_position()
        self.state = "PLAYING"
        self.speed = 10
        self.update_interval = 1000 // self.speed
        self.last_update = pygame.time.get_ticks()

    def update(self):
        if self.state != "PLAYING":
             if self.state == "GAME_OVER": self.food.update()
             return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            if not self.snake.update(): # This now checks against tighter bounds
                self.state = "GAME_OVER"
                return
            if self.snake.get_head_position() == self.food.position:
                self.snake.grow()
                self.food.randomize_position()
                # Ensure food doesn't spawn on snake (uses new bounds)
                while self.food.position in self.snake.positions:
                    self.food.randomize_position()
        self.food.update()

    def render(self):
        screen.fill(BACKGROUND)
        self.draw_rounded_corners()
        # Draw full grid for background aesthetic
        for x in range(0, WIDTH, GRID_SIZE): pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE): pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

        # Render based on state
        if self.state == "START": self.render_start_screen()
        elif self.state == "PLAYING":
            self.food.render(screen)
            self.snake.render(screen) # Renders snake within the tighter bounds
            self.render_score()
        elif self.state == "GAME_OVER":
            # Render snake/food in final position first (which is now visually inside frame)
            self.food.render(screen)
            self.snake.render(screen)
            # Then render the overlay and text/button
            self.render_game_over_screen()
        pygame.display.flip()

    def draw_rounded_corners(self):
        # (No changes needed here)
        pygame.draw.circle(screen, FRAME_COLOR, (CORNER_RADIUS, CORNER_RADIUS), CORNER_RADIUS)
        pygame.draw.circle(screen, FRAME_COLOR, (WIDTH - CORNER_RADIUS, CORNER_RADIUS), CORNER_RADIUS)
        pygame.draw.circle(screen, FRAME_COLOR, (CORNER_RADIUS, HEIGHT - CORNER_RADIUS), CORNER_RADIUS)
        pygame.draw.circle(screen, FRAME_COLOR, (WIDTH - CORNER_RADIUS, HEIGHT - CORNER_RADIUS), CORNER_RADIUS)
        pygame.draw.rect(screen, FRAME_COLOR, (0, CORNER_RADIUS, CORNER_RADIUS, HEIGHT - 2 * CORNER_RADIUS))
        pygame.draw.rect(screen, FRAME_COLOR, (WIDTH - CORNER_RADIUS, CORNER_RADIUS, CORNER_RADIUS, HEIGHT - 2 * CORNER_RADIUS))
        pygame.draw.rect(screen, FRAME_COLOR, (CORNER_RADIUS, 0, WIDTH - 2 * CORNER_RADIUS, CORNER_RADIUS))
        pygame.draw.rect(screen, FRAME_COLOR, (CORNER_RADIUS, HEIGHT - CORNER_RADIUS, WIDTH - 2 * CORNER_RADIUS, CORNER_RADIUS))

    def render_score(self):
        # (No changes needed here)
        score_text = f"Score: {self.snake.score}"; speed_text = f"Speed: {self.speed}x"
        score_surface = font_small.render(score_text, True, SCORE_COLOR); speed_surface = font_small.render(speed_text, True, TEXT_COLOR)
        shadow_offset = 2; shadow_color = (0,0,0, 150)
        score_shadow_surface = font_small.render(score_text, True, shadow_color)
        score_pos_x = CORNER_RADIUS // 2 + 10; score_pos_y = CORNER_RADIUS // 2 + 5
        screen.blit(score_shadow_surface, (score_pos_x + shadow_offset, score_pos_y + shadow_offset)); screen.blit(score_surface, (score_pos_x, score_pos_y))
        speed_shadow_surface = font_small.render(speed_text, True, shadow_color)
        speed_pos_y = score_pos_y + 30
        screen.blit(speed_shadow_surface, (score_pos_x + shadow_offset, speed_pos_y + shadow_offset)); screen.blit(speed_surface, (score_pos_x, speed_pos_y))

    def render_start_screen(self):
        # (No changes needed here)
        center_x = WIDTH // 2
        title_text = "SLEEK SNAKE"; title_surface = font_large.render(title_text, True, SNAKE_COLOR)
        title_rect = title_surface.get_rect(center=(center_x, HEIGHT // 4)); screen.blit(title_surface, title_rect)
        subtitle_text = "A Modern Take on a Classic Game"; subtitle_surface = font_small.render(subtitle_text, True, TEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(center_x, title_rect.bottom + 20)); screen.blit(subtitle_surface, subtitle_rect)
        instructions = ["Use arrow keys to move", "Eat food to grow and score points", "+ / - to adjust speed", "Avoid hitting the walls or yourself!", "", "Press SPACE to start"]
        y_offset = subtitle_rect.bottom + 50
        for line in instructions: inst_surface = font_small.render(line, True, TEXT_COLOR); inst_rect = inst_surface.get_rect(center=(center_x, y_offset)); screen.blit(inst_surface, inst_rect); y_offset += 30

    def render_game_over_screen(self):
        # (No changes needed here)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((FRAME_COLOR[0], FRAME_COLOR[1], FRAME_COLOR[2], 200)); screen.blit(overlay, (0, 0))
        center_x = WIDTH // 2
        over_text = "GAME OVER"; over_surface = font_large.render(over_text, True, FOOD_COLOR)
        over_rect = over_surface.get_rect(center=(center_x, HEIGHT // 3)); screen.blit(over_surface, over_rect)
        score_text = f"Final Score: {self.snake.score}"; score_surface = font_medium.render(score_text, True, TEXT_COLOR)
        score_rect = score_surface.get_rect(center=(center_x, over_rect.bottom + 40)); screen.blit(score_surface, score_rect)
        button_rect = pygame.Rect(0, 0, 200, 50); button_rect.center = (center_x, score_rect.bottom + 60) # Position button relative to score text
        mouse_pos = pygame.mouse.get_pos(); button_color = BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        shadow_offset = 4; shadow_rect = button_rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(screen, (0, 0, 0, 150), shadow_rect, border_radius=10); pygame.draw.rect(screen, button_color, button_rect, border_radius=10)
        button_text = "Play Again"; button_surface = font_medium.render(button_text, True, TEXT_COLOR)
        text_rect = button_surface.get_rect(center=button_rect.center); screen.blit(button_surface, text_rect)
        restart_text = "or press SPACE to restart"; restart_surface = font_small.render(restart_text, True, TEXT_COLOR)
        restart_rect = restart_surface.get_rect(center=(center_x, button_rect.bottom + 25)); screen.blit(restart_surface, restart_rect)

# Main game loop
def main():
    game = Game()
    while True:
        game.handle_input()
        game.update()
        game.render()
        clock.tick(FPS)

if __name__ == "__main__":
    main()