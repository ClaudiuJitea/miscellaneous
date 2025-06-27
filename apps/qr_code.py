import customtkinter as ctk
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageTk
import io
import os
from pathlib import Path


class QRCodeGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Define custom colors for themes
        self.themes = {
            "dark-blue": {
                "primary": "#1a237e",
                "secondary": "#3949ab",
                "text": "#ffffff",
                "entry": "#283593",
            },
            "green": {
                "primary": "#1b5e20",
                "secondary": "#2e7d32",
                "text": "#ffffff",
                "entry": "#388e3c",
            },
            "blue": {
                "primary": "#0d47a1",
                "secondary": "#1565c0",
                "text": "#ffffff",
                "entry": "#1976d2",
            },
        }

        # Set default theme
        self.current_theme = "blue"

        # Configure window
        self.title("QR Code Generator")
        self.geometry("400x690")  # Increased height to accommodate larger QR frame

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Create widgets
        self.create_widgets()

        # Apply theme after creating widgets
        self.apply_theme()

    def create_widgets(self):
        # Create more menu
        self.create_more_menu()

        # URL input
        self.url_label = ctk.CTkLabel(self, text="Enter Website URL:")
        self.url_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        self.url_entry = ctk.CTkEntry(self, width=360)
        self.url_entry.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Generate button
        self.generate_button = ctk.CTkButton(
            self,
            text="Generate QR Code",
            command=self.generate_qr_code,
        )
        self.generate_button.grid(row=2, column=0, padx=20, pady=10)

        # QR code display
        self.qr_frame = ctk.CTkFrame(self, width=360, height=400)  # Increased height
        self.qr_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")
        self.qr_frame.grid_propagate(False)

        self.qr_label = ctk.CTkLabel(self.qr_frame, text="QR Code will appear here")
        self.qr_label.place(relx=0.5, rely=0.5, anchor="center")

        # Button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        # Save button
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="Save QR Code",
            command=self.save_qr_code,
        )
        self.save_button.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.save_button.configure(state="disabled")

        # Clear button
        self.clear_button = ctk.CTkButton(
            self.button_frame,
            text="Clear",
            command=self.clear_all,
        )
        self.clear_button.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")

        # Save message
        self.save_message = ctk.CTkLabel(self, text="")
        self.save_message.grid(row=5, column=0, padx=20, pady=10)

        # Store the generated QR code
        self.qr_image = None

    def create_more_menu(self):
        self.more_menu = ctk.CTkOptionMenu(
            self,
            values=["Themes", "About"],
            command=self.handle_more_menu,
        )
        self.more_menu.set("...more")
        self.more_menu.grid(row=0, column=0, padx=(0, 20), pady=(20, 0), sticky="e")

    def handle_more_menu(self, choice):
        if choice == "Themes":
            self.show_theme_dialog()
        elif choice == "About":
            self.show_about_dialog()
        self.more_menu.set("...more")

    def show_theme_dialog(self):
        theme_dialog = ctk.CTkToplevel(self)
        theme_dialog.title("Change Theme")
        theme_dialog.geometry("300x200")
        theme_dialog.grab_set()
        self.apply_theme_to_window(theme_dialog)

        theme_label = ctk.CTkLabel(theme_dialog, text="Select a theme:")
        theme_label.pack(pady=10)

        theme_var = ctk.StringVar(value=self.current_theme)
        for theme in self.themes.keys():
            ctk.CTkRadioButton(
                theme_dialog,
                text=theme.capitalize(),
                variable=theme_var,
                value=theme,
                fg_color=self.themes[self.current_theme]["secondary"],
                border_color=self.themes[self.current_theme]["text"],
                hover_color=self.themes[self.current_theme]["primary"],
                text_color=self.themes[self.current_theme]["text"],
            ).pack(pady=5)

        ok_button = ctk.CTkButton(
            theme_dialog,
            text="OK",
            command=lambda: self.change_theme(theme_var.get(), theme_dialog),
            fg_color=self.themes[self.current_theme]["secondary"],
            text_color=self.themes[self.current_theme]["text"],
            hover_color=self.themes[self.current_theme]["primary"],
        )
        ok_button.pack(pady=10)

    def change_theme(self, theme, dialog):
        self.current_theme = theme
        self.apply_theme()
        dialog.destroy()

    def show_about_dialog(self):
        about_dialog = ctk.CTkToplevel(self)
        about_dialog.title("About")
        about_dialog.geometry("300x150")
        about_dialog.grab_set()
        self.apply_theme_to_window(about_dialog)

        about_label = ctk.CTkLabel(about_dialog, text="Generated with ClaudeAI")
        about_label.pack(expand=True)

        ok_button = ctk.CTkButton(
            about_dialog,
            text="OK",
            command=about_dialog.destroy,
            fg_color=self.themes[self.current_theme]["secondary"],
            text_color=self.themes[self.current_theme]["text"],
            hover_color=self.themes[self.current_theme]["primary"],
        )
        ok_button.pack(pady=10)

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        self.configure(fg_color=theme["primary"])
        self.url_entry.configure(fg_color=theme["entry"], text_color=theme["text"])
        self.generate_button.configure(
            fg_color=theme["secondary"], text_color=theme["text"]
        )
        self.qr_frame.configure(fg_color=theme["secondary"])
        self.qr_label.configure(text_color=theme["text"])
        self.button_frame.configure(fg_color=theme["primary"])
        self.save_button.configure(
            fg_color=theme["secondary"], text_color=theme["text"]
        )
        self.clear_button.configure(
            fg_color=theme["secondary"], text_color=theme["text"]
        )
        self.more_menu.configure(
            fg_color=theme["secondary"],
            button_color=theme["secondary"],
            button_hover_color=theme["primary"],
            dropdown_fg_color=theme["secondary"],
            dropdown_hover_color=theme["primary"],
            text_color=theme["text"],
        )

        for widget in [self.url_label, self.save_message]:
            widget.configure(text_color=theme["text"])

    def apply_theme_to_window(self, window):
        theme = self.themes[self.current_theme]
        window.configure(fg_color=theme["primary"])
        for child in window.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text_color=theme["text"])
            elif isinstance(child, ctk.CTkButton):
                child.configure(
                    fg_color=theme["secondary"],
                    text_color=theme["text"],
                    hover_color=theme["primary"],
                )
            elif isinstance(child, ctk.CTkRadioButton):
                child.configure(
                    fg_color=theme["secondary"],
                    border_color=theme["text"],
                    hover_color=theme["primary"],
                    text_color=theme["text"],
                )

    def generate_qr_code(self):
        url = self.url_entry.get()
        if url:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            theme = self.themes[self.current_theme]
            qr_image = qr.make_image(
                fill_color=theme["text"], back_color=theme["secondary"]
            )

            # Create a new image with space for text and QR code
            self.qr_image = Image.new("RGB", (340, 380), color=theme["secondary"])
            draw = ImageDraw.Draw(self.qr_image)

            # Add text
            font = ImageFont.load_default()
            text_width = draw.textlength(url, font=font)
            text_position = ((340 - text_width) // 2, 10)  # Center text horizontally
            draw.text(text_position, url, fill=theme["text"], font=font)

            # Paste QR code
            qr_image = qr_image.resize((340, 340), Image.LANCZOS)
            self.qr_image.paste(qr_image, (0, 40))  # Position QR code below text

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(self.qr_image)
            self.qr_label.configure(image=photo, text="")
            self.qr_label.image = photo
            self.save_button.configure(state="normal")
            self.save_message.configure(text="")
        else:
            self.qr_label.configure(text="QR Code will appear here", image="")
            self.save_button.configure(state="disabled")
            self.save_message.configure(text="Please enter a valid URL")

    def save_qr_code(self):
        if self.qr_image:
            from tkinter import filedialog
            import time
            
            # Generate a default filename based on the URL
            url = self.url_entry.get()
            default_name = f"qr_{url.replace('https://', '').replace('http://', '').replace('/', '_')}_{int(time.time())}.png"
            
            # Open file dialog to choose save location
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=default_name,
                title="Save QR Code As"
            )
            
            if filepath:  # If user didn't cancel the dialog
                try:
                    self.qr_image.save(filepath)
                    self.save_message.configure(text=f"QR Code saved successfully!")
                except Exception as e:
                    self.save_message.configure(text=f"Error saving file: {str(e)}")

    def clear_all(self):
        self.url_entry.delete(0, "end")
        self.qr_label.configure(text="QR Code will appear here", image="")
        self.save_button.configure(state="disabled")
        self.save_message.configure(text="")
        self.qr_image = None


if __name__ == "__main__":
    app = QRCodeGenerator()
    app.mainloop()
