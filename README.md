# WhatsApp Helper Application

A desktop application built with Python and Tkinter to streamline a WhatsApp messaging workflow. This tool helps manage customer data from a Google Sheet and validates phone numbers using an external API gateway.

## Features

- **Loads Customer Data:** Reads customer information directly from a specified Google Sheet.
- **Dynamic Message Templates:** Automatically generates greetings (`pagi`, `siang`, `sore`, `malam`) based on the time of day.
- **API Integration:** Connects to a WhatsApp API gateway to check if phone numbers are valid and registered.
- **Automated Workflow:** Automatically finds the next valid customer, skipping numbers that are invalid or have already been processed.
- **Session Management:** Handles API login and gracefully recovers from expired sessions by prompting for re-login.
- **Logging:** Keeps a running log of all successful (`SENT`) and failed (`INVALID`) contacts in separate, viewable windows for the current session.

## Setup

### 1. Prerequisites
Ensure you have Python 3 installed. Then, install the required libraries by running:
```bash
pip install gspread google-auth-oauthlib pyperclip requests ttkbootstrap
```

### 2. Configuration
The application requires two configuration files that are **not** included in the repository for security reasons.

- **`credentials.json`**: Your Google Cloud service account key. You must follow the `gspread` documentation to generate this file and enable the Google Sheets and Google Drive APIs.
- **`config.py`**: Your personal application settings.
    1. Rename the `config.py.example` file to `config.py`.
    2. Edit `config.py` and fill in your actual details (Google Sheet name, API URL, login credentials, etc.).

### 3. Google Sheets
1. Create a Google Sheet with the required headers (see `config.py.example`).
2. Share this sheet with the `client_email` found inside your `credentials.json` file, giving it "Editor" permissions.

## Usage

To run the application, navigate to the project folder in your command prompt or terminal and run:
```bash
python main.py
```
Upon launching, you must log in via the `API -> Login to Gateway...` menu to enable the main features.