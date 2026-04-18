import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_flights():
    try:
        response = requests.get(f"{BASE_URL}/flights/")
        print(f"Flights Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Flights Found: {response.json().get('count', 0)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_flights()
