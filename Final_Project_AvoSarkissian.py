import tkinter as tk
from tkinter import messagebox, simpledialog
import matplotlib.pyplot as plt
import matplotlib
import json
import os

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')

class AccountManager:
    def __init__(self):
        self.accounts_file = 'user_accounts.json'
        self.accounts = self.load_accounts()

    def load_accounts(self):
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_accounts(self):
        with open(self.accounts_file, 'w') as f:
            json.dump(self.accounts, f)

    def create_account(self, username, password):
        if username in self.accounts:
            return False
        self.accounts[username] = {'password': password, 'financial_data': {}}
        self.save_accounts()
        return True

    def validate_login(self, username, password):
        return username in self.accounts and self.accounts[username]['password'] == password

    def save_financial_data(self, username, data):
        if username in self.accounts:
            self.accounts[username]['financial_data'] = data
            self.save_accounts()

    def load_financial_data(self, username):
        if username in self.accounts:
            return self.accounts[username]['financial_data']
        return {}

class FinancialCalculator:
    @staticmethod
    def future_value(rate, cash_flows):
        """Calculates the future value of a series of cash flows at a given rate."""
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows, 1))

    @staticmethod
    def compare_investment_vs_debt_payoff(remaining_loan_amount, monthly_income, monthly_expenses, monthly_loan_payment, loan_interest_rate, years=1):
        """Compares paying off debt early vs investing with monthly contributions."""
        investment_rate = 0.1022  # Fixed annual investment growth rate
        monthly_investment_rate = (1 + investment_rate) ** (1/12) - 1
        monthly_debt_rate = (1 + loan_interest_rate) ** (1/12) - 1

        excess_income = monthly_income - monthly_expenses - monthly_loan_payment
        if excess_income <= 0:
            messagebox.showwarning("Warning", "Your expenses and loan payment exceed your income. No excess income for comparison.")
            return [], []

        investment_growth = []
        debt_repayment = []
        current_investment_value = 0
        current_debt = remaining_loan_amount

        for month in range(1, int(years * 12) + 1):
            current_debt -= excess_income
            interest = current_debt * monthly_debt_rate
            current_debt = max(0, current_debt + interest)
            debt_repayment.append(current_debt)

            current_investment_value += excess_income
            current_investment_value *= (1 + monthly_investment_rate)
            investment_growth.append(current_investment_value)

            if current_debt <= 0:
                break  # Debt paid off, can stop the simulation

        return investment_growth, debt_repayment

