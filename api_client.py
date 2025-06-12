import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
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
                return data.get("message", "Login failed: Unknown error.")
        except requests.exceptions.RequestException as e:
            return str(e)

    def is_phone_registered(self, session_name, phone_number, country_code):
        if not self.token: return None, "You are not logged in.", True
        try:
            check_url = f"{self.base_url}/session/is-registered/{session_name}/{phone_number}"
            params = {"countryCode": country_code}
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(check_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            is_registered = data.get("isRegistered", False)
            return is_registered, None, False
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code in [401, 403]:
                return None, "Session expired or token is invalid.", True
            else:
                return None, str(e), False