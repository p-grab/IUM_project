import random
import time
import requests
from models import ModelManager

BASE = "http://localhost:8080"

manager = ModelManager()
listings_a = set(manager.model_a['listing_id'].unique()) if manager.model_a is not None else set()
listings_b = set(manager.model_b['listing_id'].unique()) if manager.model_b is not None else set()

all_listings = list(listings_a | listings_b)

print(f"Model A: {len(listings_a)} unique listings")
print(f"Model B: {len(listings_b)} unique listings")
print(f"Unique total: {len(all_listings)}")

n = min(50, len(all_listings))
picked = random.sample(all_listings, n)

for i, listing_id in enumerate(picked, 1):
    try:
        r = requests.post(f"{BASE}/predict", json={"listing_id": int(listing_id), "top_k": 3})
        if r.ok:
            print(f"{i}/{n}: {listing_id} OK")
        else:
            print(f"{i}/{n}: {listing_id} HTTP {r.status_code}")
        time.sleep(0.1)
    except Exception as e:
        print(f"{i}/{n}: {listing_id} ERROR: {e}")

print("Finished!")