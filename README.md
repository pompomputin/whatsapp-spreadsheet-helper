# WhatsApp Spreadsheet Helper

A robust desktop application built with Python and Tkinter to streamline customer messaging workflows. This tool connects a Google Sheet of contacts to a WhatsApp API gateway, automating number validation and message template generation.

![Application Screenshot](https://i.imgur.com/uO7z1fF.png)

---

## Features

- **Google Sheets Integration**: Directly reads and writes customer data from a specified Google Sheet.
- **Dynamic Message Templates**: Automatically generates greeting messages (`Selamat pagi/siang/sore/malam`) based on the user's local time.
- **WhatsApp API Validation**: Connects to an API gateway to check if phone numbers are valid and registered on WhatsApp before you send a message.
- **Automated Workflow**: Intelligently finds the next customer to process, automatically skipping those already marked as "SENT" or "INVALID".
- **Robust Session & Error Handling**:
    - Manages API login and token-based sessions.
    - Gracefully handles API connection errors (e.g., a server reboot) by pausing the application instead of incorrectly marking data as invalid.
    - Prompts for re-login if the API session expires.
- **Interactive UI**:
    - Displays all key customer data (Name, Phone, Username) in a clear, prominent panel.
    - "Previous" button to easily go back to the last viewed customer.
    - Real-time feedback on phone number status ("Registered", "Invalid", "Login to check").
- **Configurable Global Hotkeys**:
    - Copy message templates using keyboard shortcuts (e.g., F1, F2) that work even when the app is not in focus.
    - Hotkeys are fully configurable via the `config.ini` file.
- **Session Logging**: Keeps a running log of all successful and failed contacts in separate, viewable windows for the current session.

---

## Setup & Installation Guide

Follow these steps carefully to get the application running.

### Step 1: Clone the Repository

First, clone this repository to your local machine using Git:

```bash
git clone https://github.com/YourUsername/whatsapp-spreadsheet-helper.git
cd whatsapp-spreadsheet-helper
```
(Replace `YourUsername` with your actual GitHub username.)

---

### Step 2: Install Dependencies

This project uses several Python libraries. It is highly recommended to use a `requirements.txt` file for easy installation.

Create a file named `requirements.txt` in the project folder and paste the following lines into it:

```
gspread
google-auth-oauthlib
pyperclip
requests
keyboard
```

Now, install all the required libraries by running this command in your terminal:

```bash
pip install -r requirements.txt
```

---

### Step 3: Google Cloud & Credentials Setup

The application uses a Google Cloud Service Account to securely access your Google Sheet.

#### 1. Create a Google Cloud Project
Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.

#### 2. Enable APIs
In your new project, go to the "APIs & Services" > "Library" section and enable these two APIs:
- Google Drive API
- Google Sheets API

#### 3. Create a Service Account
- Go to "APIs & Services" > "Credentials".
- Click "Create Credentials" and select "Service account".
- Give it a name (e.g., "sheets-editor") and click "Create and Continue".
- For the role, select "Project" > "Editor" and click "Continue".
- Skip the last step and click "Done".

#### 4. Generate a JSON Key
- On the Credentials page, find your newly created service account and click on it.
- Go to the "KEYS" tab.
- Click "ADD KEY" > "Create new key".
- Select JSON as the key type and click "CREATE".
- A JSON file will be downloaded. Rename this file to `credentials.json` and place it in the root of your project folder. **This file is your private key and should never be shared publicly.**

---

### Step 4: Google Sheet Setup

#### 1. Create the Sheet
Create a new Google Sheet.

#### 2. Set Up Columns
Add the following headers in the first row of your sheet (the names must match exactly):

- PHONE NUMBER
- NAMA
- USERNAME
- LAST LOGIN
- TERKIRIM

#### 3. Share the Sheet
- Open your `credentials.json` file. Find the `client_email` address inside it (it will look something like `your-service-account@your-project.iam.gserviceaccount.com`).
- In your Google Sheet, click the "Share" button.
- Paste the `client_email` address into the sharing dialog and give it Editor permissions.

---

### Step 5: Application Configuration

Configure the application's settings.

- In the project folder, find the `example.config.ini` file.
- Make a copy of this file and rename the copy to `config.ini`.
- Open `config.ini` with a text editor and fill in the values for your setup. The file is divided into sections:
  - `[DEFAULT]`: Set your `google_sheet_name` and `worksheet_name`.
  - `[API]`: Enter the `base_url` for your WhatsApp gateway and your username, password, and session name.
  - `[COLUMNS]`: These should already match the sheet headers. Do not change them unless you also change your sheet.
  - `[MACROS]`: You can customize the global hotkeys here (e.g., F1, F2, F3).

---

## How to Use

**Run as Administrator (Important!):**  
For the global hotkeys (F1, F2, etc.) to work when the application is not in focus, you must run it with administrator privileges.

Right-click your command prompt (or IDE) and choose "Run as administrator" before running the script.

---

### Launch the Application

```bash
python main.py
```

- **Login:** The application will load the first customer from the sheet, but most features are disabled. Go to the menu `API -> Login to Gateway...` and enter your credentials to activate the tool.

---

### Workflow

- Once logged in, the app will automatically find the next available customer and check if their phone number is registered.
- Use the "Copy Message" buttons or your configured hotkeys to copy the templates.
- Click "Mark as Done" or "Mark as Invalid" to update the sheet and automatically load the next customer.
- Use the "< Previous Customer" button if the app skips ahead and you need to go back one step.

---

## Building an Executable (.exe)

You can package this application into a single `.exe` file that can be run on other Windows computers without needing Python installed.

1. **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2. **Run the Build Command:**  
   From your project directory, run the following command. It includes all necessary files and hides the background console window.

    ```bash
    pyinstaller --onefile --windowed --name WhatsAppHelper --add-data "config.ini;." --add-data "credentials.json;." main.py
    ```

3. **Find Your Application:**  
    Your `WhatsAppHelper.exe` file will be inside the newly created `dist` folder. Remember to run it as an administrator for the global hotkeys to function correctly.

---