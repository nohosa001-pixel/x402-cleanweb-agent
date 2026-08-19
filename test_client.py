import requests

BASE_URL = "http://127.0.0.1:8000"

def test_clean_web():
    print("\n--- 1. Testing Clean-Web (Expecting HTTP 402 - 0.01 USDC) ---")
    url = f"{BASE_URL}/api/v1/clean-web?url=https://example.com"
    res = requests.get(url)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:", res.json())

def test_clean_youtube():
    print("\n--- 2. Testing Clean-YouTube (Expecting HTTP 402 - 0.02 USDC) ---")
    url = f"{BASE_URL}/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    res = requests.get(url)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:", res.json())

if __name__ == "__main__":
    test_clean_web()
    test_clean_youtube()
