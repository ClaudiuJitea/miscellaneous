import customtkinter as ctk
import math
from CTkToolTip import CTkToolTip  # For tooltips

class Calculator(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Calculator")
        self.geometry("400x600")  # Increased base window size
        self.resizable(False, False)
        
        # Set the theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Variables
        self.current_expression = "0"
        self.display_var = ctk.StringVar(value="0")
        self.memory = 0
        self.memory_used = False
        self.memory_display = ctk.StringVar(value="")
        self.last_was_operator = False
        self.last_was_equals = False
        self.calculation_history = []
        self.scientific_mode = False
        self.history_window = None

        # Configure main window grid
        self.grid_columnconfigure(0, weight=1)
        for i in range(4):
            self.grid_rowconfigure(i, weight=1)

        # Create the UI
        self.create_widgets()
        
        # Bind keyboard events
        self.bind('<Key>', self.handle_keypress)

    def format_number(self, number_str):
        try:
            # Convert string to float
            number = float(number_str)
            
            # If number is too large or has too many decimals
            if abs(number) > 1e16:
                return "{:.10e}".format(number)
            else:
                # Format number to maximum 12 decimal places
                formatted = "{:.12f}".format(number).rstrip('0').rstrip('.')
                if len(formatted) > 16:
                    return "{:.10e}".format(number)
                return formatted
        except:
            return number_str

    def create_widgets(self):
        # Display frame
        display_frame = ctk.CTkFrame(self, fg_color="transparent")
        display_frame.grid(row=0, column=0, columnspan=4, padx=15, pady=(15, 5), sticky="nsew")

        # Display label
        display = ctk.CTkLabel(
            display_frame,
            textvariable=self.display_var,
            font=("Segoe UI", 36),  # Increased font size
            anchor="e",
            wraplength=350  # Increased wraplength
        )
        display.pack(fill="both", expand=True, padx=15)

        # Memory display
        memory_frame = ctk.CTkFrame(self, fg_color="transparent")
        memory_frame.grid(row=1, column=0, columnspan=4, padx=15, pady=5, sticky="nsew")

        self.memory_label = ctk.CTkLabel(
            memory_frame,
            textvariable=self.memory_display,
            font=("Segoe UI", 12),
            text_color="gray"
        )
        self.memory_label.pack(anchor="w", padx=15)

        # Control buttons frame (Memory, Mode, History)
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.grid(row=2, column=0, columnspan=4, padx=15, pady=5, sticky="nsew")

        # Configure control frame grid
        for i in range(7):
            control_frame.grid_columnconfigure(i, weight=1)

        # Memory buttons
        memory_buttons = ['MC', 'MR', 'M+', 'M-', 'MS']
        for i, text in enumerate(memory_buttons):
            btn = ctk.CTkButton(
                control_frame,
                text=text,
                width=50,
                height=35,
                font=("Segoe UI", 12),
                fg_color="transparent",
                text_color="gray",
                hover_color=("gray85", "gray25"),
                command=lambda t=text: self.handle_memory(t)
            )
            btn.grid(row=0, column=i, padx=3)

        # Mode and History buttons
        mode_button = ctk.CTkButton(
            control_frame,
            text="Mode",
            width=50,
            height=35,
            font=("Segoe UI", 12),
            fg_color="#2F58CD",
            command=self.toggle_mode
        )
        mode_button.grid(row=0, column=5, padx=3)

        history_button = ctk.CTkButton(
            control_frame,
            text="History",
            width=50,
            height=35,
            font=("Segoe UI", 12),
            fg_color="#2F58CD",
            command=self.show_history
        )
        history_button.grid(row=0, column=6, padx=3)

        # Main buttons frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=4, padx=15, pady=10, sticky="nsew")

        # Configure button frame grid
        max_rows = 7 if self.scientific_mode else 6
        for i in range(max_rows):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

        # Create buttons
        buttons = self.scientific_buttons() if self.scientific_mode else self.standard_buttons()
        button_width = 80
        button_height = 55

        for i, row in enumerate(buttons):
            for j, text in enumerate(row):
                is_equals = text == '='
                btn = ctk.CTkButton(
                    button_frame,
                    text=text,
                    width=button_width,
                    height=button_height,
                    font=("Segoe UI", 18),  # Increased font size
                    fg_color=("#2F58CD" if is_equals else ("gray85", "gray25")),
                    text_color="white",
                    hover_color=("#2648B0" if is_equals else ("gray75", "gray35")),
                    command=lambda t=text: self.handle_button_press(t)
                )
                btn.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")  # Reduced padding

    def update_memory_display(self):
        if self.memory_used:
            self.memory_display.set(f"Memory: {self.format_number(str(self.memory))}")
        else:
            self.memory_display.set("Memory add (Ctrl+P)")

    def handle_memory(self, operation):
        try:
            current_value = float(self.current_expression.split()[-1] if ' ' in self.current_expression else self.current_expression)
            
            if operation == 'MC':
                self.memory = 0
                self.memory_used = False
            elif operation == 'MR':
                if self.memory_used:
                    self.current_expression = self.format_number(str(self.memory))
                    self.display_var.set(self.current_expression)
                    self.last_was_equals = True
            elif operation == 'M+':
                self.memory += current_value
                self.memory_used = True
            elif operation == 'M-':
                self.memory -= current_value
                self.memory_used = True
            elif operation == 'MS':
                self.memory = current_value
                self.memory_used = True
            elif operation == 'M˅':
                # Show memory value temporarily
                if self.memory_used:
                    temp_display = self.current_expression
                    self.current_expression = self.format_number(str(self.memory))
                    self.display_var.set(self.current_expression)
                    self.after(1000, lambda: self.display_var.set(temp_display))
            
            self.update_memory_display()
        except:
            pass

    def handle_keypress(self, event):
        key = event.char
        if key in '0123456789':
            self.handle_button_press(key)
        elif key == '\r':  # Enter key
            self.handle_button_press('=')
        elif key == '\x08':  # Backspace
            self.handle_button_press('⌫')
        elif key == '.':
            self.handle_button_press('.')
        elif key in '+-*/':
            op_map = {'+': '+', '-': '-', '*': '×', '/': '÷'}
            self.handle_button_press(op_map[key])
        elif key == 'c':
            self.handle_button_press('C')
            
    def toggle_mode(self):
        self.scientific_mode = not self.scientific_mode
        if self.scientific_mode:
            self.geometry("400x700")  # Increased height for scientific mode
        else:
            self.geometry("400x600")  # Standard mode height
        self.create_widgets()
        
    def show_history(self):
        if self.history_window is None or not self.history_window.winfo_exists():
            self.history_window = ctk.CTkToplevel(self)
            self.history_window.title("Calculation History")
            self.history_window.geometry("300x350")
            
            history_text = ctk.CTkTextbox(self.history_window, width=280, height=350)
            history_text.pack(padx=10, pady=10)
            
            for calc in reversed(self.calculation_history):
                history_text.insert('end', f"{calc}\n")
            
            clear_button = ctk.CTkButton(
                self.history_window,
                text="Clear History",
                command=lambda: [self.calculation_history.clear(), self.history_window.destroy()]
            )
            clear_button.pack(pady=5)

    def handle_button_press(self, button):
        if button == 'C' or button == 'CE':
            self.clear()
        elif button == '⌫':
            self.backspace()
        elif button == '=':
            self.calculate()
        elif button in ['%', '±', '¹/x', 'x²', '√x']:
            self.handle_special_operation(button)
        elif button in ['÷', '×', '-', '+']:
            self.handle_operator(button)
        elif button == '.':
            self.handle_decimal()
        else:
            self.handle_number(button)

        # Format the display before updating
        if self.current_expression not in ["Error", "Cannot divide by zero", "Invalid input"]:
            parts = self.current_expression.split()
            if len(parts) > 0:
                last_part = parts[-1]
                if not any(op in last_part for op in ['÷', '×', '-', '+']):
                    parts[-1] = self.format_number(last_part)
                self.current_expression = ' '.join(parts)
        
        self.display_var.set(self.current_expression)

    def handle_number(self, number):
        if self.last_was_equals:
            self.current_expression = "0"
            self.last_was_equals = False

        if self.current_expression == "0":
            self.current_expression = str(number)
        elif self.last_was_operator:
            self.current_expression += str(number)
        else:
            self.current_expression += str(number)
        
        self.last_was_operator = False

    def handle_decimal(self):
        if self.last_was_equals:
            self.current_expression = "0"
            self.last_was_equals = False

        parts = self.current_expression.split()
        if '.' not in parts[-1]:
            self.current_expression += '.'
        self.last_was_operator = False

    def handle_operator(self, operator):
        if self.last_was_equals:
            self.last_was_equals = False

        if self.last_was_operator:
            self.current_expression = self.current_expression[:-3] + f" {operator} "
        else:
            self.current_expression += f" {operator} "
        self.last_was_operator = True

    def handle_special_operation(self, button):
        try:
            current_value = float(self.current_expression.split()[-1] if ' ' in self.current_expression else self.current_expression)
            
            result = None
            if button == '%':
                result = current_value / 100
            elif button == '±':
                result = -current_value
            elif button == '¹/x':
                if current_value == 0:
                    self.current_expression = "Cannot divide by zero"
                    return
                result = 1 / current_value
            elif button == 'x²':
                result = current_value ** 2
            elif button == '√x':
                if current_value < 0:
                    self.current_expression = "Invalid input"
                    return
                result = math.sqrt(current_value)
            elif button == 'sin':
                result = math.sin(math.radians(current_value))
            elif button == 'cos':
                result = math.cos(math.radians(current_value))
            elif button == 'tan':
                result = math.tan(math.radians(current_value))
            elif button == 'log':
                if current_value <= 0:
                    self.current_expression = "Invalid input"
                    return
                result = math.log10(current_value)
            elif button == 'ln':
                if current_value <= 0:
                    self.current_expression = "Invalid input"
                    return
                result = math.log(current_value)
            elif button == 'e^x':
                result = math.exp(current_value)
            elif button == 'π':
                result = math.pi
                
            if result is not None:
                self.current_expression = self.format_number(str(result))
                self.last_was_equals = True
                
        except ValueError:
            self.current_expression = "Error"

    def calculate(self):
        try:
            # Replace operators
            expression = self.current_expression.replace('×', '*').replace('÷', '/')
            
            # Calculate result
            result = eval(expression)
            
            # Add to history
            self.calculation_history.append(f"{self.current_expression} = {self.format_number(str(result))}")
            if len(self.calculation_history) > 100:  # Keep only last 100 calculations
                self.calculation_history.pop(0)
            
            # Update display
            self.current_expression = self.format_number(str(result))
            self.last_was_equals = True
            
        except Exception as e:
            self.current_expression = "Error"

    def clear(self):
        self.current_expression = "0"
        self.last_was_operator = False
        self.last_was_equals = False

    def backspace(self):
        if self.current_expression in ["Error", "Cannot divide by zero", "Invalid input"]:
            self.clear()
            return

        if len(self.current_expression) > 0:
            if self.current_expression.endswith(' '):
                self.current_expression = self.current_expression[:-3]
                self.last_was_operator = False
            else:
                self.current_expression = self.current_expression[:-1]
            
            if not self.current_expression:
                self.current_expression = "0"

    def standard_buttons(self):
        return [
            ['%', 'CE', 'C', '⌫'],
            ['¹/x', 'x²', '√x', '÷'],
            ['7', '8', '9', '×'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['±', '0', '.', '=']
        ]

    def scientific_buttons(self):
        return [
            ['%', 'CE', 'C', '⌫'],
            ['sin', 'cos', 'tan', '÷'],
            ['log', 'ln', 'e^x', '×'],
            ['7', '8', '9', '-'],
            ['4', '5', '6', '+'],
            ['1', '2', '3', '='],
            ['±', '0', '.', 'π']
        ]

if __name__ == "__main__":
    app = Calculator()
    app.mainloop()
