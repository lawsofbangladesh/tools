#!/usr/bin/env python3
"""
Bangladesh Laws HTML to MDX Converter
======================================

This script converts all Bangladesh law HTML files from the Bangladesh Legal Database
to clean MDX format suitable for documentation websites.

Features:
- Extracts metadata (title, description, publication date)
- Preserves preamble text (Bengali and English)
- Converts sections with proper heading hierarchy
- Extracts and links footnotes (clickable superscript references)
- Converts internal act references to markdown links
- Handles both Bengali and English laws
- Supports repealed act notices

Directory Structure:
- Input: files/htmls/laws/volume-*/act-*.html
- Output: files/md_output/act-*.mdx

Author: Laws of Bangladesh Project
Date: November 2025
"""

import os
import re
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import argparse

def extract_act_id(filename):
    """Extract act number from filename"""
    match = re.search(r'act-(\d+)', filename)
    return match.group(1) if match else None

def clean_text(text):
    """Clean text by removing extra whitespace"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def process_content_with_links(element, footnotes_dict=None):
    """Process element content, converting links to markdown and collecting footnotes
    
    Args:
        element: BeautifulSoup element to process
        footnotes_dict: Dictionary to collect inline footnotes {number: text}
    
    Returns:
        Processed text with markdown links and footnote references
    """
    if not element:
        return ""
    
    # Handle string nodes directly
    if isinstance(element, str):
        return element.strip()
    
    # Handle NavigableString
    if not hasattr(element, 'children'):
        return str(element).strip()
    
    result = []
    for child in element.children:
        if hasattr(child, 'name'):
            if child.name == 'a':
                href = child.get('href', '')
                text = child.get_text(strip=True)
                title = child.get('title', '')
                if href.startswith('/act-'):
                    act_match = re.search(r'/act-(\d+)', href)
                    if act_match:
                        if title:
                            result.append(f'[{text}](/laws/act-{act_match.group(1)} "{title}")')
                        else:
                            result.append(f"[{text}](/laws/act-{act_match.group(1)})")
                    else:
                        result.append(text)
                else:
                    result.append(text)
            elif child.name == 'span' and 'footnote' in child.get('class', []):
                # Handle footnote markers - extract the number and footnote text
                sup = child.find('sup', class_='en')
                if sup:
                    a_tag = sup.find('a')
                    if a_tag:
                        footnote_num = clean_text(a_tag.get_text())
                        # Get footnote text from title attribute
                        footnote_text = child.get('title', '')
                        
                        # Store footnote if dict provided
                        if footnotes_dict is not None and footnote_text:
                            # Process footnote text recursively to convert any internal links
                            from bs4 import BeautifulSoup
                            footnote_soup = BeautifulSoup(footnote_text, 'html.parser')
                            footnote_text = process_content_with_links(footnote_soup, None)
                            footnotes_dict[footnote_num] = clean_text(footnote_text)
                        
                        # Use superscript with anchor link for proper footnote reference
                        result.append(f'<sup>[[{footnote_num}]](#footnote-{footnote_num})</sup>')
                    else:
                        # If no a tag, just get sup text
                        footnote_num = clean_text(sup.get_text())
                        result.append(f'<sup>[[{footnote_num}]](#footnote-{footnote_num})</sup>')
            elif child.name == 'div':
                # Skip div.clbr and div.na
                if 'clbr' not in child.get('class', []) and 'na' not in child.get('class', []):
                    result.append(process_content_with_links(child, footnotes_dict))
            else:
                # Recursively process other tags
                result.append(process_content_with_links(child, footnotes_dict))
        else:
            # Text node
            text = str(child).strip()
            if text:
                result.append(text)
    
    return ' '.join(result)

def extract_metadata(soup):
    """Extract metadata from HTML"""
    metadata = {}
    
    # Find the first lineremove div with title and act number
    title_section = soup.find('div', class_='lineremove')
    if title_section:
        h3 = title_section.find('h3')
        h4 = title_section.find('h4')
        
        metadata['title'] = clean_text(h3.get_text()) if h3 else ""
        
        # Extract sidebarTitle from h4, cleaning up whitespace
        if h4:
            h4_text = clean_text(h4.get_text())
            metadata['sidebarTitle'] = h4_text
        else:
            metadata['sidebarTitle'] = ""
    
    # Extract description
    desc_div = soup.find('div', class_='act-role-style')
    if desc_div:
        metadata['description'] = clean_text(desc_div.get_text())
    else:
        metadata['description'] = ""
    
    # Extract date - keep the brackets
    date_p = soup.find('p', class_='publish-date')
    if date_p:
        date_text = clean_text(date_p.get_text())
        metadata['date'] = date_text  # Keep full format with brackets
    else:
        metadata['date'] = ""
    
    return metadata

def extract_preamble(soup, footnotes_dict=None):
    """Extract preamble text from Bengali/English law structure
    
    Preamble structure:
    Bengali laws: Text between clbr divs starting with যেহেতু and সেহেতু
    English laws: <p> tags with WHEREAS... and It is hereby enacted...
    
    Args:
        soup: BeautifulSoup object
        footnotes_dict: Dictionary to collect inline footnotes
    
    Returns:
        Preamble text as string
    """
    # Find all divs with 'lineremove' class or inside description sections
    potential_divs = soup.find_all(['div'])
    
    # Look for divs containing preamble keywords
    for div in potential_divs:
        full_text = div.get_text()
        
        # Check for Bengali preamble
        has_bengali_preamble = 'যেহেতু' in full_text and 'সেহেতু' in full_text
        # Check for English preamble
        has_english_preamble = ('WHEREAS' in full_text and 'It is hereby enacted' in full_text) or \
                              ('WHEREAS' in full_text and 'NOW, THEREFORE' in full_text)
        
        if not (has_bengali_preamble or has_english_preamble):
            continue
        
        # For English laws, look for <p> tags with preamble text
        if has_english_preamble:
            p_tags = div.find_all('p', recursive=True)
            preamble_parts = []
            collecting = False
            
            for p in p_tags:
                p_text = p.get_text(strip=True)
                # Start collecting when we see WHEREAS
                if 'WHEREAS' in p_text:
                    collecting = True
                
                if collecting:
                    # Process the p tag content with links
                    processed_text = process_content_with_links(p, footnotes_dict)
                    preamble_parts.append(processed_text)
                    
                    # Stop after "It is hereby enacted" or "NOW, THEREFORE"
                    if 'It is hereby enacted' in p_text or 'NOW, THEREFORE' in p_text:
                        break
            
            if preamble_parts:
                return clean_text(' '.join(preamble_parts))
        
        # For Bengali laws, extract text from pad-right div
        pad_right_div = div.find('div', class_='pad-right')
        if pad_right_div and has_bengali_preamble:
            # Extract all text nodes from the div, skipping clbr/na divs
            preamble_parts = []
            collecting = False  # Start collecting when we see যেহেতু
            
            for child in pad_right_div.descendants:
                if isinstance(child, str):
                    text = child.strip()
                    if text:
                        # Check if this text is directly under pad-right, not inside clbr/na
                        parent = child.parent
                        if parent and hasattr(parent, 'get'):
                            parent_classes = parent.get('class', [])
                            # Skip text inside clbr or na divs
                            if 'clbr' in parent_classes or 'na' in parent_classes:
                                continue
                            # Check if parent is the pad-right div itself or close to it
                            if parent == pad_right_div or parent.parent == pad_right_div:
                                # Start collecting when we see যেহেতু
                                if 'যেহেতু' in text:
                                    collecting = True
                                
                                # Add text if we're collecting
                                if collecting:
                                    preamble_parts.append(text)
            
            if preamble_parts:
                preamble_text = ' '.join(preamble_parts)
                return clean_text(preamble_text)
    
    return ""

def extract_sections(soup, footnotes_dict=None):
    """Extract sections from lineremoves divs
    
    Args:
        soup: BeautifulSoup object
        footnotes_dict: Dictionary to collect inline footnotes
    
    Returns:
        List of section dictionaries with type, heading, and content
    """
    sections = []
    
    # Find all lineremoves divs
    section_divs = soup.find_all('div', class_='lineremoves')
    
    for div in section_divs:
        # Check if this section is repealed (skip if needed, but still process)
        is_repealed = 'repealed' in div.get('class', [])
        
        # Check for Part heading
        part_group = div.find('div', class_='act-part-group')
        if part_group:
            part_no = part_group.find('p', class_='act-part-no')
            part_name = part_group.find('p', class_='act-part-name')
            if part_no and part_name:
                part_text = f"{clean_text(part_no.get_text())} - {clean_text(part_name.get_text())}"
                sections.append({
                    'type': 'part',
                    'content': part_text
                })
        
        # Extract section heading and content
        heading_div = div.find('div', class_='txt-head')
        content_div = div.find('div', class_='txt-details')
        
        if heading_div or content_div:
            heading = clean_text(heading_div.get_text()) if heading_div else ""
            
            # Process content with links and collect footnotes
            if content_div:
                content = process_content_with_links(content_div, footnotes_dict)
                
                # Handle footnote markers [* * *]
                content = re.sub(r'\[\*\s*\*\s*\*\]', r'[\* \* \*]', content)
                
                sections.append({
                    'type': 'section',
                    'heading': heading,
                    'content': content
                })
    
    return sections

def extract_footnotes(soup, inline_footnotes=None):
    """Extract footnotes from footnoteListAll div and merge with inline footnotes
    
    Args:
        soup: BeautifulSoup object
        inline_footnotes: Dictionary of inline footnotes collected from content {number: text}
    
    Returns:
        List of footnote dictionaries with 'number' and 'text' keys
    """
    footnotes = []
    footnotes_dict = inline_footnotes.copy() if inline_footnotes else {}
    
    # Extract from footnoteListAll section (bottom of page footnotes)
    footnote_section = soup.find('div', class_='footnoteListAll')
    if footnote_section:
        footnote_items = footnote_section.find_all('li', class_='footnoteList')
        
        for item in footnote_items:
            # Extract footnote number
            h6 = item.find('h6')
            if h6:
                sup = h6.find('sup')
                if sup:
                    footnote_num = clean_text(sup.get_text())
                    
                    # Extract footnote text (remove h6 and get remaining text)
                    h6.decompose()  # Remove h6 from the item
                    footnote_text = process_content_with_links(item)
                    footnote_text = clean_text(footnote_text)
                    
                    # Add or update footnote
                    footnotes_dict[footnote_num] = footnote_text
    
    # Convert dict to sorted list
    for num in sorted(footnotes_dict.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        footnotes.append({
            'number': num,
            'text': footnotes_dict[num]
        })
    
    return footnotes

def check_if_repealed(soup):
    """Check if the act is repealed"""
    repealed_section = soup.find('section', class_='bt-act-repealed')
    if repealed_section:
        repealed_text = clean_text(repealed_section.get_text())
        return repealed_text
    return None

def generate_mdx(html_path):
    """Generate clean MDX from HTML
    
    Args:
        html_path: Path to input HTML file
    
    Returns:
        String containing complete MDX content
    """
    # Read HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Use html.parser instead of lxml to handle malformed HTML (divs inside p tags)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract all components
    act_id = extract_act_id(os.path.basename(html_path))
    metadata = extract_metadata(soup)
    
    # Create dictionary to collect inline footnotes
    inline_footnotes = {}
    
    # Extract preamble (may contain footnotes)
    preamble = extract_preamble(soup, inline_footnotes)
    
    # Extract sections (may contain footnotes)
    sections = extract_sections(soup, inline_footnotes)
    
    # Extract and merge all footnotes
    footnotes = extract_footnotes(soup, inline_footnotes)
    
    repealed_notice = check_if_repealed(soup)
    
    # Build MDX content
    mdx = []
    
    # Frontmatter
    mdx.append("---")
    mdx.append(f"title: {metadata['title']}")
    mdx.append(f"sidebarTitle: {metadata['sidebarTitle']}")
    if metadata['description']:
        mdx.append(f"description: {metadata['description']}")
    mdx.append("---")
    mdx.append("")
    
    # Date
    if metadata['date']:
        mdx.append(f"**Date of Publication:** {metadata['date']}")
        mdx.append("")
    
    # Repealed notice if present
    if repealed_notice:
        mdx.append(f"**REPEALED:** {repealed_notice}")
        mdx.append("")
    
    # Preamble
    if preamble:
        mdx.append("## Preamble")
        mdx.append("")
        mdx.append(preamble)
        mdx.append("")
    
    # Sections
    if sections:
        mdx.append("## Sections/Articles")
        mdx.append("")
        
        for section in sections:
            if section['type'] == 'part':
                mdx.append(f"### {section['content']}")
                mdx.append("")
            elif section['type'] == 'section':
                if section['heading']:
                    mdx.append(f"### {section['heading']}")
                    mdx.append("")
                mdx.append(section['content'])
                mdx.append("")
    
    # Footnotes
    if footnotes:
        mdx.append("## Footnotes")
        mdx.append("")
        for footnote in footnotes:
            # Add anchor ID for linking from inline references
            mdx.append(f'<span id="footnote-{footnote["number"]}"></span>')
            mdx.append(f"- ###### {footnote['number']}")
            mdx.append("")
            mdx.append(f"  {footnote['text']}")
            mdx.append("")
    
    # Note with original link
    mdx.append("<Note>")
    mdx.append(f"  Click [here](http://bdlaws.minlaw.gov.bd/act-details-{act_id}.html) to see the original act on the Bangladesh Legal Database.")
    mdx.append("</Note>")
    
    return '\n'.join(mdx)

def find_all_html_files(input_dir):
    """Find all HTML files in volume directories
    
    Args:
        input_dir: Base directory containing volume-* subdirectories
    
    Returns:
        List of Path objects for all HTML files
    """
    html_files = []
    input_path = Path(input_dir)
    
    # Find all volume directories
    volume_dirs = sorted(input_path.glob("volume-*"))
    
    for volume_dir in volume_dirs:
        # Find all act HTML files in this volume
        act_files = sorted(volume_dir.glob("act-*.html"))
        html_files.extend(act_files)
    
    return html_files

def convert_all_laws(input_dir, output_dir, verbose=False, skip_existing=False):
    """Convert all HTML law files to MDX format
    
    Args:
        input_dir: Directory containing volume-*/act-*.html files
        output_dir: Directory to save converted MDX files
        verbose: Print detailed progress messages
        skip_existing: Skip files that already exist in output directory
    
    Returns:
        Tuple of (success_count, error_count, skipped_count)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all HTML files
    html_files = find_all_html_files(input_dir)
    
    if not html_files:
        print(f"No HTML files found in {input_dir}")
        return 0, 0, 0
    
    print(f"Found {len(html_files)} HTML files to convert")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, html_file in enumerate(html_files, 1):
        try:
            # Extract act ID
            act_id = extract_act_id(html_file.name)
            if not act_id:
                if verbose:
                    print(f"[{i}/{len(html_files)}] SKIP: Could not extract act ID from {html_file.name}")
                skipped_count += 1
                continue
            
            # Check if output file already exists
            output_file = output_path / f"act-{act_id}.mdx"
            if skip_existing and output_file.exists():
                if verbose:
                    print(f"[{i}/{len(html_files)}] SKIP: {output_file.name} already exists")
                skipped_count += 1
                continue
            
            # Convert to MDX
            mdx_content = generate_mdx(html_file)
            
            # Save output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(mdx_content)
            
            success_count += 1
            
            # Print progress
            if verbose or (i % 100 == 0):
                print(f"[{i}/{len(html_files)}] OK - Converted: act-{act_id}.mdx")
            
        except Exception as e:
            error_count += 1
            print(f"[{i}/{len(html_files)}] ERROR converting {html_file.name}: {e}")
    
    return success_count, error_count, skipped_count

