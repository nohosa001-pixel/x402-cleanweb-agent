import requests

BASE_URL = "http://127.0.0.1:8000"

def test_no_payment():
    print("\n--- 1. Testing without X-Payment-Tx Header (Expecting HTTP 402) ---")
    url = f"{BASE_URL}/api/v1/clean-web?url=https://example.com"
    res = requests.get(url)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:")
    print(res.json())

def test_invalid_payment():
    print("\n--- 2. Testing with Invalid X-Payment-Tx Header (Expecting HTTP 402) ---")
    url = f"{BASE_URL}/api/v1/clean-web?url=https://example.com"
    headers = {
        "X-Payment-Tx": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    }
    res = requests.get(url, headers=headers)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:")
    print(res.json())

if __name__ == "__main__":
    test_no_payment()
    test_invalid_payment()
