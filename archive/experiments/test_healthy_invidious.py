import requests

def get_healthy_invidious_instances():
    try:
        r = requests.get("https://api.invidious.io/instances.json?sort_by=health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            healthy = []
            for item in data:
                # item is [domain_name, info_dict]
                domain = item[0]
                info = item[1]
                if info.get("type") == "https" and info.get("api") and info.get("cors"):
                    healthy.append(info.get("uri"))
            return healthy
    except Exception as e:
        print("Failed to get instances list:", e)
    return []

if __name__ == "__main__":
    instances = get_healthy_invidious_instances()
    print(f"Found {len(instances)} healthy instances:", instances[:5])
    
    for uri in instances[:10]:
        try:
            print(f"Testing {uri}/api/v1/captions/aircAruvnKk ...")
            r = requests.get(f"{uri}/api/v1/captions/aircAruvnKk", timeout=4)
            if r.status_code == 200:
                print(">>> SUCCESS on", uri)
                captions = r.json().get("captions", [])
                print("Captions available:", len(captions))
                if captions:
                    sub_url = f"{uri}{captions[0]['url']}"
                    sub_r = requests.get(sub_url, timeout=4)
                    print("Sub length:", len(sub_r.text))
                    print("Sample:\n", sub_r.text[:300])
                    break
        except Exception as e:
            print(f"Failed {uri}: {e}")
