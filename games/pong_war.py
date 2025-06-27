import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 25  # Increased grid size to match JS version
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 60
BALL_RADIUS = GRID_SIZE // 2  # Match ball size to grid size
MIN_SPEED = 5
MAX_SPEED = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# Colors inspired by the JS version
YIN_COLOR = (217, 232, 227)  # MysticMint (Light)
YIN_BALL_COLOR = (17, 76, 90)  # NocturnalExpedition
YANG_COLOR = (23, 43, 54)  # OceanicNoir (Dark)
YANG_BALL_COLOR = (217, 232, 227)  # MysticMint

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Pong War')
clock = pygame.time.Clock()

# Fonts - Use a nicer game-like font
try:
    # Try to load a nicer built-in font first with smaller size
    available_fonts = pygame.font.get_fonts()
    if 'comicsansms' in available_fonts:
        font = pygame.font.SysFont('comicsansms', 28)
    elif 'impact' in available_fonts:
        font = pygame.font.SysFont('impact', 28)
    elif 'verdana' in available_fonts:
        font = pygame.font.SysFont('verdana', 28)
    else:
        font = pygame.font.Font(None, 28)  # Default pygame font
except:
    font = pygame.font.SysFont('Arial', 28)  # Fallback

class Ball:
    def __init__(self, x, y, ball_color, team, reverse_color):
        self.x = x
        self.y = y
        self.radius = BALL_RADIUS
        self.ball_color = ball_color
        self.reverse_color = reverse_color
        self.team = team  # 0 for light, 1 for dark
        
        # Initial velocity (similar to JS version)
        if team == 0:  # Day team
            self.vx = 8
            self.vy = -8
        else:  # Night team
            self.vx = -8
            self.vy = 8
    
    def update(self, grid):
        # Check for collisions with squares
        self.check_square_collision(grid)
        
        # Check for collisions with walls
        self.check_boundary_collision()
        
        # Move the ball
        self.x += self.vx
        self.y += self.vy
        
        # Add randomness to movement (like in the JS version)
        self.add_randomness()
    
    def check_square_collision(self, grid):
        # Check multiple points around the ball's circumference (like in JS version)
        for angle in range(0, 360, 45):  # Check 8 points around the ball
            angle_rad = math.radians(angle)
            check_x = self.x + math.cos(angle_rad) * self.radius
            check_y = self.y + math.sin(angle_rad) * self.radius
            
            # Convert to grid coordinates
            grid_x = int(check_x // GRID_SIZE)
            grid_y = int(check_y // GRID_SIZE)
            
            if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                # If we hit a square of the opposite team
                if grid[grid_y][grid_x] != self.team:
                    # Change the square color to our team
                    grid[grid_y][grid_x] = self.team
                    
                    # Determine bounce direction based on the angle
                    if abs(math.cos(angle_rad)) > abs(math.sin(angle_rad)):
                        self.vx = -self.vx
                    else:
                        self.vy = -self.vy
                    
                    # Only bounce once per update
                    return
    
    def check_boundary_collision(self):
        if self.x + self.vx > WIDTH - self.radius or self.x + self.vx < self.radius:
            self.vx = -self.vx
        if self.y + self.vy > HEIGHT - self.radius or self.y + self.vy < self.radius:
            self.vy = -self.vy
    
    def add_randomness(self):
        # Add small random changes to velocity (like in JS version)
        self.vx += random.uniform(-0.02, 0.02)
        self.vy += random.uniform(-0.02, 0.02)
        
        # Limit the speed of the ball
        self.vx = max(min(self.vx, MAX_SPEED), -MAX_SPEED)
        self.vy = max(min(self.vy, MAX_SPEED), -MAX_SPEED)
        
        # Make sure the ball always maintains a minimum speed
        if abs(self.vx) < MIN_SPEED:
            self.vx = MIN_SPEED if self.vx > 0 else -MIN_SPEED
        if abs(self.vy) < MIN_SPEED:
            self.vy = MIN_SPEED if self.vy > 0 else -MIN_SPEED
    
    def draw(self):
        pygame.draw.circle(screen, self.ball_color, (int(self.x), int(self.y)), self.radius)

def initialize_grid():
    # -1 is unclaimed, 0 is light team, 1 is dark team
    grid = [[-1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    # Initialize left half for light team
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH // 2):
            grid[y][x] = 0
    
    # Initialize right half for dark team
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH // 2, GRID_WIDTH):
            grid[y][x] = 1
    
    return grid

def draw_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if grid[y][x] == 0:  # Yin team (Light)
                pygame.draw.rect(screen, YIN_COLOR, rect)
            elif grid[y][x] == 1:  # Yang team (Dark)
                pygame.draw.rect(screen, YANG_COLOR, rect)

def count_territories(grid):
    light_count = 0
    dark_count = 0
    
    for row in grid:
        for cell in row:
            if cell == 0:
                light_count += 1
            elif cell == 1:
                dark_count += 1
    
    return light_count, dark_count

def check_trapped(ball, grid):
    # Check if the ball is trapped (surrounded by opposite team's territory)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    grid_x = int(ball.x // GRID_SIZE)
    grid_y = int(ball.y // GRID_SIZE)
    
    for dx, dy in directions:
        nx, ny = grid_x + dx, grid_y + dy
        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
            # If there's any adjacent cell that's not the opposite team, the ball is not trapped
            if grid[ny][nx] != 1 - ball.team:
                return False
    
    return True

def main():
    # Initialize the grid
    grid = initialize_grid()
    
    # Create balls - using the colors from the JS version
    yin_ball = Ball(WIDTH // 4, HEIGHT // 2, YIN_BALL_COLOR, 0, YIN_COLOR)
    yang_ball = Ball(3 * WIDTH // 4, HEIGHT // 2, YANG_BALL_COLOR, 1, YANG_COLOR)
    
    balls = [yin_ball, yang_ball]
    
    # Game loop
    running = True
    game_over = False
    winner = None
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    # Reset the game
                    grid = initialize_grid()
                    yin_ball = Ball(WIDTH // 4, HEIGHT // 2, YIN_BALL_COLOR, 0, YIN_COLOR)
                    yang_ball = Ball(3 * WIDTH // 4, HEIGHT // 2, YANG_BALL_COLOR, 1, YANG_COLOR)
                    balls = [yin_ball, yang_ball]
                    game_over = False
                    winner = None
        
        if not game_over:
            # Update
            for ball in balls:
                ball.update(grid)
            
            # Check if any ball is trapped
            for i, ball in enumerate(balls):
                if check_trapped(ball, grid):
                    game_over = True
                    winner = 1 - i  # The other team wins
                    break
        
        # Draw
        screen.fill(BLACK)
        draw_grid(grid)
        
        for ball in balls:
            ball.draw()
        
        # Display territory counts
        light_count, dark_count = count_territories(grid)
        
        # Display the score with better visibility
        # Create a background for the score text for better readability
        score_text = font.render(f'yin {light_count} | yang {dark_count}', True, WHITE)
        text_width = score_text.get_width()
        text_height = score_text.get_height()
        text_x = WIDTH // 2 - text_width // 2
        text_y = HEIGHT - 40
        
        # Draw a semi-transparent rounded background for the text
        bg_rect = pygame.Rect(text_x - 15, text_y - 8, text_width + 30, text_height + 16)
        
        # Create a surface for the rounded rectangle
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw a rounded rectangle
        radius = 12  # Radius for rounded corners
        rect_width = bg_rect.width
        rect_height = bg_rect.height
        
        # Draw the rounded rectangle with semi-transparency
        pygame.draw.rect(bg_surface, (0, 0, 0, 180), (0, 0, rect_width, rect_height), border_radius=radius)
        
        # Blit the rounded rectangle surface
        screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
        
        # Draw the score text
        screen.blit(score_text, (text_x, text_y))
        
        # Display game over message if applicable
        if game_over:
            if winner == 0:
                message = 'Yin wins! Press R to restart.'
                color = YIN_COLOR
            else:
                message = 'Yang wins! Press R to restart.'
                color = YANG_COLOR
            
            # Create a larger, nicer font for the game over message
            try:
                # Try to load a nicer built-in font first
                available_fonts = pygame.font.get_fonts()
                if 'comicsansms' in available_fonts:
                    game_over_font = pygame.font.SysFont('comicsansms', 40)
                elif 'impact' in available_fonts:
                    game_over_font = pygame.font.SysFont('impact', 40)
                elif 'verdana' in available_fonts:
                    game_over_font = pygame.font.SysFont('verdana', 40)
                else:
                    game_over_font = pygame.font.Font(None, 40)  # Default pygame font
            except:
                game_over_font = pygame.font.SysFont('Arial', 40)  # Fallback
                
            text = game_over_font.render(message, True, color)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            
            # Add a rounded background to the game over message
            bg_rect = pygame.Rect(text_rect.x - 25, text_rect.y - 15, text_rect.width + 50, text_rect.height + 30)
            
            # Create a surface for the rounded rectangle
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 0))  # Transparent background
            
            # Draw a rounded rectangle
            radius = 18  # Larger radius for game over message
            rect_width = bg_rect.width
            rect_height = bg_rect.height
            
            # Draw the rounded rectangle with semi-transparency
            pygame.draw.rect(bg_surface, (0, 0, 0, 200), (0, 0, rect_width, rect_height), border_radius=radius)
            
            # Blit the rounded rectangle surface
            screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
            
            screen.blit(text, text_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
