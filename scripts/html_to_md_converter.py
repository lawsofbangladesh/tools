"""
HTML to Markdown Converter using markdownify library
Converts Bangladesh law HTML files to clean Markdown format
"""
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def convert_html_file(html_path, output_path):
    """
    Convert a single HTML file to Markdown
    """
    print(f"\nProcessing: {html_path}")
    
    # Read the HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Extract the main content section (the actual law content)
    content_div = soup.find('div', {'id': 'hide'})
    
    if not content_div:
        print(f"  ✗ Could not find main content div")
        return False
    
    # Convert to markdown using markdownify
    # Configure markdownify to handle the HTML properly
    markdown_content = md(
        str(content_div),
        heading_style="ATX",  # Use # for headings
        bullets="-",  # Use - for bullet lists
        strip=['script', 'style', 'link', 'meta'],  # Remove these tags
        escape_asterisks=False,  # Don't escape asterisks
        escape_underscores=False  # Don't escape underscores
    )
    
    # Save the markdown
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"  ✓ Converted to: {output_path}")
    return True

def main():
    """
    Convert the test HTML files
    """
    base_dir = Path(__file__).parent.parent
    
    # Test files to convert
    test_files = [
        ('files/htmls/laws/volume-14/act-356.html', 'files/md_raw/act-356.md'),
        ('files/htmls/laws/volume-14/act-365.html', 'files/md_raw/act-365.md'),
        ('files/htmls/laws/volume-26/act-678.html', 'files/md_raw/act-678.md'),
    ]
    
    print("=" * 80)
    print("HTML to Markdown Converter (using markdownify)")
    print("=" * 80)
    
    for html_file, output_file in test_files:
        html_path = base_dir / html_file
        output_path = base_dir / output_file
        
        if not html_path.exists():
            print(f"\n✗ HTML file not found: {html_path}")
            continue
        
        convert_html_file(html_path, output_path)
    
    print("\n" + "=" * 80)
    print("Conversion completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
