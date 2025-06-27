import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
import time
import math

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class Colors:
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    BG_LIGHT = "#0f3460"
    ACCENT_PRIMARY = "#e94560"
    ACCENT_SECONDARY = "#00b4d8"
    TEXT_LIGHT = "#ffffff"
    TEXT_DARK = "#d6e5fa"
    HOVER = "#533483"
    X_COLOR = "#e94560"  # Red
    O_COLOR = "#00b4d8"  # Blue
    GRID_COLOR = "#30475e"
    WIN_LINE_COLOR = "#f5f5f5"

class TicTacToeGame(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Modern Tic Tac Toe")
        self.geometry("600x700")
        self.configure(fg_color=Colors.BG_DARK)
        self.resizable(False, False)
        
        # Game variables
        self.current_player = "X"
        self.board = ["", "", "", "", "", "", "", "", ""]
        self.game_active = True
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0
        self.animation_speed = 0.3  # seconds
        self.winning_line = None
        self.game_mode = "player_vs_computer"  # Default mode
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color=Colors.BG_DARK)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_DARK)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="TIC TAC TOE", 
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color=Colors.TEXT_LIGHT
        )
        self.title_label.pack(pady=10)
        
        # Mode selection
        self.mode_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_MEDIUM, corner_radius=10)
        self.mode_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        self.mode_var = tk.StringVar(value="player_vs_computer")
        
        self.pvc_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Player vs Computer",
            variable=self.mode_var,
            value="player_vs_computer",
            command=self.reset_game,
            fg_color=Colors.ACCENT_PRIMARY,
            border_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.HOVER,
            text_color=Colors.TEXT_LIGHT
        )
        self.pvc_radio.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.pvp_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Player vs Player",
            variable=self.mode_var,
            value="player_vs_player",
            command=self.reset_game,
            fg_color=Colors.ACCENT_PRIMARY,
            border_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.HOVER,
            text_color=Colors.TEXT_LIGHT
        )
        self.pvp_radio.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Score frame
        self.score_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_MEDIUM, corner_radius=10)
        self.score_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        # X score
        self.x_score_frame = ctk.CTkFrame(self.score_frame, fg_color=Colors.BG_MEDIUM)
        self.x_score_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10, pady=10)
        
        self.x_label = ctk.CTkLabel(
            self.x_score_frame,
            text="X",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color=Colors.X_COLOR
        )
        self.x_label.pack()
        
        self.x_score_label = ctk.CTkLabel(
            self.x_score_frame,
            text="0",
            font=ctk.CTkFont(family="Arial", size=20),
            text_color=Colors.TEXT_LIGHT
        )
        self.x_score_label.pack()
        
        # Draws
        self.draws_frame = ctk.CTkFrame(self.score_frame, fg_color=Colors.BG_MEDIUM)
        self.draws_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10, pady=10)
        
        self.draws_label = ctk.CTkLabel(
            self.draws_frame,
            text="DRAWS",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color=Colors.TEXT_LIGHT
        )
        self.draws_label.pack()
        
        self.draws_score_label = ctk.CTkLabel(
            self.draws_frame,
            text="0",
            font=ctk.CTkFont(family="Arial", size=20),
            text_color=Colors.TEXT_LIGHT
        )
        self.draws_score_label.pack()
        
        # O score
        self.o_score_frame = ctk.CTkFrame(self.score_frame, fg_color=Colors.BG_MEDIUM)
        self.o_score_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10, pady=10)
        
        self.o_label = ctk.CTkLabel(
            self.o_score_frame,
            text="O",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color=Colors.O_COLOR
        )
        self.o_label.pack()
        
        self.o_score_label = ctk.CTkLabel(
            self.o_score_frame,
            text="0",
            font=ctk.CTkFont(family="Arial", size=20),
            text_color=Colors.TEXT_LIGHT
        )
        self.o_score_label.pack()
        
        # Turn indicator
        self.turn_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_MEDIUM, corner_radius=10)
        self.turn_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        self.turn_label = ctk.CTkLabel(
            self.turn_frame,
            text="X's Turn",
            font=ctk.CTkFont(family="Arial", size=18),
            text_color=Colors.X_COLOR
        )
        self.turn_label.pack(pady=10)
        
        # Game board
        self.board_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_LIGHT, corner_radius=10)
        self.board_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 20))
        
        # Create canvas for drawing the board
        self.canvas = tk.Canvas(
            self.board_frame,
            bg=Colors.BG_LIGHT,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.draw_board)
        
        # Bottom buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.BG_DARK)
        self.button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.reset_button = ctk.CTkButton(
            self.button_frame,
            text="Reset Game",
            command=self.reset_game,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.HOVER,
            corner_radius=10,
            font=ctk.CTkFont(family="Arial", size=16)
        )
        self.reset_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        
        self.new_game_button = ctk.CTkButton(
            self.button_frame,
            text="New Game",
            command=self.new_game,
            fg_color=Colors.ACCENT_SECONDARY,
            hover_color=Colors.HOVER,
            corner_radius=10,
            font=ctk.CTkFont(family="Arial", size=16)
        )
        self.new_game_button.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.X, expand=True)
    
    def draw_board(self, event=None):
        self.canvas.delete("board")
        
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Calculate cell size and offset to center the grid
        size = min(width, height)
        self.cell_size = size / 3
        
        # Calculate offsets to center the grid
        x_offset = (width - size) / 2
        y_offset = (height - size) / 2
        
        # Draw grid lines
        line_width = 4
        
        # Vertical lines
        self.canvas.create_line(
            x_offset + self.cell_size, y_offset + 10, 
            x_offset + self.cell_size, y_offset + size - 10,
            width=line_width, fill=Colors.GRID_COLOR, tags="board"
        )
        self.canvas.create_line(
            x_offset + 2 * self.cell_size, y_offset + 10, 
            x_offset + 2 * self.cell_size, y_offset + size - 10,
            width=line_width, fill=Colors.GRID_COLOR, tags="board"
        )
        
        # Horizontal lines
        self.canvas.create_line(
            x_offset + 10, y_offset + self.cell_size, 
            x_offset + size - 10, y_offset + self.cell_size,
            width=line_width, fill=Colors.GRID_COLOR, tags="board"
        )
        self.canvas.create_line(
            x_offset + 10, y_offset + 2 * self.cell_size, 
            x_offset + size - 10, y_offset + 2 * self.cell_size,
            width=line_width, fill=Colors.GRID_COLOR, tags="board"
        )
        
        # Store offsets for use in other methods
        self.x_offset = x_offset
        self.y_offset = y_offset
        
        # Bind click event
        self.canvas.bind("<Button-1>", self.handle_click)
        
        # Redraw pieces
        self.redraw_pieces()
    
    def redraw_pieces(self):
        self.canvas.delete("piece")
        
        for i in range(9):
            row, col = i // 3, i % 3
            if self.board[i] == "X":
                self.draw_x(row, col, animate=False)
            elif self.board[i] == "O":
                self.draw_o(row, col, animate=False)
        
        # Redraw winning line if exists
        if self.winning_line:
            self.draw_winning_line(*self.winning_line)
    
    def handle_click(self, event):
        if not self.game_active:
            return
        
        # Adjust click coordinates to account for grid offset
        adjusted_x = event.x - self.x_offset
        adjusted_y = event.y - self.y_offset
        
        # Calculate which cell was clicked
        col = int(adjusted_x // self.cell_size)
        row = int(adjusted_y // self.cell_size)
        
        # Ensure valid cell
        if col < 0 or col > 2 or row < 0 or row > 2:
            return
        
        index = row * 3 + col
        
        # Check if cell is empty
        if self.board[index] == "":
            # Update board
            self.board[index] = self.current_player
            
            # Draw the piece with animation
            if self.current_player == "X":
                self.draw_x(row, col)
            else:
                self.draw_o(row, col)
            
            # Check for win or draw
            if self.check_winner():
                self.game_active = False
                if self.current_player == "X":
                    self.player_score += 1
                    self.x_score_label.configure(text=str(self.player_score))
                else:
                    self.computer_score += 1
                    self.o_score_label.configure(text=str(self.computer_score))
                
                # Update turn label
                self.turn_label.configure(
                    text=f"{self.current_player} Wins!",
                    text_color=Colors.X_COLOR if self.current_player == "X" else Colors.O_COLOR
                )
                
                # Schedule reset after delay
                self.after(2000, self.reset_board)
            elif "" not in self.board:
                self.game_active = False
                self.draws += 1
                self.draws_score_label.configure(text=str(self.draws))
                self.turn_label.configure(text="Draw!", text_color=Colors.TEXT_LIGHT)
                
                # Schedule reset after delay
                self.after(2000, self.reset_board)
            else:
                # Switch player
                self.current_player = "O" if self.current_player == "X" else "X"
                
                # Update turn label
                self.turn_label.configure(
                    text=f"{self.current_player}'s Turn",
                    text_color=Colors.X_COLOR if self.current_player == "X" else Colors.O_COLOR
                )
                
                # If playing against computer and it's O's turn
                if self.game_mode == "player_vs_computer" and self.current_player == "O" and self.game_active:
                    self.after(500, self.computer_move)
    
    def computer_move(self):
        if not self.game_active:
            return
        
        # Check for winning move
        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "O"
                if self.check_winner(check_only=True):
                    row, col = i // 3, i % 3
                    self.draw_o(row, col)
                    
                    # Update score
                    self.computer_score += 1
                    self.o_score_label.configure(text=str(self.computer_score))
                    
                    # Update turn label
                    self.turn_label.configure(text="O Wins!", text_color=Colors.O_COLOR)
                    
                    self.game_active = False
                    
                    # Schedule reset after delay
                    self.after(2000, self.reset_board)
                    return
                self.board[i] = ""
        
        # Check for blocking move
        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "X"
                if self.check_winner(check_only=True):
                    self.board[i] = "O"
                    row, col = i // 3, i % 3
                    self.draw_o(row, col)
                    
                    # Check if this is a winning move for O
                    if self.check_winner():
                        # Update score
                        self.computer_score += 1
                        self.o_score_label.configure(text=str(self.computer_score))
                        
                        # Update turn label
                        self.turn_label.configure(text="O Wins!", text_color=Colors.O_COLOR)
                        
                        self.game_active = False
                        
                        # Schedule reset after delay
                        self.after(2000, self.reset_board)
                        return
                    
                    # Switch player
                    self.current_player = "X"
                    
                    # Update turn label
                    self.turn_label.configure(text="X's Turn", text_color=Colors.X_COLOR)
                    
                    # Check for draw
                    if "" not in self.board:
                        self.game_active = False
                        self.draws += 1
                        self.draws_score_label.configure(text=str(self.draws))
                        self.turn_label.configure(text="Draw!", text_color=Colors.TEXT_LIGHT)
                        
                        # Schedule reset after delay
                        self.after(2000, self.reset_board)
                    
                    return
                self.board[i] = ""
        
        # Try center
        if self.board[4] == "":
            self.board[4] = "O"
            row, col = 1, 1
            self.draw_o(row, col)
        else:
            # Random move
            empty_cells = [i for i, cell in enumerate(self.board) if cell == ""]
            if empty_cells:
                index = random.choice(empty_cells)
                self.board[index] = "O"
                row, col = index // 3, index % 3
                self.draw_o(row, col)
        
        # Check for win
        if self.check_winner():
            # Update score
            self.computer_score += 1
            self.o_score_label.configure(text=str(self.computer_score))
            
            # Update turn label
            self.turn_label.configure(text="O Wins!", text_color=Colors.O_COLOR)
            
            self.game_active = False
            
            # Schedule reset after delay
            self.after(2000, self.reset_board)
            return
        
        # Check for draw
        if "" not in self.board:
            self.game_active = False
            self.draws += 1
            self.draws_score_label.configure(text=str(self.draws))
            self.turn_label.configure(text="Draw!", text_color=Colors.TEXT_LIGHT)
            
            # Schedule reset after delay
            self.after(2000, self.reset_board)
            return
        
        # Switch player
        self.current_player = "X"
        
        # Update turn label
        self.turn_label.configure(text="X's Turn", text_color=Colors.X_COLOR)
    
    def draw_x(self, row, col, animate=True):
        # Calculate center of cell with offset
        x_center = self.x_offset + col * self.cell_size + self.cell_size / 2
        y_center = self.y_offset + row * self.cell_size + self.cell_size / 2
        
        # Size of X
        size = self.cell_size * 0.3
        
        if animate:
            # Animation steps
            steps = 10
            step_size = size / steps
            
            for i in range(1, steps + 1):
                current_size = step_size * i
                
                # Delete previous frame
                self.canvas.delete("temp_x")
                
                # Draw X with current size
                self.canvas.create_line(
                    x_center - current_size, y_center - current_size,
                    x_center + current_size, y_center + current_size,
                    width=8, fill=Colors.X_COLOR, tags="temp_x"
                )
                self.canvas.create_line(
                    x_center + current_size, y_center - current_size,
                    x_center - current_size, y_center + current_size,
                    width=8, fill=Colors.X_COLOR, tags="temp_x"
                )
                
                # Update canvas
                self.update()
                time.sleep(self.animation_speed / steps)
            
            # Delete temporary animation
            self.canvas.delete("temp_x")
        
        # Draw final X
        self.canvas.create_line(
            x_center - size, y_center - size,
            x_center + size, y_center + size,
            width=8, fill=Colors.X_COLOR, tags="piece"
        )
        self.canvas.create_line(
            x_center + size, y_center - size,
            x_center - size, y_center + size,
            width=8, fill=Colors.X_COLOR, tags="piece"
        )
    
    def draw_o(self, row, col, animate=True):
        # Calculate center of cell with offset
        x_center = self.x_offset + col * self.cell_size + self.cell_size / 2
        y_center = self.y_offset + row * self.cell_size + self.cell_size / 2
        
        # Size of O
        radius = self.cell_size * 0.3
        
        if animate:
            # Animation steps
            steps = 10
            step_size = radius / steps
            
            for i in range(1, steps + 1):
                current_radius = step_size * i
                
                # Delete previous frame
                self.canvas.delete("temp_o")
                
                # Draw O with current radius
                self.canvas.create_oval(
                    x_center - current_radius, y_center - current_radius,
                    x_center + current_radius, y_center + current_radius,
                    width=8, outline=Colors.O_COLOR, tags="temp_o"
                )
                
                # Update canvas
                self.update()
                time.sleep(self.animation_speed / steps)
            
            # Delete temporary animation
            self.canvas.delete("temp_o")
        
        # Draw final O
        self.canvas.create_oval(
            x_center - radius, y_center - radius,
            x_center + radius, y_center + radius,
            width=8, outline=Colors.O_COLOR, tags="piece"
        )
    
    def check_winner(self, check_only=False):
        # Winning combinations
        win_combinations = [
            # Rows
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            # Columns
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            # Diagonals
            [0, 4, 8], [2, 4, 6]
        ]
        
        for combo in win_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != ""):
                if not check_only:
                    # Store winning line info for drawing
                    self.winning_line = combo
                    self.draw_winning_line(combo)
                return True
        
        return False
    
    def draw_winning_line(self, combo):
        # Calculate start and end points of the winning line
        start_idx, end_idx = combo[0], combo[2]
        
        # For middle row and column, use the actual middle index
        if combo in [[0, 1, 2], [3, 4, 5], [6, 7, 8]]:  # Rows
            start_idx, end_idx = combo[0], combo[2]
        elif combo in [[0, 3, 6], [1, 4, 7], [2, 5, 8]]:  # Columns
            start_idx, end_idx = combo[0], combo[2]
        
        # Calculate cell centers
        start_row, start_col = start_idx // 3, start_idx % 3
        end_row, end_col = end_idx // 3, end_idx % 3
        
        # Get cell centers with offset
        start_x = self.x_offset + start_col * self.cell_size + self.cell_size / 2
        start_y = self.y_offset + start_row * self.cell_size + self.cell_size / 2
        end_x = self.x_offset + end_col * self.cell_size + self.cell_size / 2
        end_y = self.y_offset + end_row * self.cell_size + self.cell_size / 2
        
        # For diagonals, adjust to use corners
        if combo == [0, 4, 8]:  # Main diagonal
            start_x = self.x_offset + 10
            start_y = self.y_offset + 10
            end_x = self.x_offset + self.cell_size * 3 - 10
            end_y = self.y_offset + self.cell_size * 3 - 10
        elif combo == [2, 4, 6]:  # Other diagonal
            start_x = self.x_offset + self.cell_size * 3 - 10
            start_y = self.y_offset + 10
            end_x = self.x_offset + 10
            end_y = self.y_offset + self.cell_size * 3 - 10
        
        # Draw the line
        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            width=10, fill=Colors.WIN_LINE_COLOR, tags="piece",
            capstyle=tk.ROUND
        )
    
    def reset_board(self):
        # Clear board
        self.board = ["", "", "", "", "", "", "", "", ""]
        self.canvas.delete("piece")
        self.winning_line = None
        
        # Reset game state
        self.game_active = True
        self.current_player = "X"
        
        # Update turn label
        self.turn_label.configure(text="X's Turn", text_color=Colors.X_COLOR)
        
        # If playing against computer and it's O's turn
        if self.game_mode == "player_vs_computer" and self.current_player == "O":
            self.after(500, self.computer_move)
    
    def reset_game(self):
        # Update game mode
        self.game_mode = self.mode_var.get()
        
        # Reset board
        self.reset_board()
    
    def new_game(self):
        # Reset scores
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0
        
        # Update score labels
        self.x_score_label.configure(text="0")
        self.o_score_label.configure(text="0")
        self.draws_score_label.configure(text="0")
        
        # Reset board
        self.reset_game()

if __name__ == "__main__":
    app = TicTacToeGame()
    app.mainloop()
