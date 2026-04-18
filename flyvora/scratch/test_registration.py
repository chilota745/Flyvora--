import requests
import random

BASE_URL = "http://127.0.0.1:8000/api"

def test_registration():
    username = f"user_{random.randint(1000, 9999)}"
    password = "password123"
    email = f"{username}@example.com"
    
    try:
        response = requests.post(f"{BASE_URL}/register/", json={
            "username": username,
            "email": email,
            "password": password
        })
        print(f"Registration Status Code: {response.status_code}")
        if response.status_code == 201:
            print(f"Success! Token received: {response.json().get('token')}")
            return username, password
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Connection Failed: {e}")
    return None, None

if __name__ == "__main__":
    u, p = test_registration()
    if u:
        print(f"Registered user: {u}")