class FinancialVisualizerGUI:
    def __init__(self, root, account_manager):
        self.root = root
        self.account_manager = account_manager
        self.current_user = None
        self.financial_data = {}
        self.start_login_ui()

    def start_login_ui(self):
        self.clear_ui()
        login_frame = tk.Frame(self.root)
        login_frame.pack()

        tk.Label(login_frame, text="Username:").pack()
        username_entry = tk.Entry(login_frame)
        username_entry.pack()

        tk.Label(login_frame, text="Password:").pack()
        password_entry = tk.Entry(login_frame, show="*")
        password_entry.pack()

        tk.Button(login_frame, text="Login", command=lambda: self.login(username_entry.get(), password_entry.get())).pack()
        tk.Button(login_frame, text="Register", command=lambda: self.register(username_entry.get(), password_entry.get())).pack()

    def login(self, username, password):
        if self.account_manager.validate_login(username, password):
            self.current_user = username
            self.financial_data = self.account_manager.load_financial_data(username)
            self.main_ui()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")

    def register(self, username, password):
        if self.account_manager.create_account(username, password):
            messagebox.showinfo("Success", "Account created successfully. Please login.")
            self.start_login_ui()
        else:
            messagebox.showerror("Failed", "Account creation failed. Username might already exist.")

    def main_ui(self):
        self.clear_ui()
        tk.Button(self.root, text="Enter Financial Data", command=self.enter_financial_data).pack()
        tk.Button(self.root, text="Compare Debt vs. Investment", command=self.compare_debt_vs_investment).pack()
        tk.Button(self.root, text="Save Profile", command=self.save_profile).pack()
        tk.Button(self.root, text="Load Profile", command=self.load_profile).pack()

    def clear_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def enter_financial_data(self):
        """Prompts user to enter financial data."""
        self.financial_data = {
            'monthly_income': simpledialog.askfloat("Monthly Income", "Enter your monthly income after tax:"),
            'monthly_expenses': simpledialog.askfloat("Monthly Expenses", "Enter your monthly expenses (excluding loan payment):"),
            'monthly_loan_payment': simpledialog.askfloat("Monthly Loan Payment", "Enter your monthly loan payment:"),
            'remaining_loan_amount': simpledialog.askfloat("Remaining Loan Amount", "Enter your remaining loan amount:"),
            'loan_interest_rate': simpledialog.askfloat("Loan Interest Rate", "Enter your loan's annual interest rate (as a decimal):"),
            'remaining_loan_period': simpledialog.askfloat("Remaining Loan Period", "Enter the remaining period of the loan in years (can be a decimal):")
        }
        messagebox.showinfo("Data Entered", "Financial data entered successfully.")

    def compare_debt_vs_investment(self):
        """Performs comparison and shows results."""
        if not all(key in self.financial_data for key in ['monthly_income', 'monthly_expenses', 'monthly_loan_payment', 'remaining_loan_amount', 'loan_interest_rate', 'remaining_loan_period']):
            messagebox.showerror("Error", "Please enter all financial data first.")
            return

        investment_growth, debt_repayment = FinancialCalculator.compare_investment_vs_debt_payoff(
            self.financial_data['remaining_loan_amount'], self.financial_data['monthly_income'], self.financial_data['monthly_expenses'], 
            self.financial_data['monthly_loan_payment'], self.financial_data['loan_interest_rate'], 
            self.financial_data['remaining_loan_period'])

        if investment_growth[-1] > self.financial_data['remaining_loan_amount']:
            advice = "Investing your excess income is more beneficial."
        else:
            advice = "Paying off your loan early is more beneficial."

        months = list(range(1, len(investment_growth) + 1))
        plt.figure(figsize=(10, 6))
        plt.plot(months, debt_repayment, label='Debt Repayment Over Time', color='red')
        plt.plot(months, investment_growth, label='Investment Growth Over Time', color='green')
        plt.title('Debt Repayment vs. Investment Growth Over Time')
        plt.xlabel('Months')
        plt.ylabel('Value')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
        summary_text = f"""
  - Monthly Income: ${self.financial_data['monthly_income']}
        - Monthly Expenses: ${self.financial_data['monthly_expenses']}
        - Monthly Loan Payment: ${self.financial_data['monthly_loan_payment']}
        - Remaining Loan Amount: ${self.financial_data['remaining_loan_amount']}
        - Loan Interest Rate: {self.financial_data['loan_interest_rate']*100}%
        - Advice: {advice}"""

        # Adjust subplot parameters as needed
        plt.subplots_adjust(bottom=0.3)
        
        # Adding the bold title separately above the summary text
        plt.figtext(0.5, 0.14, "Summary Report:", weight='bold', horizontalalignment='center', fontsize=12)
        
        # Adding the rest of the summary text
        plt.figtext(0.5, 0.05, summary_text.strip(), wrap=True, horizontalalignment='center', fontsize=10)
        
        # Show the plot
        plt.show()


    def save_profile(self):
        """Saves the financial data to a file specific to the logged-in user."""
        if self.current_user:
            profile_path = f"{self.current_user}_profile.json"
            with open(profile_path, 'w') as file:
                json.dump(self.financial_data, file)
            messagebox.showinfo("Success", "Financial profile saved successfully.")
        else:
            messagebox.showerror("Error", "No user is currently logged in.")

    def load_profile(self):
        """Loads the financial data from a file specific to the logged-in user."""
        if self.current_user:
            profile_path = f"{self.current_user}_profile.json"
            try:
                with open(profile_path, 'r') as file:
                    self.financial_data = json.load(file)
                messagebox.showinfo("Success", "Financial profile loaded successfully.")
                self.compare_debt_vs_investment()
            except FileNotFoundError:
                messagebox.showerror("Error", "No profile found for the current user.")
        else:
            messagebox.showerror("Error", "No user is currently logged in.")

def run_application():
    root = tk.Tk()
    root.title("Financial Visualizer with User Accounts")
    account_manager = AccountManager()
    FinancialVisualizerGUI(root, account_manager)
    root.mainloop()

if __name__ == "__main__":
    run_application()