def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Convert Bangladesh law HTML files to MDX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all laws with default paths
  python convert_all_laws.py
  
  # Convert with verbose output
  python convert_all_laws.py --verbose
  
  # Skip already converted files
  python convert_all_laws.py --skip-existing
  
  # Specify custom input/output directories
  python convert_all_laws.py --input files/htmls/laws --output files/mdx_output
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        default='files/htmls/laws',
        help='Input directory containing volume-*/act-*.html files (default: files/htmls/laws)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='files/md_output',
        help='Output directory for MDX files (default: files/md_output)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress for each file'
    )
    
    parser.add_argument(
        '--skip-existing', '-s',
        action='store_true',
        help='Skip files that already exist in output directory'
    )
    
    args = parser.parse_args()
    
    # Run conversion
    print("=" * 60)
    print("Bangladesh Laws HTML to MDX Converter")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = datetime.now()
    
    success, errors, skipped = convert_all_laws(
        args.input,
        args.output,
        verbose=args.verbose,
        skip_existing=args.skip_existing
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Print summary
    print()
    print("=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Successfully converted: {success} files")
    print(f"Errors encountered:    {errors} files")
    print(f"Skipped:               {skipped} files")
    print(f"Total time:            {duration:.2f} seconds")
    print(f"Completed at:          {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
