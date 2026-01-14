import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Database setup
DB_FILE = "bmi_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bmi_records (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            weight REAL,
            height REAL,
            bmi REAL,
            category TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def add_user(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_bmi(user_name, weight, height, bmi, category):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE name = ?", (user_name,))
    user_id = cursor.fetchone()[0]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO bmi_records (user_id, weight, height, bmi, category, date) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, weight, height, bmi, category, date))
    conn.commit()
    conn.close()

def get_history(user_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT weight, height, bmi, category, date FROM bmi_records
        WHERE user_id = (SELECT id FROM users WHERE name = ?)
        ORDER BY date DESC
    """, (user_name,))
    history = cursor.fetchall()
    conn.close()
    return history

def calculate_bmi(weight, height):
    height_m = height / 100  # Convert cm to m
    bmi = weight / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 24.9:
        category = "Normal"
    elif 25 <= bmi < 29.9:
        category = "Overweight"
    else:
        category = "Obese"
    return round(bmi, 2), category

class BMICalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Calculator")
        self.root.geometry("600x700")

        init_db()

        # User selection
        ttk.Label(root, text="Select or Add User:").pack(pady=5)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(root, textvariable=self.user_var, values=get_users())
        self.user_combo.pack(pady=5)
        self.user_combo.bind("<<ComboboxSelected>>", self.load_user_history)

        self.new_user_entry = ttk.Entry(root)
        self.new_user_entry.pack(pady=5)
        ttk.Button(root, text="Add New User", command=self.add_new_user).pack(pady=5)

        # Input fields
        ttk.Label(root, text="Weight (kg):").pack(pady=5)
        self.weight_entry = ttk.Entry(root)
        self.weight_entry.pack(pady=5)

        ttk.Label(root, text="Height (cm):").pack(pady=5)
        self.height_entry = ttk.Entry(root)
        self.height_entry.pack(pady=5)

        ttk.Button(root, text="Calculate BMI", command=self.calculate_and_display).pack(pady=10)

        # Result display
        self.result_label = ttk.Label(root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        # Visualization (simple color-coded label)
        self.visual_label = ttk.Label(root, text="", font=("Arial", 12))
        self.visual_label.pack(pady=10)

        # History and Trends
        ttk.Button(root, text="View History", command=self.view_history).pack(pady=5)
        ttk.Button(root, text="View Trends", command=self.view_trends).pack(pady=5)

        # History listbox
        self.history_listbox = tk.Listbox(root, height=10)
        self.history_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

    def add_new_user(self):
        name = self.new_user_entry.get().strip()
        if name and add_user(name):
            self.user_combo['values'] = get_users()
            self.user_var.set(name)
            messagebox.showinfo("Success", f"User '{name}' added.")
        else:
            messagebox.showerror("Error", "User already exists or invalid name.")

    def calculate_and_display(self):
        try:
            user = self.user_var.get()
            if not user:
                messagebox.showerror("Error", "Please select a user.")
                return
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get())
            if weight <= 0 or height <= 0:
                raise ValueError
            bmi, category = calculate_bmi(weight, height)
            self.result_label.config(text=f"BMI: {bmi} ({category})")
            # Simple visualization
            if category == "Underweight":
                color = "blue"
            elif category == "Normal":
                color = "green"
            elif category == "Overweight":
                color = "orange"
            else:
                color = "red"
            self.visual_label.config(text=f"Category: {category}", foreground=color)
            save_bmi(user, weight, height, bmi, category)
            self.load_user_history()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid weight and height.")

    def load_user_history(self, event=None):
        user = self.user_var.get()
        if user:
            history = get_history(user)
            self.history_listbox.delete(0, tk.END)
            for record in history:
                self.history_listbox.insert(tk.END, f"{record[4]}: BMI {record[2]} ({record[3]}) - W:{record[0]}kg H:{record[1]}cm")

    def view_history(self):
        user = self.user_var.get()
        if not user:
            messagebox.showerror("Error", "Please select a user.")
            return
        history = get_history(user)
        if not history:
            messagebox.showinfo("History", "No history available.")
            return
        history_window = tk.Toplevel(self.root)
        history_window.title(f"History for {user}")
        listbox = tk.Listbox(history_window, height=20)
        listbox.pack(fill=tk.BOTH, expand=True)
        for record in history:
            listbox.insert(tk.END, f"{record[4]}: BMI {record[2]} ({record[3]}) - W:{record[0]}kg H:{record[1]}cm")

    def view_trends(self):
        user = self.user_var.get()
        if not user:
            messagebox.showerror("Error", "Please select a user.")
            return
        history = get_history(user)
        if len(history) < 2:
            messagebox.showinfo("Trends", "Not enough data for trends.")
            return
        dates = [datetime.strptime(record[4], "%Y-%m-%d %H:%M:%S") for record in history]
        bmis = [record[2] for record in history]
        plt.figure(figsize=(10, 5))
        plt.plot(dates, bmis, marker='o')
        plt.title(f"BMI Trend for {user}")
        plt.xlabel("Date")
        plt.ylabel("BMI")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = BMICalculator(root)
    root.mainloop()