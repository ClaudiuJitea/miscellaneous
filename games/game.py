import pygame
import random
import sys
import time
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 20

# Colors
BACKGROUND = (15, 18, 24)
GRID_COLOR = (30, 33, 39)
SNAKE_HEAD_COLOR = (41, 128, 185)
SNAKE_BODY_COLOR = (32, 79, 137)
FOOD_COLOR = (237, 68, 78)
TEXT_COLOR = (200, 200, 200)
GAME_OVER_BG = (0, 0, 0, 180)  # Semi-transparent black

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Modern Snake")
clock = pygame.time.Clock()

# Fonts
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

class Snake:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.length = 4
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        self.score = 0
        self.grow_to = 4
        
    def get_head_position(self):
        return self.positions[0]
    
    def update_direction(self, direction):
        # Prevent 180-degree turns
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.direction = direction
            
    def move(self):
        head_x, head_y = self.get_head_position()
        dir_x, dir_y = self.direction
        new_x = (head_x + dir_x) % GRID_WIDTH
        new_y = (head_y + dir_y) % GRID_HEIGHT
        
        # Check for collision with self
        if (new_x, new_y) in self.positions[1:]:
            return False
        
        # Move the snake
        self.positions.insert(0, (new_x, new_y))
        
        # Grow or keep length
        if len(self.positions) > self.grow_to:
            self.positions.pop()
            
        return True
    
    def grow(self):
        self.grow_to += 1
        self.score += 10
        
    def draw(self, surface):
        # Draw snake body
        for i, (x, y) in enumerate(self.positions):
            color_intensity = 255 - (int(i / len(self.positions) * 200) if i >= len(self.positions) else 0)
            if i == 0:
                color = SNAKE_HEAD_COLOR
            else:
                color = (
                    max(0, min(255, SNAKE_BODY_COLOR[0] + (i % 5 * 2))),
                    max(0, min(255, SNAKE_BODY_COLOR[1] + (i % 4 * 2))),
                    max(0, min(255, SNAKE_BODY_COLOR[2] + (i % 3 * 2)))
                )
            
            # Draw smooth circle for each segment
            rect = pygame.Rect(
                x * GRID_SIZE, 
                y * GRID_SIZE, 
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(surface, color, rect, border_radius=5)
            
            # Add a shine effect to each segment
            if i > 0:
                shine_rect = pygame.Rect(
                    x * GRID_SIZE + 2, 
                    y * GRID_SIZE + 2, 
                    GRID_SIZE - 6, GRID_SIZE - 6
                )
                pygame.draw.rect(surface, (255, 255, 255, 30), shine_rect, border_radius=3)
    
    def check_collision_with_food(self, pos):
        return self.get_head_position() == pos

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position()
        
    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1),
            random.randint(0, GRID_HEIGHT - 1)
        )
        
    def draw(self, surface):
        x, y = self.position
        rect = pygame.Rect(
            x * GRID_SIZE, 
            y * GRID_SIZE, 
            GRID_SIZE, GRID_SIZE
        )
        # Draw apple-like food
        pygame.draw.circle(
            surface, 
            FOOD_COLOR,
            rect.center,
            GRID_SIZE // 2 - 1
        )
        # Draw stem
        stem_rect = pygame.Rect(
            x * GRID_SIZE + GRID_SIZE // 2 - 2,
            y * GRID_SIZE - 3,
            4, 6
        )
        pygame.draw.ellipse(surface, (139, 69, 19), stem_rect)

def draw_grid(surface):
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y))

def draw_ui(surface, snake, state):
    # Draw score
    score_text = font_medium.render(f"Score: {snake.score}", True, TEXT_COLOR)
    surface.blit(score_text, (20, HEIGHT - 40))
    
    # Draw length indicator
    length_text = font_small.render(f"Length: {snake.grow_to}", True, TEXT_COLOR)
    surface.blit(length_text, (WIDTH - 200, HEIGHT - 40))

