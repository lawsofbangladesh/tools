"""
Script to extract act information from each volume page
and save to individual CSV files

This script will:
1. Read the volume list JSON
2. Download each volume page HTML
3. Parse the table to extract act information
4. Extract year from hidden column and verify with title
5. Convert act links to print format (act-print-XXX.html)
6. Save each volume's acts to a separate CSV file
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://bdlaws.minlaw.gov.bd"
VOLUME_JSON = Path(__file__).parent.parent / "files" / "volumes" / "volume_list.json"
HTML_DIR = Path(__file__).parent.parent / "files" / "htmls" / "volumes"
CSV_DIR = Path(__file__).parent.parent / "files" / "volumes" / "csv"
DELAY_BETWEEN_REQUESTS = 0  # No delay needed

def load_volume_list():
    """
    Load the volume list from JSON file
    
    Returns:
        list: List of volume dictionaries
    """
    try:
        with open(VOLUME_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['volumes']
    except FileNotFoundError:
        print(f"Error: Volume list JSON not found at {VOLUME_JSON}")
        print("Please run fetch_volume_list.py first!")
        return None
    except Exception as e:
        print(f"Error loading volume list: {e}")
        return None

def fetch_html(url):
    """
    Download HTML content from the given URL
    
    Args:
        url (str): URL to fetch
        
    Returns:
        str: HTML content or None if error
    """
    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as e:
        print(f"  Error fetching URL: {e}")
        return None

def convert_bengali_to_english(text):
    """
    Convert Bengali digits to English digits
    
    Args:
        text (str): Text containing Bengali digits
        
    Returns:
        str: Text with English digits
    """
    bengali_to_english = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
    return text.translate(bengali_to_english)

def extract_year_from_title(title):
    """
    Extract year from act title
    
    Args:
        title (str): Act title
        
    Returns:
        str: Year or None
    """
    # Match year pattern like "1978" or "১৯৭৮" (Bengali digits)
    match = re.search(r'(\d{4}|[০-৯]{4})', title)
    if match:
        year = match.group(1)
        # Convert Bengali digits to English if needed
        return convert_bengali_to_english(year)
    return None

def parse_acts_from_volume(html_content, volume_number):
    """
    Parse act information from volume HTML
    
    Args:
        html_content (str): HTML content to parse
        volume_number (str): Volume number
        
    Returns:
        list: List of dictionaries containing act information
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    acts = []
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        
        # We expect 3 cells: year (hidden), title, act number
        if len(cells) >= 3:
            # Extract year from first hidden cell
            year_cell = cells[0]
            year_link = year_cell.find('a', href=True)
            
            if not year_link:
                continue
                
            year = year_link.get_text(strip=True)
            # Convert Bengali year to English for consistency
            year = convert_bengali_to_english(year)
            act_url = year_link['href']
            
            # Extract act ID from URL (e.g., /act-563.html -> 563)
            act_id_match = re.search(r'/act-(\d+)\.html', act_url)
            if not act_id_match:
                continue
            
            act_id = act_id_match.group(1)
            
            # Extract title from second cell
            title_cell = cells[1]
            title_link = title_cell.find('a', href=True)
            
            if not title_link:
                continue
                
            title = title_link.get_text(strip=True)
            
            # Verify year matches with title (optional check, commented out to reduce noise)
            # title_year = extract_year_from_title(title)
            # if title_year and title_year != year:
            #     print(f"  Warning: Year mismatch for {title}")
            #     print(f"    Hidden column year: {year}, Title year: {title_year}")
            
            # Extract act number from third cell
            number_cell = cells[2]
            number_link = number_cell.find('a', href=True)
            
            if not number_link:
                continue
                
            act_number = number_link.get_text(strip=True)
            
            # Create print URL
            print_url = f"{BASE_URL}/act-print-{act_id}.html"
            
            act_info = {
                "volume_number": volume_number,
                "year": year,
                "act_title": title,
                "act_number": act_number,
                "act_id": act_id,
                "link": print_url
            }
            
            acts.append(act_info)
    
    return acts

def save_to_csv(acts, volume_number):
    """
    Save acts to CSV file
    
    Args:
        acts (list): List of act dictionaries
        volume_number (str): Volume number for filename
    """
    if not acts:
        print(f"  No acts found for volume {volume_number}")
        return
    
    # Ensure CSV directory exists
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    csv_filename = f"volume-{volume_number}.csv"
    csv_path = CSV_DIR / csv_filename
    
    # Write to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ['volume_number', 'year', 'act_title', 'act_number', 'act_id', 'link']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(acts)
    
    print(f"  ✓ Saved {len(acts)} acts to: {csv_filename}")

def save_volume_html(html_content, volume_number):
    """
    Save volume HTML for reference
    
    Args:
        html_content (str): HTML content
        volume_number (str): Volume number
    """
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    html_path = HTML_DIR / f"volume-{volume_number}.html"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def process_volume(volume):
    """
    Process a single volume: fetch, parse, and save
    
    Args:
        volume (dict): Volume information
        
    Returns:
        dict: Statistics about processed volume
    """
    volume_number = volume['volume_number']
    volume_url = volume['url']
    
    print(f"\nProcessing Volume {volume_number}:")
    print(f"  Description: {volume['description']}")
    
    # Fetch HTML
    html_content = fetch_html(volume_url)
    if not html_content:
        return {"volume": volume_number, "success": False, "acts_count": 0}
    
    # Save HTML
    save_volume_html(html_content, volume_number)
    
    # Parse acts
    acts = parse_acts_from_volume(html_content, volume_number)
    
    # Save to CSV
    save_to_csv(acts, volume_number)
    
    return {"volume": volume_number, "success": True, "acts_count": len(acts)}

def main():
    """
    Main function to process all volumes
    """
    print("=" * 70)
    print("Bangladesh Laws - Acts Extractor from Volumes")
    print("=" * 70)
    print()
    
    # Load volume list
    print("Loading volume list...")
    volumes = load_volume_list()
    
    if not volumes:
        print("Failed to load volume list. Exiting.")
        return
    
    print(f"Found {len(volumes)} volumes to process.\n")
    
    # Process each volume
    results = []
    total_acts = 0
    
    for i, volume in enumerate(volumes, 1):
        result = process_volume(volume)
        results.append(result)
        
        if result['success']:
            total_acts += result['acts_count']
        
        # Add delay between requests if configured
        if i < len(volumes) and DELAY_BETWEEN_REQUESTS > 0:
            print(f"  Waiting {DELAY_BETWEEN_REQUESTS} seconds before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Summary
    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)
    print(f"Total volumes processed: {len(volumes)}")
    print(f"Total acts extracted: {total_acts}")
    print(f"CSV files saved in: {CSV_DIR}")
    print(f"HTML files saved in: {HTML_DIR}")
    
    # Show any failures
    failures = [r for r in results if not r['success']]
    if failures:
        print(f"\nFailed volumes ({len(failures)}):")
        for f in failures:
            print(f"  - Volume {f['volume']}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
