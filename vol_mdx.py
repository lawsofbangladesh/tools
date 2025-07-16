import os
import glob
import re
from bs4 import BeautifulSoup

def clean_text(text):
    """A simple helper to clean up whitespace."""
    return ' '.join(text.strip().split()) if text else ""

def extract_and_convert_volume(html_file_path, output_base_dir):
    """
    Extracts information from a volume HTML file, manually formats the table
    into the specified MDX structure, and saves it.
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # --- Metadata Extraction (Frontmatter) ---
        title_tag = soup.select_one('section.bg-act-section p.text-color-white')
        title = clean_text(title_tag.get_text()) if title_tag else "Volume Title Not Found"

        filename = os.path.basename(html_file_path)
        match = re.search(r'volume-(\d+)', filename)
        if not match:
            print(f"Warning: Could not determine volume number from filename: {filename}")
            return
            
        volume_number = match.group(1)
        sidebar_title = f"Volume {volume_number}"
        volume_folder_name = f"volume-{volume_number}"

        description = ""

        # --- Table Extraction and Manual Markdown Conversion ---
        table_tag = soup.select_one('table.datatable.table-search')
        if not table_tag:
            print(f"Warning: No data table found in {html_file_path}. Skipping file.")
            return

        # Manually build the markdown table string
        markdown_rows = []
        markdown_rows.append("| Year | Short Title | Act No |")
        markdown_rows.append("|------|-------------|--------|")

        for row in table_tag.select('tbody tr'):
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            # Column 1: Year (from the hidden first td)
            year = clean_text(cells[0].get_text())

            # Column 2: Short Title and Link
            title_cell_link = cells[1].find('a')
            title_text = "No Title"
            new_href = "#"
            if title_cell_link:
                title_text = clean_text(title_cell_link.get_text())
                original_href = title_cell_link.get('href', '')
                
                # Extract act ID (e.g., '48' from '/act-48.html')
                act_id_match = re.search(r'act-(\d+)', original_href)
                if act_id_match:
                    act_id = act_id_match.group(1)
                    # Construct the new link format
                    new_href = f"/laws/{volume_folder_name}/act-{act_id}"
                else:
                    # Fallback if the href format is unexpected
                    new_href = original_href

            # Column 3: Act No (text only)
            act_no = clean_text(cells[2].get_text())

            # Assemble the markdown table row
            markdown_rows.append(f"| {year} | [{title_text}]({new_href}) | {act_no} |")

        table_md = "\n".join(markdown_rows)
        
        # --- Final MDX Formatting ---
        mdx_content = f"""---
title: "{title}"
sidebarTitle: "{sidebar_title}"
description: "{description}"
---

{table_md}
"""

        # --- Saving the file ---
        output_dir = os.path.join(output_base_dir, volume_folder_name)
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'index.mdx')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mdx_content)
            
        print(f"Successfully converted {html_file_path} to {output_path}")

    except Exception as e:
        print(f"Could not process {html_file_path}. Error: {e}")

def main():
    """
    Main function to find all volume HTML files and run the conversion process.
    """
    # Ensure you have the required libraries installed:
    # pip install beautifulsoup4
    
    input_folder = 'vol_html'
    output_folder = 'laws'

    # Find all HTML files in the input folder
    html_files = glob.glob(os.path.join(input_folder, 'volume-*.html'))

    if not html_files:
        print(f"No 'volume-*.html' files found in the '{input_folder}' directory.")
        return

    for html_file in html_files:
        extract_and_convert_volume(html_file, output_folder)

if __name__ == '__main__':
    main()
