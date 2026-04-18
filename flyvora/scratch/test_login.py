import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_login(username, password):
    try:
        response = requests.post(f"{BASE_URL}/token/", data={"username": username, "password": password})
        print(f"Login Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Token: {response.json().get('token')}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    # Assuming there's a user 'testuser' with password 'password123' 
    # Or I should check what users are available.
    test_login("admin", "admin") 
