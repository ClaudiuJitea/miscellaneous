import customtkinter as ctk
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class MeasurementConverter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Measurement Calculator")
        self.geometry("400x320")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = ctk.CTkLabel(
            self, text="Measurement Calculator", font=("Arial", 20, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 5))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            self,
            text="Convert between different units of weight, length, and volume.",
            font=("Arial", 12),
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Measurement type selection
        self.measurement_type = ctk.CTkSegmentedButton(
            self, values=["Weight", "Length", "Volume"]
        )
        self.measurement_type.grid(
            row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew"
        )
        self.measurement_type.set("Weight")
        self.measurement_type.configure(command=self.update_units)

        # From section
        from_label = ctk.CTkLabel(self, text="From")
        from_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.from_entry = ctk.CTkEntry(self, placeholder_text="Enter value")
        self.from_entry.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.from_entry.bind("<KeyRelease>", self.update_conversion)

        unit_label = ctk.CTkLabel(self, text="Unit")
        unit_label.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.from_unit = ctk.CTkOptionMenu(
            self, values=["kg", "g", "lb", "oz"], command=self.update_conversion
        )
        self.from_unit.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # To section
        to_label = ctk.CTkLabel(self, text="To")
        to_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")

        self.to_entry = ctk.CTkEntry(self, state="readonly")
        self.to_entry.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        self.to_unit = ctk.CTkOptionMenu(
            self, values=["kg", "g", "lb", "oz"], command=self.update_conversion
        )
        self.to_unit.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        self.update_units()

    def update_units(self, *args):
        measurement = self.measurement_type.get()
        if measurement == "Weight":
            units = ["kg", "g", "lb", "oz"]
        elif measurement == "Length":
            units = ["m", "cm", "km", "in", "ft", "yd", "mi"]
        else:  # Volume
            units = ["L", "mL", "m³", "gal", "qt", "pt", "fl oz"]

        self.from_unit.configure(values=units)
        self.from_unit.set(units[0])
        self.to_unit.configure(values=units)
        self.to_unit.set(units[1])

        self.update_conversion()

    def update_conversion(self, *args):
        try:
            value = float(self.from_entry.get())
            from_unit = self.from_unit.get()
            to_unit = self.to_unit.get()

            if self.measurement_type.get() == "Weight":
                result = self.convert_weight(value, from_unit, to_unit)
            elif self.measurement_type.get() == "Length":
                result = self.convert_length(value, from_unit, to_unit)
            else:  # Volume
                result = self.convert_volume(value, from_unit, to_unit)

            self.to_entry.configure(state="normal")
            self.to_entry.delete(0, tk.END)
            self.to_entry.insert(0, f"{result:.4f}")
            self.to_entry.configure(state="readonly")
        except ValueError:
            self.to_entry.configure(state="normal")
            self.to_entry.delete(0, tk.END)
            self.to_entry.insert(0, "")
            self.to_entry.configure(state="readonly")

    def convert_weight(self, value, from_unit, to_unit):
        units = {"kg": 1, "g": 1000, "lb": 2.20462, "oz": 35.274}
        return value * units[to_unit] / units[from_unit]

    def convert_length(self, value, from_unit, to_unit):
        units = {
            "m": 1,
            "cm": 100,
            "km": 0.001,
            "in": 39.3701,
            "ft": 3.28084,
            "yd": 1.09361,
            "mi": 0.000621371,
        }
        return value * units[to_unit] / units[from_unit]

    def convert_volume(self, value, from_unit, to_unit):
        units = {
            "L": 1,
            "mL": 1000,
            "m³": 0.001,
            "gal": 0.264172,
            "qt": 1.05669,
            "pt": 2.11338,
            "fl oz": 33.814,
        }
        return value * units[to_unit] / units[from_unit]


if __name__ == "__main__":
    app = MeasurementConverter()
    app.mainloop()
