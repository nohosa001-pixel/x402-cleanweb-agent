import requests

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("\n--- 1. Testing Clean-Web (0.01 USDC) ---")
    r1 = requests.get(f"{BASE_URL}/api/v1/clean-web?url=https://example.com")
    print(f"Status: {r1.status_code}, Service: {r1.json().get('service')}, Price: {r1.json().get('x402', {}).get('amount')}")

    print("\n--- 2. Testing Clean-YouTube (0.02 USDC) ---")
    r2 = requests.get(f"{BASE_URL}/api/v1/clean-youtube?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print(f"Status: {r2.status_code}, Service: {r2.json().get('service')}, Price: {r2.json().get('x402', {}).get('amount')}")

    print("\n--- 3. Testing Clean-PDF (0.05 USDC) ---")
    r3 = requests.get(f"{BASE_URL}/api/v1/clean-pdf?url=https://arxiv.org/pdf/2301.00001.pdf")
    print(f"Status: {r3.status_code}, Service: {r3.json().get('service')}, Price: {r3.json().get('x402', {}).get('amount')}")

    print("\n--- 4. Testing Clean-Text (0.005 USDC) ---")
    r4 = requests.get(f"{BASE_URL}/api/v1/clean-text?url=https://example.com")
    print(f"Status: {r4.status_code}, Service: {r4.json().get('service')}, Price: {r4.json().get('x402', {}).get('amount')}")

    print("\n--- 5. Testing Root DApp UI ---")
    r5 = requests.get(f"{BASE_URL}/")
    print(f"Status: {r5.status_code}, Content-Type: {r5.headers.get('content-type')}, Length: {len(r5.text)} bytes")

if __name__ == "__main__":
    test_all()
