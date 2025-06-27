import customtkinter as ctk
import math

def calculate_loan():
    """Calculates the loan amortization schedule and displays it."""
    try:
        principal = float(principal_entry.get())
        annual_rate = float(rate_entry.get())
        total_months = int(months_entry.get())

        # Basic input validation
        if principal <= 0 or total_months <= 0 or annual_rate < 0:
            results_textbox.delete("1.0", "end")
            results_textbox.insert("end", "Please enter positive values for principal and months, and a non-negative rate.")
            return

        # Convert annual rate percentage to monthly decimal rate
        monthly_rate = (annual_rate / 100) / 12

        # Calculate monthly payment
        # Handle 0% interest case separately to avoid division by zero or formula issues
        if monthly_rate > 0:
            # M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
        else:
            # Interest-free loan
            monthly_payment = principal / total_months
            # Set monthly_rate to 0 explicitly if rate was 0%
            monthly_rate = 0

        # Clear previous results
        results_textbox.delete("1.0", "end")

        # Display summary
        results_textbox.insert("end", f"Loan Summary:\n")
        results_textbox.insert("end", f" Principal Amount: ${principal:,.2f}\n")
        results_textbox.insert("end", f" Annual Interest Rate: {annual_rate}%\n")
        results_textbox.insert("end", f" Loan Term: {total_months} months\n")
        # Round monthly payment to two decimal places for display,
        # but use the full calculated value for internal calculations to maintain accuracy
        results_textbox.insert("end", f" Estimated Monthly Payment: ${monthly_payment:,.2f}\n\n")

        # --- Amortization Schedule ---
        # Display Header
        # Use a monospaced font and fixed widths for alignment
        # Adjust widths as needed based on expected maximum values
        header = "{:<8} {:<15} {:<15} {:<15} {:<20}\n".format(
            "Month", "Payment", "Principal", "Interest", "Remaining")
        results_textbox.insert("end", "Amortization Schedule:\n")
        results_textbox.insert("end", header)
        # Add a separator line matching header width
        separator = "-" * len(header.strip()) # .strip() removes trailing newline
        results_textbox.insert("end", separator + "\n")

        # Calculate and display schedule for each month
        remaining_balance = principal
        total_interest_paid = 0 # Initialize total interest accumulator
        total_amount_paid = 0   # Initialize total payment accumulator

        for month_num in range(1, total_months + 1):
            interest_this_month = remaining_balance * monthly_rate

            # For the last month, adjust payment and principal to clear the remaining balance exactly
            if month_num == total_months:
                # The final payment should be the remaining balance plus the interest for that month
                monthly_payment_actual = remaining_balance + interest_this_month
                principal_this_month = remaining_balance
                remaining_balance = 0 # Should be exactly 0 after this payment
            else:
                principal_this_month = monthly_payment - interest_this_month
                 # Prevent tiny negative principal due to floating point errors on small balances
                if principal_this_month < 0 and abs(principal_this_month) < 1e-9: # Use a small epsilon
                     principal_this_month = 0
                     interest_this_month = monthly_payment # If principal is effectively zero, payment is all interest
                elif principal_this_month < 0: # Larger negative principal indicates an issue (shouldn't happen with correct formula)
                     # This case is unlikely, but handle defensively
                     print(f"Warning: Unexpected negative principal calculated for month {month_num}: {principal_this_month:.2f}")
                     principal_this_month = 0
                     interest_this_month = monthly_payment

                remaining_balance -= principal_this_month
                # Ensure remaining balance doesn't go slightly negative due to rounding before the last payment
                # Use a small epsilon for comparison to zero
                if remaining_balance < 1e-9 and month_num != total_months:
                     remaining_balance = 0

                monthly_payment_actual = monthly_payment # Use the calculated monthly payment for most months

            # Accumulate totals
            total_interest_paid += interest_this_month
            total_amount_paid += monthly_payment_actual

            # Format the row data
            row_data = "{:<8} ${:<14.2f} ${:<14.2f} ${:<14.2f} ${:<19.2f}\n".format(
                month_num,
                monthly_payment_actual, # Use actual payment for display
                principal_this_month,
                interest_this_month,
                remaining_balance)

            results_textbox.insert("end", row_data)

        # --- Display Totals ---
        results_textbox.insert("end", separator + "\n") # Add separator before totals
        results_textbox.insert("end", f"\nTotal Interest Paid: ${total_interest_paid:,.2f}\n")
        results_textbox.insert("end", f"Total Amount Paid Back: ${total_amount_paid:,.2f}\n")
        # Optional: Verify total_amount_paid is principal + total_interest_paid (should be close, maybe exact with last month's adjustment)
        # print(f"Verification check: Principal + Total Interest = {principal + total_interest_paid:.2f}, Total Paid = {total_amount_paid:.2f}")


    except ValueError:
        results_textbox.delete("1.0", "end")
        results_textbox.insert("end", "Invalid input. Please enter valid numbers for principal, rate, and months.")
    except Exception as e:
        results_textbox.delete("1.0", "end")
        results_textbox.insert("end", f"An unexpected error occurred: {e}")


# --- GUI Setup ---
ctk.set_appearance_mode("dark") # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"

app = ctk.CTk()
app.title("Bank Loan Calculator")
app.geometry("850x650") # Set a larger default window size to accommodate wider output

# Configure grid layout for the main window
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1) # Give columns equal weight
app.grid_rowconfigure(4, weight=1) # Row 4 (results textbox) will expand

# Input Frame
input_frame = ctk.CTkFrame(app, corner_radius=10)
input_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")

# Use grid for elements within the input frame
input_frame.grid_columnconfigure(0, weight=1)
input_frame.grid_columnconfigure(1, weight=2) # Give entry column more space

# Principal Input
principal_label = ctk.CTkLabel(input_frame, text="Principal Loan Amount ($):")
principal_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
principal_entry = ctk.CTkEntry(input_frame, width=250) # Make entry wider
principal_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

# Annual Rate Input
rate_label = ctk.CTkLabel(input_frame, text="Annual Interest Rate (%):")
rate_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
rate_entry = ctk.CTkEntry(input_frame, width=250) # Make entry wider
rate_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

# Loan Term Input
months_label = ctk.CTkLabel(input_frame, text="Loan Term (Months):")
months_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
months_entry = ctk.CTkEntry(input_frame, width=250) # Make entry wider
months_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

# Calculate Button
calculate_button = ctk.CTkButton(app, text="Calculate Loan", command=calculate_loan)
calculate_button.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

# Results Textbox
# Use a monospaced font for column alignment and disable wrapping
results_textbox = ctk.CTkTextbox(app, wrap="none", font=("Courier New", 12)) # Or use another monospaced font like "Consolas"
results_textbox.grid(row=4, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="nsew")
results_textbox.insert("end", "Enter loan details above and click 'Calculate Loan'.")
results_textbox.configure(state="normal") # Keep state as normal initially to insert text

# Start the GUI event loop
app.mainloop()