import json
import pathlib
import os
import requests
from datetime import datetime, timezone, timedelta

ZERNIO_API_KEY = os.environ["ZERNIO_API_KEY"]
ZERNIO_ACCOUNT_ID = os.environ["ZERNIO_ACCOUNT_ID"]
BASE_URL = "https://zernio.com/api/v1"
HEADERS = {"Authorization": f"Bearer {ZERNIO_API_KEY}", "Content-Type": "application/json"}

def upload_slide(file_path):
    name = pathlib.Path(file_path).name

    res = requests.post(
        f"{BASE_URL}/media/presign",
        headers=HEADERS,
        json={"filename": name, "contentType": "image/jpeg"},
        timeout=15,
    )
    if not res.ok:
        print(f"Presign failed {res.status_code}: {res.text}")
    res.raise_for_status()
    data = res.json()
    upload_url = data["uploadUrl"]
    public_url = data["publicUrl"]

    with open(file_path, "rb") as f:
        put_res = requests.put(
            upload_url,
            headers={"Content-Type": "image/jpeg"},
            data=f,
            timeout=60,
        )
    put_res.raise_for_status()
    return public_url

def run():
    slides = json.loads(pathlib.Path("data/current_run/slide_paths.json").read_text())["slides"]
    caption_data = json.loads(pathlib.Path("data/current_run/caption.json").read_text())
    hooks_data = json.loads(pathlib.Path("data/current_run/hooks.json").read_text())

    print("Uploading slides to Zernio...")
    media_items = []
    for path in slides:
        public_url = upload_slide(path)
        media_items.append({"type": "image", "url": public_url})
        print(f"  Uploaded: {pathlib.Path(path).name}")

    # Schedule 5 min from now — API returns instantly, Zernio publishes async
    scheduled_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S")

    payload = {
        "content": caption_data["caption"],
        "mediaItems": media_items,
        "platforms": [{"platform": "instagram", "accountId": ZERNIO_ACCOUNT_ID}],
        "scheduledFor": scheduled_at,
    }

    res = requests.post(f"{BASE_URL}/posts", headers=HEADERS, json=payload, timeout=120)
    if not res.ok:
        print(f"Post failed {res.status_code}: {res.text}")
    res.raise_for_status()
    post_id = res.json().get("id", "unknown")

    log_entry = {
        "post_id": post_id,
        "hook": hooks_data["selected"]["text"],
        "scheduled_at": scheduled_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "slide_count": len(slides),
    }
    log_file = pathlib.Path("data/posts_log.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Post queued: {post_id}, publishes at: {scheduled_at} UTC")

if __name__ == "__main__":
    run()
