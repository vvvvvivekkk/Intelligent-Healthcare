import requests
import json

URL = "http://localhost:5000/api/admin/login"
DATA = {
    "username": "admin",
    "password": "admin123"
}

try:
    print(f"Testing POST {URL} with {DATA}...")
    resp = requests.post(URL, json=DATA)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
