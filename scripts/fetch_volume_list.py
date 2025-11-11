"""
Script to fetch and extract the list of law volumes from Bangladesh Laws website
http://bdlaws.minlaw.gov.bd/laws-of-bangladesh.html

This script will:
1. Download the HTML page
2. Parse the volume links
3. Extract volume number, description, and URL
4. Save the data to a JSON file in files/volumes/
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://bdlaws.minlaw.gov.bd"
TARGET_URL = f"{BASE_URL}/laws-of-bangladesh.html"
OUTPUT_DIR = Path(__file__).parent.parent / "files" / "volumes"
HTML_DIR = Path(__file__).parent.parent / "files" / "htmls"

def fetch_html(url):
    """
    Download HTML content from the given URL
    
    Args:
        url (str): URL to fetch
        
    Returns:
        str: HTML content or None if error
    """
    try:
        print(f"Fetching URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes
        response.encoding = response.apparent_encoding  # Handle encoding properly
        print(f"Successfully fetched URL (Status: {response.status_code})")
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def parse_volumes(html_content):
    """
    Parse the HTML content and extract volume information
    
    Args:
        html_content (str): HTML content to parse
        
    Returns:
        list: List of dictionaries containing volume information
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    volumes = []
    
    # Find all links that match the volume pattern
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        
        # Check if this is a volume link
        if 'volume-' in href and '.html' in href:
            # Extract volume number from URL
            volume_num = href.replace('http://bdlaws.minlaw.gov.bd/volume-', '')\
                            .replace('.html', '')\
                            .replace('/volume-', '')
            
            # Get the description text
            description = link.get_text(strip=True)
            
            # Build full URL if needed
            if not href.startswith('http'):
                full_url = f"{BASE_URL}/{href.lstrip('/')}"
            else:
                full_url = href
            
            volume_info = {
                "volume_number": volume_num,
                "description": description,
                "url": full_url
            }
            
            volumes.append(volume_info)
            print(f"Found Volume {volume_num}: {description[:50]}...")
    
    return volumes

def save_to_json(data, filename="volume_list.json"):
    """
    Save the volume data to a JSON file
    
    Args:
        data (list): List of volume dictionaries
        filename (str): Output filename
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = OUTPUT_DIR / filename
    
    # Prepare the output data with metadata
    output_data = {
        "metadata": {
            "source_url": TARGET_URL,
            "fetched_date": datetime.now().isoformat(),
            "total_volumes": len(data)
        },
        "volumes": data
    }
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nData saved to: {output_path}")
    print(f"Total volumes extracted: {len(data)}")

def save_html(html_content, filename="laws-of-bangladesh.html"):
    """
    Save the raw HTML content for reference
    
    Args:
        html_content (str): HTML content to save
        filename (str): Output filename
    """
    # Ensure HTML directory exists
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = HTML_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML saved to: {output_path}")

def main():
    """
    Main function to execute the script
    """
    print("=" * 70)
    print("Bangladesh Laws - Volume List Fetcher")
    print("=" * 70)
    print()
    
    # Step 1: Fetch the HTML
    html_content = fetch_html(TARGET_URL)
    if not html_content:
        print("Failed to fetch HTML. Exiting.")
        return
    
    # Step 2: Save the HTML for reference
    print("\nSaving HTML file...")
    save_html(html_content)
    
    # Step 3: Parse volumes
    print("\nParsing volume information...")
    volumes = parse_volumes(html_content)
    
    if not volumes:
        print("No volumes found. Please check the HTML structure.")
        return
    
    # Step 4: Save to JSON
    print("\nSaving to JSON...")
    save_to_json(volumes)
    
    print("\n" + "=" * 70)
    print("Process completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
