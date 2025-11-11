"""
Script to download individual act HTMLs from all volume CSV files

This script will:
1. Read all volume CSV files
2. Visit each act link
3. Download and prettify the HTML
4. Save in organized folder structure: htmls/laws/volume-[no]/act-[id].html
5. Use parallel processing for faster downloads
"""

import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
BASE_URL = "http://bdlaws.minlaw.gov.bd"
CSV_DIR = Path(__file__).parent.parent / "files" / "volumes" / "csv"
HTML_OUTPUT_DIR = Path(__file__).parent.parent / "files" / "htmls" / "laws"
MAX_RETRIES = 3  # Number of retries for failed requests
MAX_WORKERS = 10  # Number of parallel download threads

# Thread-safe counter for progress
progress_lock = threading.Lock()
progress_counter = {"completed": 0, "total": 0}

def get_all_csv_files():
    """
    Get all volume CSV files
    
    Returns:
        list: List of CSV file paths
    """
    csv_files = sorted(CSV_DIR.glob("volume-*.csv"))
    return csv_files

def read_acts_from_csv(csv_path):
    """
    Read acts from a CSV file
    
    Args:
        csv_path (Path): Path to CSV file
        
    Returns:
        list: List of act dictionaries
    """
    acts = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                acts.append(row)
    except Exception as e:
        print(f"  Error reading CSV {csv_path}: {e}")
    
    return acts

def fetch_and_prettify_html(url, retries=MAX_RETRIES):
    """
    Download HTML and prettify it
    
    Args:
        url (str): URL to fetch
        retries (int): Number of retries left
        
    Returns:
        str: Prettified HTML or None if error
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            # Prettify the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            prettified = soup.prettify()
            
            return prettified
        except requests.RequestException as e:
            if attempt < retries - 1:
                continue  # Just retry without printing
            else:
                return None
    
    return None

def save_html(html_content, volume_number, act_id):
    """
    Save HTML to file in organized structure
    
    Args:
        html_content (str): HTML content to save
        volume_number (str): Volume number
        act_id (str): Act ID
    """
    # Create directory for this volume
    volume_dir = HTML_OUTPUT_DIR / f"volume-{volume_number}"
    volume_dir.mkdir(parents=True, exist_ok=True)
    
    # Save HTML file
    html_path = volume_dir / f"act-{act_id}.html"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def process_act(act):
    """
    Download and save a single act
    
    Args:
        act (dict): Act information
        
    Returns:
        dict: Result with success status and act info
    """
    volume_number = act['volume_number']
    act_id = act['act_id']
    act_title = act['act_title']
    link = act['link']
    
    # Fetch and prettify HTML
    html_content = fetch_and_prettify_html(link)
    
    if not html_content:
        return {
            "success": False,
            "volume": volume_number,
            "act_id": act_id,
            "title": act_title
        }
    
    # Save HTML
    save_html(html_content, volume_number, act_id)
    
    # Update progress
    with progress_lock:
        progress_counter["completed"] += 1
        completed = progress_counter["completed"]
        total = progress_counter["total"]
        if completed % 10 == 0 or completed == total:
            print(f"Progress: {completed}/{total} acts downloaded ({completed*100//total}%)")
    
    return {
        "success": True,
        "volume": volume_number,
        "act_id": act_id,
        "title": act_title
    }

def collect_all_acts():
    """
    Collect all acts from all CSV files
    
    Returns:
        list: List of all acts to process
    """
    all_acts = []
    csv_files = get_all_csv_files()
    
    for csv_file in csv_files:
        acts = read_acts_from_csv(csv_file)
        all_acts.extend(acts)
    
    return all_acts

def main():
    """
    Main function to process all volumes with parallel processing
    """
    print("=" * 70)
    print("Bangladesh Laws - Act HTML Downloader (Parallel)")
    print("=" * 70)
    print()
    
    start_time = datetime.now()
    
    # Get all CSV files
    print("Finding volume CSV files...")
    csv_files = get_all_csv_files()
    
    if not csv_files:
        print(f"No CSV files found in {CSV_DIR}")
        return
    
    print(f"Found {len(csv_files)} volume CSV files")
    
    # Collect all acts
    print("Collecting all acts from CSV files...")
    all_acts = collect_all_acts()
    
    if not all_acts:
        print("No acts found to process")
        return
    
    print(f"Found {len(all_acts)} acts to download")
    print(f"Using {MAX_WORKERS} parallel workers\n")
    
    # Initialize progress counter
    progress_counter["total"] = len(all_acts)
    progress_counter["completed"] = 0
    
    # Process acts in parallel
    failed_acts = []
    successful_acts = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_act = {executor.submit(process_act, act): act for act in all_acts}
        
        # Process completed tasks
        for future in as_completed(future_to_act):
            result = future.result()
            
            if result["success"]:
                successful_acts += 1
            else:
                failed_acts.append(result)
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)
    print(f"Total volumes processed: {len(csv_files)}")
    print(f"Total acts processed: {len(all_acts)}")
    print(f"Successfully downloaded: {successful_acts}")
    print(f"Failed downloads: {len(failed_acts)}")
    print(f"Time taken: {duration}")
    print(f"Average speed: {len(all_acts) / duration.total_seconds():.2f} acts/second")
    print(f"HTML files saved in: {HTML_OUTPUT_DIR}")
    
    # Show failed acts if any
    if failed_acts:
        print(f"\nFailed acts ({len(failed_acts)}):")
        for fail in failed_acts[:20]:  # Show first 20 failures
            print(f"  Volume {fail['volume']}, Act {fail['act_id']}: {fail['title'][:60]}...")
        if len(failed_acts) > 20:
            print(f"  ... and {len(failed_acts) - 20} more")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
