import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Toplevel, Label, Entry, Button
import gspread
import pyperclip
import sys
from datetime import datetime
import time

# --- Import our new files ---
from config import *
from api_client import ApiClient

class WhatsAppHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Helper")
        self.root.geometry("600x550")

        # Create an instance of our ApiClient
        self.api_client = ApiClient(API_BASE_URL)
        self.api_session_name = None

        self.success_log, self.failed_log = [], []
        self.log_windows = {} 
        self.worksheet = None
        self.current_customer_data = {}

        self.setup_gui()
        
        try:
            self.authenticate_and_load_sheet()
            # --- THIS LINE IS NOW CORRECTLY ADDED BACK ---
            self.load_first_customer() 
        except Exception as e:
            messagebox.showerror("Error", f"Could not initialize app.\nError: {e}")
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
        tk.Button(phone_frame, text="Copy Phone", command=self.copy_phone_number).pack(side=tk.LEFT)
        
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
        self.next_button = tk.Button(action_frame, text="Mark as Done & Get Next Customer", command=self.mark_done_and_next, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"), state=tk.DISABLED)
        self.next_button.pack(fill=tk.X, pady=(5,0))
        self.invalid_button = tk.Button(action_frame, text="Mark as Invalid & Get Next", command=self.mark_invalid_and_next, bg="#f44336", fg="white", font=("Helvetica", 10, "bold"), state=tk.DISABLED)
        self.invalid_button.pack(fill=tk.X, pady=(5,0))
    
    def authenticate_and_load_sheet(self):
        self.worksheet = gspread.service_account(filename="credentials.json").open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)
        print("Successfully connected to Google Sheets.")
    
    def get_time_based_greeting(self):
        h = datetime.now().hour
        if 4 <= h < 10: return "pagi"
        elif 10 <= h < 15: return "siang"
        elif 15 <= h < 18: return "sore"
        else: return "malam"

    def load_and_validate_next_customer(self):
        if not self.api_client.token:
            messagebox.showwarning("Not Logged In", "Please login via the API menu to start processing.")
            return

        self.customer_info_label.config(text="Searching for next valid customer...")
        self.next_button.config(state=tk.DISABLED)
        self.invalid_button.config(state=tk.DISABLED)
        self.root.update_idletasks()

        all_records = self.worksheet.get_all_records()
        start_index = self.current_customer_data.get('row_index', 1) -1 

        while True:
            found_customer = None
            for i in range(start_index, len(all_records)):
                record = all_records[i]
                status = str(record.get(STATUS_COLUMN, '')).strip()
                if status not in [STATUS_DONE_TEXT, STATUS_INVALID_TEXT]:
                    found_customer = record
                    found_customer['row_index'] = i + 2 
                    start_index = i + 1 
                    break
            
            if not found_customer:
                self._display_no_more_customers(); return

            self.current_customer_data = found_customer
            phone_to_check = self.current_customer_data.get(PHONE_COLUMN, "")
            is_valid, err_msg, is_auth_err = self.api_client.is_phone_registered(self.api_session_name, phone_to_check, DEFAULT_COUNTRY_CODE)
            
            if is_auth_err:
                self.handle_auth_failure(err_msg); return
            
            if is_valid:
                self.phone_status_label.config(text="Registered", fg="green")
                self._display_customer_data(); return
            else:
                print(f"Number {phone_to_check} is invalid, auto-skipping.")
                self.phone_status_label.config(text="Invalid, skipping...", fg="red")
                self._update_status(STATUS_INVALID_TEXT)
    
    def load_first_customer(self):
        all_records = self.worksheet.get_all_records()
        for i, record in enumerate(all_records):
            status = str(record.get(STATUS_COLUMN, '')).strip()
            if status not in [STATUS_DONE_TEXT, STATUS_INVALID_TEXT]:
                self.current_customer_data = record
                self.current_customer_data['row_index'] = i + 2
                self._display_customer_data(enable_buttons=False)
                break
    
    def _display_customer_data(self, enable_buttons=True):
        name = self.current_customer_data.get(NAME_COLUMN, ""); phone = self.current_customer_data.get(PHONE_COLUMN, "")
        user_id = self.current_customer_data.get(ID_COLUMN, ""); last_login = self.current_customer_data.get(LAST_LOGIN_COLUMN, "")
        self.customer_info_label.config(text=f"Contact Name: {name}")
        self.update_text_widget(self.phone_text, phone)
        greeting_word = self.get_time_based_greeting()
        msg1 = f"Selamat {greeting_word} ka {name}"; msg2 = (f"ingin konfirmasi mengenai ID kaka *{user_id}* \n"
                 f"sejak *{last_login}*\nDi situs Amor77\n"
                 f"belum dimainkan ya ka ? apakah ada kendala ?")
        self.update_text_widget(self.msg1_text, msg1); self.update_text_widget(self.msg2_text, msg2)
        if enable_buttons and self.api_client.token:
            self.next_button.config(state=tk.NORMAL); self.invalid_button.config(state=tk.NORMAL)

    def _display_no_more_customers(self):
        self.phone_status_label.config(text=""); self.update_text_widget(self.phone_text, "")
        self.update_text_widget(self.msg1_text, ""); self.update_text_widget(self.msg2_text, "")
        self.customer_info_label.config(text="All Done!")
        messagebox.showinfo("Complete", "You have processed all customers in the sheet!")
        self.next_button.config(state=tk.DISABLED); self.invalid_button.config(state=tk.DISABLED)

    def _update_status(self, status_text):
        if not self.current_customer_data: return
        try:
            row, col = self.current_customer_data['row_index'], self.worksheet.find(STATUS_COLUMN).col
            self.worksheet.update_cell(row, col, status_text)
            print(f"Updated row {row} status to '{status_text}'.")
            name = self.current_customer_data.get(NAME_COLUMN, 'N/A'); phone = self.current_customer_data.get(PHONE_COLUMN, 'N/A')
            username = self.current_customer_data.get(ID_COLUMN, 'N/A')
            log_entry = f"{name} ({phone}) - {username}"
            if status_text == STATUS_DONE_TEXT: self.success_log.append(log_entry)
            elif status_text == STATUS_INVALID_TEXT: self.failed_log.append(log_entry)
            self.update_log_window("Success" if status_text == STATUS_DONE_TEXT else "Failed")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update Google Sheet.\nError: {e}")
            
    def mark_done_and_next(self):
        self._update_status(STATUS_DONE_TEXT); self.load_and_validate_next_customer()

    def mark_invalid_and_next(self):
        self._update_status(STATUS_INVALID_TEXT); self.load_and_validate_next_customer()

    def open_login_window(self):
        login_window = Toplevel(self.root); login_window.title("API Gateway Login"); login_window.geometry("300x200")
        login_window.transient(self.root); login_window.grab_set()
        Label(login_window, text="Username:").pack(pady=(10,0)); user_entry = Entry(login_window, width=30); user_entry.pack(); user_entry.insert(0, DEFAULT_API_USERNAME)
        Label(login_window, text="Password:").pack(pady=(5,0)); pass_entry = Entry(login_window, show="*", width=30); pass_entry.pack(); pass_entry.insert(0, DEFAULT_API_PASSWORD)
        Label(login_window, text="Session Name:").pack(pady=(5,0)); session_entry = Entry(login_window, width=30); session_entry.pack(); session_entry.insert(0, self.api_session_name or DEFAULT_API_SESSION)
        
        def perform_login():
            user, pwd, session = user_entry.get(), pass_entry.get(), session_entry.get()
            if not all([user, pwd, session]): messagebox.showerror("Error", "All fields are required.", parent=login_window); return
            
            result = self.api_client.login(user, pwd)
            if self.api_client.token:
                self.api_session_name = session
                self.next_button.config(state=tk.NORMAL); self.invalid_button.config(state=tk.NORMAL)
                messagebox.showinfo("Success", "Successfully logged in. You may now begin.", parent=login_window)
                login_window.destroy()
                self.load_and_validate_next_customer()
            else:
                messagebox.showerror("Login Failed", f"Could not log in.\nServer says: {result}", parent=login_window)

        Button(login_window, text="Login", command=perform_login).pack(pady=15)

    def handle_auth_failure(self, error_message):
        self.api_client.token = None
        self.next_button.config(state=tk.DISABLED); self.invalid_button.config(state=tk.DISABLED)
        messagebox.showerror("Session Error", f"{error_message}\nPlease log in again.")
        self.open_login_window()

    def copy_phone_number(self): pyperclip.copy(self.phone_text.get("1.0", tk.END).strip())
    def copy_message_1(self): pyperclip.copy(self.msg1_text.get("1.0", tk.END).strip())
    def copy_message_2(self): pyperclip.copy(self.msg2_text.get("1.0", tk.END).strip())
    def show_log_window(self, log_type):
        if self.log_windows.get(log_type) and self.log_windows[log_type].winfo_exists(): self.log_windows[log_type].lift(); return
        log_window = Toplevel(self.root); log_window.title(f"{log_type} Log"); log_window.geometry("500x500")
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
    try:
        import gspread, pyperclip, requests
    except ImportError as e:
        module = str(e).split("'")[1]
        print(f"Required library '{module}' not found.")
        print(f"Please install it by running: pip install {module}")
        sys.exit()
    root = tk.Tk()
    app = WhatsAppHelperApp(root)
    root.mainloop()