def draw_menu(surface, state=""):
    state = state.lower()
    surface.fill(BACKGROUND)
    draw_grid(surface)
    
    # Title
    title = font_large.render("MODERN SNAKE", True, SNAKE_HEAD_COLOR)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    surface.blit(title, title_rect)
    
    # Instructions
    if state == "game_over":
        instruction = font_medium.render("GAME OVER", True, FOOD_COLOR)
    else:
        instruction = font_small.render("Press SPACE to Start", True, TEXT_COLOR)
    
    instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(instruction, instruction_rect)
    
    # Draw a snake as placeholder
    for i in range(5):
        # Head
        head_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT // 2 + 50, 25, 25)
        pygame.draw.rect(surface, SNAKE_HEAD_COLOR, head_rect, border_radius=5)
        
        # Body segments
        for i in range(4):
            x_offset = (-i) * 15
            body_rect = pygame.Rect(WIDTH // 2 - 20 + x_offset, HEIGHT // 2 + 50, 15, 20)
            pygame.draw.rect(surface, SNAKE_BODY_COLOR, body_rect, border_radius=3)

def draw_game_over(surface, score):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(GAME_OVER_BG)
    surface.blit(overlay, (0, 0))
    
    # Game over text
    game_over = font_large.render("GAME OVER", True, FOOD_COLOR)
    game_over_rect = game_over.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    surface.blit(game_over, game_over_rect)
    
    # Final score
    score_text = font_medium.render(f"Final Score: {score}", True, TEXT_COLOR)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(score_text, score_rect)
    
    # Restart button
    restart_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 80, 300, 50)
    pygame.draw.rect(surface, (50, 50, 50), restart_button, border_radius=10)
    pygame.draw.rect(surface, SNAKE_HEAD_COLOR, restart_button, width=2, border_radius=10)
    
    restart_text = font_small.render("RESTART", True, TEXT_COLOR)
    restart_text_rect = restart_text.get_rect(center=restart_button.center)
    surface.blit(restart_text, restart_text_rect)
    
    return restart_button

def main():
    snake = Snake()
    food = Food()
    
    game_state = MENU
    last_direction = snake.direction
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if event.key == pygame.K_SPACE:
                        game_state = PLAYING
                
                elif game_state == PLAYING:
                    if event.key == pygame.K_UP:
                        snake.update_direction((0, -1))
                    elif event.key == pygame.K_DOWN:
                        snake.update_direction((0, 1))
                    elif event.key == pygame.K_LEFT:
                        snake.update_direction((-1, 0))
                    elif event.key == pygame.K_RIGHT:
                        snake.update_direction((1, 0))
                    elif event.key == pygame.K_ESCAPE:
                        game_state = MENU
                
                elif game_state == GAME_OVER:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        snake.reset()
                        food.randomize_position()
                        game_state = PLAYING
        
        # Fill the background
        screen.fill(BACKGROUND)
        draw_grid(screen)
        
        # Game logic based on state
        if game_state == MENU:
            draw_menu(screen)
            
        elif game_state == PLAYING:
            # Get keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] and last_direction != (0, 1):
                snake.update_direction((0, -1))
                last_direction = (0, -1)
            elif keys[pygame.K_DOWN] and last_direction != (0, -1):
                snake.update_direction((0, 1))
                last_direction = (0, 1)
            elif keys[pygame.K_LEFT] and last_direction != (0, 1):
                snake.update_direction((-1, 0))
                last_direction = (-1, 0)
            elif keys[pygame.K_RIGHT] and last_direction != (0, -1):
                snake.update_direction((1, 0))
                last_direction = (1, 0)
                
            # Move snake
            if not snake.move():
                game_state = GAME_OVER
                continue
                
            # Check for food
            if snake.check_collision_with_food(food.position):
                snake.grow()
                food.randomize_position()
                # Make sure food doesn't appear on snake
                while food.position in snake.positions:
                    food.randomize_position()
            
            # Draw game elements
            snake.draw(screen)
            food.draw(screen)
            draw_ui(screen, snake, PLAYING)
            
        elif game_state == GAME_OVER:
            snake.draw(screen)
            food.draw(screen)
            draw_ui(screen, snake, "game_over")
            
            # Check for restart button click
            restart_button = draw_game_over(screen, snake.score)
            
            # Get mouse position
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if mouse is over button
            if restart_button.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                snake.reset()
                food.randomize_position()
                game_state = PLAYING
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
