import csv
import requests
from bs4 import BeautifulSoup
import os

BASE_URL = "http://bdlaws.minlaw.gov.bd"

# Create output folder
os.makedirs("volumes", exist_ok=True)

# Step 1: Read volumes.csv
with open("volumes.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row['Title']
        url = row['URL']
        volume_filename = url.split("/")[-1].replace(".html", "")  # e.g. volume-1

        print(f"Processing {volume_filename}...")

        try:
            # Step 2: Request volume page
            res = requests.get(url)
            soup = BeautifulSoup(res.content, "html.parser")

            # Step 3: Find table rows
            tbody = soup.find("tbody")
            rows = tbody.find_all("tr") if tbody else []

            data = []

            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) != 3:
                    continue  # Skip malformed rows

                # Extract data
                year_tag = tds[0].find("a")
                year = year_tag.text.strip() if year_tag else ""

                title_tag = tds[1].find("a")
                short_title = title_tag.text.strip() if title_tag else ""

                act_tag = tds[2].find("a")
                act_no = act_tag.text.strip() if act_tag else ""

                act_href = act_tag['href'] if act_tag and 'href' in act_tag.attrs else ""
                act_id = act_href.split("-")[-1].replace(".html", "")
                act_url = f"{BASE_URL}/act-print-{act_id}.html" if act_id.isdigit() else ""

                data.append({
                    "Year": year,
                    "Short Title": short_title,
                    "Act No": act_no,
                    "URL": act_url
                })

            # Step 4: Write to CSV
            out_csv_path = os.path.join("volumes", f"{volume_filename}.csv")
            with open(out_csv_path, "w", newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=["Year", "Short Title", "Act No", "URL"])
                writer.writeheader()
                writer.writerows(data)

        except Exception as e:
            print(f"Failed to process {title}: {e}")
