import requests

r = requests.get("https://api.invidious.io/instances.json", timeout=5)
print("Status:", r.status_code)
data = r.json()
print("Type:", type(data))
if isinstance(data, list):
    for entry in data[:5]:
        print(entry[0], entry[1].get("uri"), entry[1].get("type"))
