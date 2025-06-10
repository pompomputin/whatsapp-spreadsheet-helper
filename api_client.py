import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        """Attempts to log in and returns the token if successful."""
        try:
            login_url = f"{self.base_url}/auth/login"
            payload = {"username": username, "password": password}
            response = requests.post(login_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success") and data.get("token"):
                self.token = data["token"]
                return self.token
            else:
                # Return the error message from the server if login fails
                return data.get("message", "Login failed: Unknown error.")
        except requests.exceptions.RequestException as e:
            # Return the exception message if there's a network issue
            return str(e)

    def is_phone_registered(self, session_name, phone_number, country_code):
        """
        Checks if a phone number is on WhatsApp.
        Returns a tuple: (is_registered, error_message, is_auth_error)
        """
        if not self.token:
            return None, "You are not logged in.", True

        try:
            check_url = f"{self.base_url}/session/is-registered/{session_name}/{phone_number}"
            params = {"countryCode": country_code}
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(check_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            is_registered = data.get("isRegistered", False)
            return is_registered, None, False # Success
            
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code in [401, 403]:
                # This is a specific authentication error
                return None, "Session expired or token is invalid.", True
            else:
                # This is a general network or server error
                return None, str(e), False