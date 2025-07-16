import os
import json
import re

def natural_sort_key(s):
    """
    A key for natural sorting of strings.
    For example: 'act-2.mdx' comes before 'act-10.mdx'.
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def create_navigation_json(root_dir='markdown', output_file='docs.json'):
    """
    Scans a directory of markdown files and creates a JSON file
    for navigation based on the folder structure.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: The directory '{root_dir}' was not found.")
        return

    # Initialize the main JSON structure
    nav_data = {
        "pages": [
            "laws/index"
        ]
    }

    # Find all volume directories, e.g., 'markdown/volume-1', 'markdown/volume-2'
    try:
        volume_dirs = [d.path for d in os.scandir(root_dir) if d.is_dir() and d.name.startswith('volume-')]
        # Sort directories naturally by volume number
        volume_dirs.sort(key=natural_sort_key)
    except FileNotFoundError:
        print(f"Error: Could not scan the directory '{root_dir}'. Make sure it exists.")
        return

    # Process each volume directory
    for vol_path in volume_dirs:
        vol_name = os.path.basename(vol_path)  # e.g., 'volume-1'
        match = re.search(r'\d+', vol_name)
        if not match:
            continue
        
        volume_number = match.group(0)
        
        # Create the group object for this volume
        volume_group = {
            "group": f"Volume {volume_number}",
            "icon": "book",
            "pages": []
        }

        # Find all .mdx files within the volume directory
        try:
            mdx_files = [f for f in os.listdir(vol_path) if f.endswith('.mdx')]
            # Sort files naturally (index.mdx first, then act-1, act-2, etc.)
            mdx_files.sort(key=lambda x: (x != 'index.mdx', natural_sort_key(x)))
        except FileNotFoundError:
            print(f"Warning: Could not read files in '{vol_path}'. Skipping.")
            continue

        # Create the page paths for the JSON
        for mdx_file in mdx_files:
            # Remove the .mdx extension
            page_name = os.path.splitext(mdx_file)[0]
            # Construct the relative path
            page_path = f"laws/{vol_name}/{page_name}"
            volume_group["pages"].append(page_path)
            
        # Add the completed group to the main pages list
        nav_data["pages"].append(volume_group)

    # Write the final JSON structure to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(nav_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully created navigation file at '{output_file}'")
    except IOError as e:
        print(f"Error writing to file '{output_file}': {e}")

if __name__ == '__main__':
    # Assuming your markdown files are in a directory named 'markdown'
    # in the same location as this script.
    create_navigation_json()
