import json
import pathlib
import requests
import os
import time

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

STOICISM_QUERIES = [
    "ancient greek architecture dark moody",
    "stoic philosopher marble statue",
    "dramatic mountain landscape fog",
    "roman colosseum golden hour",
    "lone figure dark forest path",
    "ancient temple ruins misty",
    "dramatic ocean storm waves",
    "warrior silhouette sunset",
    "minimalist dark room candle light",
    "stone wall texture weathered ancient",
]

def fetch_pexels(query, slot_index):
    url = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "per_page": 10,
        "orientation": "portrait",
    }
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, params=params, headers=headers, timeout=15)
    res.raise_for_status()
    photos = res.json().get("photos", [])
    if not photos:
        print(f"  No results for query: {query}")
        return None

    photo = photos[slot_index % len(photos)]
    img_url = photo["src"]["large"]
    img_res = requests.get(img_url, timeout=30)
    img_res.raise_for_status()

    out_dir = pathlib.Path("data/current_run/raw_images")
    out_dir.mkdir(parents=True, exist_ok=True)
    img_path = out_dir / f"slide_{slot_index:02d}.jpg"
    img_path.write_bytes(img_res.content)
    return str(img_path)

def run():
    hooks_data = json.loads(pathlib.Path("data/current_run/hooks.json").read_text())
    selected_hook = hooks_data["selected"]
    print(f"Fetching images for hook: {selected_hook['text']}")

    image_paths = []
    for i, query in enumerate(STOICISM_QUERIES):
        print(f"  Fetching slot {i+1}/10: {query}")
        path = fetch_pexels(query, i)
        if path:
            image_paths.append(path)
        time.sleep(0.3)

    pathlib.Path("data/current_run/image_paths.json").write_text(
        json.dumps({"images": image_paths}, indent=2)
    )
    print(f"Fetched {len(image_paths)}/10 images")

if __name__ == "__main__":
    run()
