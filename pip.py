import os
import glob
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def clean_text(text):
    """A simple helper to clean up whitespace."""
    return ' '.join(text.strip().split()) if text else ""

def extract_and_convert(html_file_path, md_folder_path):
    """
    Extracts information from an HTML file, formats it into MDX using a 
    library for accurate conversion, and saves it.
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # --- Metadata Extraction (Frontmatter) ---
        title_tag = soup.select_one('.text-center h3')
        title = clean_text(title_tag.get_text()) if title_tag else "Title Not Found"

        number_tag = soup.select_one('.text-center h4')
        number = clean_text(number_tag.get_text()) if number_tag else "Number Not Found"

        description_tag = soup.select_one('.text-center.act-role-style strong')
        description = clean_text(description_tag.get_text()) if description_tag else "Description Not Found"
        
        date_tag = soup.select_one('.pull-right.publish-date')
        date = clean_text(date_tag.get_text()) if date_tag else "Date Not Found"

        # --- Content Extraction and Conversion ---
        
        # Preamble
        preamble_html = ''
        preamble_label = soup.find('div', class_='col-md-2', string=lambda t: t and 'Preamble' in t.strip())
        if preamble_label:
            preamble_content_div = preamble_label.find_next_sibling('div', class_='col-md-10')
            if preamble_content_div:
                preamble_html = str(preamble_content_div)
        else:
            # Fallback for introductory paragraphs without a "Preamble" label
            intro_div = soup.select_one('.row.lineremove .col-md-12.pad-right')
            if intro_div:
                preamble_html = str(intro_div)
        
        # Convert preamble HTML to Markdown
        preamble_md = md(preamble_html, heading_style="ATX") if preamble_html else "Preamble Not Found"


        # Sections/Articles
        sections = []
        for section_row in soup.select('section.padding-bottom-20 .row.lineremoves'):
            heading_tag = section_row.select_one('.col-sm-3.txt-head')
            details_tag = section_row.select_one('.col-sm-9.txt-details')
            
            if heading_tag and details_tag:
                heading = clean_text(heading_tag.get_text())
                # Convert the entire details div to markdown
                details_md = md(str(details_tag), heading_style="ATX", bullets='-')
                if heading:
                    sections.append(f"### {heading}\n\n{details_md}\n")
        sections_content = "\n".join(sections)

        # Footnotes
        footnotes_html = soup.select_one('.footnoteListAll')
        footnotes_md = ""
        if footnotes_html:
             # Convert the footnotes list to markdown
             footnotes_md = md(str(footnotes_html), heading_style="ATX", bullets='-')

        # --- MDX Formatting ---
        mdx_content = f"""---
title: "{title}"
sidebarTitle: "{number}"
description: "{description}"
---

**Date of Publication:** {date}

## Preamble
{preamble_md}

## Sections/Articles
{sections_content}

## Footnotes
{footnotes_md}
"""

        # --- Saving the file ---
        os.makedirs(os.path.dirname(md_folder_path), exist_ok=True)
        base_filename = os.path.basename(html_file_path)
        mdx_filename = os.path.splitext(base_filename)[0] + '.mdx'
        output_path = os.path.join(os.path.dirname(md_folder_path), mdx_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mdx_content)
            
        print(f"Successfully converted {html_file_path} to {output_path}")

    except Exception as e:
        print(f"Could not process {html_file_path}. Error: {e}")

def main():
    """
    Main function to run the conversion process.
    """
    # Make sure you have the required libraries installed:
    # pip install beautifulsoup4 markdownify
    
    html_folder = 'html'
    md_folder = 'pip'

    html_files = glob.glob(os.path.join(html_folder, '**', '*.html'), recursive=True)

    if not html_files:
        print(f"No HTML files found in the '{html_folder}' directory.")
        return

    for html_file in html_files:
        relative_path = os.path.relpath(html_file, html_folder)
        md_file_path = os.path.join(md_folder, relative_path)
        
        extract_and_convert(html_file, md_file_path)

if __name__ == '__main__':
    main()
