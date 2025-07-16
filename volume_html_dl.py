import os
import csv
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Config
CSV_FILE = 'volumes.csv'
OUTPUT_DIR = 'vol_html'
MAX_WORKERS = 8  # Adjust based on your internet/CPU
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} {message}")

def get_filename_from_url(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

def download_and_save(url):
    filename = get_filename_from_url(url)
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        log(f"⬇️  Fetching {url}")
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        log(f"✅ Saved to {filepath}")
        return filepath

    except Exception as e:
        log(f"❌ Failed to fetch {url}: {e}")
        return None

def main():
    urls = []

    # Read CSV and extract URLs
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row['URL'].strip()
            urls.append(url)

    log(f"📄 Loaded {len(urls)} URLs from {CSV_FILE}")

    # Start parallel downloading
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(download_and_save, url): url for url in urls}

        for future in as_completed(future_to_url):
            future.result()  # triggers logging inside function

if __name__ == "__main__":
    main()
