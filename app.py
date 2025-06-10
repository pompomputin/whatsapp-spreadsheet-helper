import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Scrollbar, Toplevel, Label, Entry, Button
import gspread
import pyperclip
import sys
import requests
from datetime import datetime
import time

# --- CONFIGURATION ---
# IMPORTANT: Change these values to match your Google Sheet details.

# This should be the name of the sheet you are using.
GOOGLE_SHEET_NAME = "pepek"
WORKSHEET_NAME = "Sheet1"

# API Gateway Configuration
API_BASE_URL = "https://pompomputin.me" 
DEFAULT_COUNTRY_CODE = "62" 

# Default login credentials
DEFAULT_API_USERNAME = "admin"
DEFAULT_API_PASSWORD = "admin123"
DEFAULT_API_SESSION = "asd"

# These column names match the template sheet. Do not change them.
PHONE_COLUMN = "PHONE NUMBER"
NAME_COLUMN = "NAMA"
ID_COLUMN = "USERNAME"
LAST_LOGIN_COLUMN = "LAST LOGIN"
STATUS_COLUMN = "TERKIRIM"

# The text to write in the status column when you click the buttons.
STATUS_DONE_TEXT = "SENT"
STATUS_INVALID_TEXT = "INVALID"

# --- END OF CONFIGURATION ---


class WhatsAppHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Helper")
        self.root.geometry("600x550")

        self.api_token = None
        self.api_session_name = None
        self.success_log = []
        self.failed_log = []
        self.log_windows = {} 
        self.worksheet = None
        self.current_customer_data = {}

        self.setup_gui()
        
        try:
            self.authenticate_and_load_sheet()
            self.load_first_customer() 
        except gspread.exceptions.SpreadsheetNotFound:
            messagebox.showerror("Error", f"Spreadsheet not found.\nPlease check that the GOOGLE_SHEET_NAME in your script matches the name in your Google Drive exactly.")
            sys.exit()
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to Google Sheets.\nError: {e}\nPlease check your credentials and sharing settings.")
            sys.exit()

    def setup_gui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        api_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="API", menu=api_menu)
        api_menu.add_command(label="Login to Gateway...", command=self.open_login_window)
        
        log_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Logs", menu=log_menu)
        log_menu.add_command(label="View Success Log", command=lambda: self.show_log_window("Success"))
        log_menu.add_command(label="View Failed Log", command=lambda: self.show_log_window("Failed"))

        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_info_frame = tk.Frame(main_frame)
        top_info_frame.pack(fill=tk.X, pady=(0, 10))
        self.customer_info_label = tk.Label(top_info_frame, text="Please log in via the API menu to begin.", font=("Helvetica", 12, "bold"))
        self.customer_info_label.pack()

        phone_frame = tk.Frame(main_frame)
        phone_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(phone_frame, text="Phone:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.phone_text = tk.Text(phone_frame, height=1, width=25, state=tk.DISABLED, bg="#f0f0f0")
        self.phone_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.phone_status_label = tk.Label(phone_frame, text="", font=("Helvetica", 10, "bold"), width=15)
        self.phone_status_label.pack(side=tk.LEFT, padx=(5,10))

        phone_button_frame = tk.Frame(phone_frame)
        phone_button_frame.pack(side=tk.LEFT)
        tk.Button(phone_button_frame, text="Copy Phone", command=self.copy_phone_number).pack(fill=tk.X)
        
        tk.Label(main_frame, text="Message 1: Greeting", font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.msg1_text = tk.Text(main_frame, height=2, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.msg1_text.pack(fill=tk.X, expand=True, pady=(0, 5))
        tk.Button(main_frame, text="Copy Message 1", command=self.copy_message_1).pack(fill=tk.X, pady=(0, 10))

        tk.Label(main_frame, text="Message 2: Follow Up", font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.msg2_text = tk.Text(main_frame, height=5, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.msg2_text.pack(fill=tk.X, expand=True, pady=(0, 5))
        tk.Button(main_frame, text="Copy Message 2", command=self.copy_message_2).pack(fill=tk.X, pady=(0, 10))

        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        self.next_button = tk.Button(action_frame, text="Mark as Done & Get Next Customer", command=self.mark_done_and_next, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.next_button.pack(fill=tk.X, pady=(5,0))
        self.invalid_button = tk.Button(action_frame, text="Mark as Invalid & Get Next", command=self.mark_invalid_and_next, bg="#f44336", fg="white", font=("Helvetica", 10, "bold"))
        self.invalid_button.pack(fill=tk.X, pady=(5,0))
        
        self.next_button.config(state=tk.DISABLED)
        self.invalid_button.config(state=tk.DISABLED)
    
    def authenticate_and_load_sheet(self):
        gc = gspread.service_account(filename="credentials.json")
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        self.worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print("Successfully connected to Google Sheets.")
    
    def get_time_based_greeting(self):
        current_hour = datetime.now().hour
        if 4 <= current_hour < 10: return "pagi"
        elif 10 <= current_hour < 15: return "siang"
        elif 15 <= current_hour < 18: return "sore"
        else: return "malam"

    def _is_phone_number_valid(self, phone_number):
        if not self.api_token:
            self.handle_auth_failure() # NEW: Trigger re-login if token is missing
            return None # Return a special value to indicate a halt

        phone_number = str(phone_number).strip()
        if not phone_number:
            return False

        self.phone_status_label.config(text="Checking...", fg="orange")
        self.root.update_idletasks()
        time.sleep(0.5)

        try:
            check_url = f"{API_BASE_URL}/session/is-registered/{self.api_session_name}/{phone_number}"
            params = {"countryCode": DEFAULT_COUNTRY_CODE}
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = requests.get(check_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("isRegistered", False)
        except requests.exceptions.RequestException as e:
            # --- NEW: Check for authentication errors ---
            if e.response is not None and e.response.status_code in [401, 403]:
                self.handle_auth_failure()
                return None # Halt the process
            return False

    def load_and_validate_next_customer(self):
        if not self.api_token:
            messagebox.showwarning("Not Logged In", "Please login via the API menu to start processing.")
            return

        self.customer_info_label.config(text="Searching for next valid customer...")
        self.next_button.config(state=tk.DISABLED)
        self.invalid_button.config(state=tk.DISABLED)
        self.root.update_idletasks()

        all_records = self.worksheet.get_all_records()
        
        while True:
            found_customer = None
            current_index = self.current_customer_data.get('row_index', 1) - 1 # Start search from last known position
            for i in range(current_index, len(all_records)):
                record = all_records[i]
                status = str(record.get(STATUS_COLUMN, '')).strip()
                if status not in [STATUS_DONE_TEXT, STATUS_INVALID_TEXT]:
                    found_customer = record
                    found_customer['row_index'] = i + 2 
                    break
            
            if not found_customer:
                self._display_no_more_customers()
                return

            self.current_customer_data = found_customer
            phone_to_check = self.current_customer_data.get(PHONE_COLUMN, "")
            
            is_valid = self._is_phone_number_valid(phone_to_check)
            
            if is_valid is None: # Special value indicating auth failure
                return # Stop the process, user needs to re-login

            if is_valid:
                self.phone_status_label.config(text="Registered", fg="green")
                self._display_customer_data()
                return
            else:
                print(f"Number {phone_to_check} is invalid, auto-skipping.")
                self.phone_status_label.config(text="Invalid, skipping...", fg="red")
                self._update_status(STATUS_INVALID_TEXT)
                all_records = self.worksheet.get_all_records() # Refresh records
    
    def load_first_customer(self):
        # This function simplified, as validation now happens after login.
        self.customer_info_label.config(text="Please log in via the API menu to begin.")

    def _display_customer_data(self):
        name = self.current_customer_data.get(NAME_COLUMN, "")
        phone = self.current_customer_data.get(PHONE_COLUMN, "")
        user_id = self.current_customer_data.get(ID_COLUMN, "")
        last_login = self.current_customer_data.get(LAST_LOGIN_COLUMN, "")
        self.customer_info_label.config(text=f"Contact Name: {name}")
        self.update_text_widget(self.phone_text, phone)
        greeting_word = self.get_time_based_greeting()
        msg1 = f"Selamat {greeting_word} ka {name}"
        msg2 = (f"ingin konfirmasi mengenai ID kaka *{user_id}* \n"
                f"sejak *{last_login}*\n"
                f"Di situs Amor77\n"
                f"belum dimainkan ya ka ? apakah ada kendala ?")
        self.update_text_widget(self.msg1_text, msg1)
        self.update_text_widget(self.msg2_text, msg2)
        if self.api_token:
            self.next_button.config(state=tk.NORMAL)
            self.invalid_button.config(state=tk.NORMAL)

    def _display_no_more_customers(self):
        self.phone_status_label.config(text="")
        self.update_text_widget(self.phone_text, "")
        self.update_text_widget(self.msg1_text, "")
        self.update_text_widget(self.msg2_text, "")
        self.customer_info_label.config(text="All Done!")
        messagebox.showinfo("Complete", "You have processed all customers in the sheet!")
        self.next_button.config(state=tk.DISABLED)
        self.invalid_button.config(state=tk.DISABLED)

    def _update_status(self, status_text):
        if not self.current_customer_data: return
        try:
            row_to_update = self.current_customer_data['row_index']
            col_to_update = self.worksheet.find(STATUS_COLUMN).col
            self.worksheet.update_cell(row_to_update, col_to_update, status_text)
            print(f"Updated row {row_to_update} status to '{status_text}'.")
            
            name = self.current_customer_data.get(NAME_COLUMN, 'N/A')
            phone = self.current_customer_data.get(PHONE_COLUMN, 'N/A')
            username = self.current_customer_data.get(ID_COLUMN, 'N/A')
            log_entry = f"{name} ({phone}) - {username}"

            if status_text == STATUS_DONE_TEXT: self.success_log.append(log_entry)
            elif status_text == STATUS_INVALID_TEXT: self.failed_log.append(log_entry)
            self.update_log_window("Success" if status_text == STATUS_DONE_TEXT else "Failed")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update Google Sheet.\nError: {e}")
            
    def mark_done_and_next(self):
        self._update_status(STATUS_DONE_TEXT)
        self.load_and_validate_next_customer()

    def mark_invalid_and_next(self):
        self._update_status(STATUS_INVALID_TEXT)
        self.load_and_validate_next_customer()

    def open_login_window(self):
        login_window = Toplevel(self.root)
        login_window.title("API Gateway Login")
        login_window.geometry("300x200")
        login_window.transient(self.root)
        login_window.grab_set()
        
        Label(login_window, text="Username:").pack(pady=(10,0))
        user_entry = Entry(login_window, width=30)
        user_entry.pack(); user_entry.insert(0, DEFAULT_API_USERNAME)
        
        Label(login_window, text="Password:").pack(pady=(5,0))
        pass_entry = Entry(login_window, show="*", width=30)
        pass_entry.pack(); pass_entry.insert(0, DEFAULT_API_PASSWORD)

        Label(login_window, text="Session Name (e.g., asd):").pack(pady=(5,0))
        session_entry = Entry(login_window, width=30)
        session_entry.pack(); session_entry.insert(0, self.api_session_name or DEFAULT_API_SESSION)
        
        def perform_login():
            username = user_entry.get(); password = pass_entry.get(); session = session_entry.get()
            if not all([username, password, session]):
                messagebox.showerror("Error", "All fields are required.", parent=login_window)
                return

            try:
                login_url = f"{API_BASE_URL}/auth/login"
                payload = {"username": username, "password": password}
                response = requests.post(login_url, json=payload, timeout=10)
                response.raise_for_status() 
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.api_token = data["token"]; self.api_session_name = session
                    self.next_button.config(state=tk.NORMAL); self.invalid_button.config(state=tk.NORMAL)
                    messagebox.showinfo("Success", "Successfully logged in. You may now begin.", parent=login_window)
                    login_window.destroy()
                    self.load_and_validate_next_customer()
                else:
                    messagebox.showerror("Login Failed", data.get("message", "Unknown error."), parent=login_window)
            except requests.exceptions.RequestException as e:
                messagebox.showerror("API Error", f"Failed to connect to API Gateway.\n{e}", parent=login_window)

        Button(login_window, text="Login", command=perform_login).pack(pady=15)

    # --- NEW: Function to handle when the API token is invalid ---
    def handle_auth_failure(self):
        """Clears token, disables buttons, and forces a re-login."""
        self.api_token = None
        self.next_button.config(state=tk.DISABLED)
        self.invalid_button.config(state=tk.DISABLED)
        messagebox.showerror("Session Error", "API Login Failed or Session Expired. Please log in again.")
        self.open_login_window()

    def copy_phone_number(self): pyperclip.copy(self.phone_text.get("1.0", tk.END).strip())
    def copy_message_1(self): pyperclip.copy(self.msg1_text.get("1.0", tk.END).strip())
    def copy_message_2(self): pyperclip.copy(self.msg2_text.get("1.0", tk.END).strip())
    def show_log_window(self, log_type):
        if self.log_windows.get(log_type) and self.log_windows[log_type].winfo_exists(): self.log_windows[log_type].lift(); return
        log_window = Toplevel(self.root)
        log_window.title(f"{log_type} Log")
        log_window.geometry("500x500")
        button_frame = tk.Frame(log_window); button_frame.pack(pady=5, fill=tk.X, padx=5)
        tk.Button(button_frame, text="Copy Selected Username", command=lambda: self.copy_selected_log_username(listbox)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        tk.Button(button_frame, text="Copy ALL Usernames", command=lambda: self.copy_all_log_usernames(listbox)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))
        listbox_frame = tk.Frame(log_window); listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        listbox = Listbox(listbox_frame, font=("Courier", 10)); listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = Scrollbar(listbox_frame, orient="vertical"); scrollbar.config(command=listbox.yview); scrollbar.pack(side=tk.RIGHT, fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        self.log_windows[log_type] = log_window
        self.update_log_window(log_type)
    def copy_selected_log_username(self, listbox):
        indices = listbox.curselection()
        if not indices: messagebox.showwarning("No Selection", "Please click on an item in the log to select it first."); return
        entry = listbox.get(indices[0])
        try: username = entry.split(' - ')[-1].strip(); pyperclip.copy(username); print(f"Copied: {username}")
        except IndexError: print(f"Could not parse: {entry}")
    def copy_all_log_usernames(self, listbox):
        entries = listbox.get(0, tk.END)
        if not entries: messagebox.showwarning("Empty Log", "The log is empty."); return
        usernames = [e.split(' - ')[-1].strip() for e in entries if ' - ' in e]
        if usernames: pyperclip.copy("\n".join(usernames)); messagebox.showinfo("Copied!", f"{len(usernames)} usernames copied.")
        else: messagebox.showwarning("No Usernames", "Could not find any usernames to copy.")
    def update_log_window(self, log_type):
        if not self.log_windows.get(log_type) or not self.log_windows[log_type].winfo_exists(): return
        window = self.log_windows[log_type]
        listbox = window.winfo_children()[1].winfo_children()[0]
        log_data = self.success_log if log_type == "Success" else self.failed_log
        listbox.delete(0, tk.END)
        for item in log_data: listbox.insert(tk.END, item)
    def update_text_widget(self, widget, text):
        widget.config(state=tk.NORMAL); widget.delete("1.0", tk.END); widget.insert("1.0", str(text)); widget.config(state=tk.DISABLED)

if __name__ == "__main__":
    try: import requests
    except ImportError: print("Requests library not found.\nPlease run: pip install requests"); sys.exit()
    root = tk.Tk()
    app = WhatsAppHelperApp(root)
    root.mainloop()