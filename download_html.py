import os
import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# CONFIG
VOLUMES_DIR = "./volumes"
OUTPUT_DIR = "./html"
MAX_WORKERS = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# Ensure base output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_act_id(url):
    # Extracts the numeric act ID from the URL
    match = re.search(r'act-print-(\d+)\.html', url)
    return match.group(1) if match else None

def fetch_and_save(row, volume_name):
    url = row['URL'].strip()
    act_id = extract_act_id(url)

    if not act_id:
        return f"❌ Invalid act URL: {url}"

    output_subdir = os.path.join(OUTPUT_DIR, volume_name)
    os.makedirs(output_subdir, exist_ok=True)

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()

        filename = f"act-{act_id}.html"
        file_path = os.path.join(output_subdir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(res.text)

        return f"✅ Saved full source: {file_path}"
    except Exception as e:
        return f"❌ Error fetching {url} — {e}"

def process_volume(volume_csv_path):
    volume_name = os.path.splitext(os.path.basename(volume_csv_path))[0]  # e.g., volume-1

    with open(volume_csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_and_save, row, volume_name): row for row in rows}

        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    for filename in os.listdir(VOLUMES_DIR):
        if filename.endswith(".csv"):
            process_volume(os.path.join(VOLUMES_DIR, filename))
