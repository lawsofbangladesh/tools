#!/usr/bin/env python3
"""
HTML to Markdown Converter for Bangladesh Laws
Carefully converts HTML law files to MDX format with proper structure.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_act_number_from_h4(h4_tag):
    """Extract act number from h4 tag"""
    if not h4_tag:
        return ""
    text = h4_tag.get_text(strip=True)
    # Extract the act number portion
    # Example: "( ACT NO. VII OF 1870 )" or "( ২০২৩ সনের ৪৯ নং আইন )"
    return clean_text(text)


def extract_metadata(soup):
    """Extract title, act number, and publication date from HTML"""
    metadata = {
        'title': '',
        'sidebarTitle': '',
        'description': '',
        'date': ''
    }
    
    # Extract title from h3
    title_tag = soup.find('h3')
    if title_tag:
        # Remove footnote spans
        for footnote in title_tag.find_all('span', class_='footnote'):
            footnote.decompose()
        metadata['title'] = clean_text(title_tag.get_text())
    
    # Extract act number from h4
    h4_tag = soup.find('h4')
    if h4_tag:
        metadata['sidebarTitle'] = extract_act_number_from_h4(h4_tag)
    
    # Extract publication date
    date_tag = soup.find('p', class_='publish-date')
    if date_tag:
        metadata['date'] = clean_text(date_tag.get_text())
    
    # Extract description from act-role-style div (PRESERVE footnote markers like 1♣)
    desc_tag = soup.find('div', class_='act-role-style')
    if desc_tag:
        # First, remove any links - description should not have markdown links
        for a_tag in desc_tag.find_all('a'):
            # Replace link with just its text
            a_tag.replace_with(a_tag.get_text())
        
        # Get raw text to preserve special characters
        desc_text = desc_tag.get_text()
        # Collapse whitespace but preserve footnote markers
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        # Remove extra spaces around numbers before ♣
        desc_text = re.sub(r'(\d)\s+♣', r'\1♣', desc_text)
        # Remove period and space before footnote number
        desc_text = re.sub(r'\.\s+(\d♣)', r'.\1', desc_text)
        metadata['description'] = desc_text
    
    return metadata


def extract_preamble(soup):
    """Extract preamble text"""
    preamble_text = ""
    
    # Find the preamble section in row structure (for acts with labeled preamble)
    for row in soup.find_all('div', class_='row'):
        col_md_2 = row.find('div', class_='col-md-2')
        col_md_10 = row.find('div', class_='col-md-10')
        
        if col_md_2 and col_md_10:
            label = clean_text(col_md_2.get_text())
            if label.lower() == 'preamble' or 'preamble' in label.lower():
                # Get the preamble text - collapse to single line
                content_text = col_md_10.get_text()
                # Collapse all whitespace to single spaces
                content_text = re.sub(r'\s+', ' ', content_text)
                content_text = content_text.strip()
                preamble_text = content_text
                break
    
    # Also check in div.lineremove for preambles that start with WHEREAS or যেহেতু
    if not preamble_text:
        # Look for div with class containing 'lineremove'
        for div in soup.find_all('div', class_=re.compile(r'lineremove')):
            # Get all text from this div
            div_text = div.get_text()
            # Check if it starts with preamble indicators
            div_text_stripped = div_text.strip()
            if div_text_stripped.startswith('WHEREAS') or div_text_stripped.startswith('যেহেতু'):
                # This is a preamble - extract all text
                # Collapse all whitespace
                preamble_text = re.sub(r'\s+', ' ', div_text)
                preamble_text = preamble_text.strip()
                break
    
    return preamble_text


def convert_internal_links(text, soup):
    """Convert internal act links to markdown format /laws/act-{id}"""
    # Find all <a> tags with href containing /act-
    links = soup.find_all('a', href=re.compile(r'/act-\d+\.html'))
    
    for link in links:
        href = link.get('href', '')
        title = link.get('title', '')
        link_text = clean_text(link.get_text())
        
        # Skip if no link text
        if not link_text:
            continue
        
        # Extract act ID from href
        match = re.search(r'/act-(\d+)\.html', href)
        if match:
            act_id = match.group(1)
            # Create markdown link - NO SPACE between closing bracket and parenthesis
            if title:
                markdown_link = f'[{link_text}](/laws/act-{act_id} "{title}")'
            else:
                markdown_link = f'[{link_text}](/laws/act-{act_id})'
            
            # Replace in the original HTML to preserve structure
            link.replace_with(markdown_link)
    
    return soup


def process_footnotes(soup):
    """Convert footnotes to markdown references"""
    footnotes = []
    footnote_map = {}
    
    # Find all footnote spans
    for footnote_span in soup.find_all('span', class_='footnote'):
        title = footnote_span.get('title', '')
        # Find the footnote number
        sup_tag = footnote_span.find('sup', class_='en')
        if sup_tag:
            a_tag = sup_tag.find('a')
            if a_tag:
                footnote_num = clean_text(a_tag.get_text())
                if footnote_num and title:
                    # Store footnote
                    footnote_map[footnote_num] = title
                    # Replace with markdown reference
                    footnote_span.replace_with(f'[{footnote_num}]({a_tag.get("href", "1")})')
    
    # Extract footnotes from the footnoteListAll section
    footnote_list = soup.find('div', class_='footnoteListAll')
    if footnote_list:
        for li in footnote_list.find_all('li', class_='footnoteList'):
            h6 = li.find('h6')
            if h6:
                # Get footnote number
                sup_tag = h6.find('sup')
                if sup_tag:
                    num = clean_text(sup_tag.get_text())
                    # Get footnote text
                    h6.decompose()  # Remove h6 to get remaining text
                    footnote_text = clean_text(li.get_text())
                    if num and footnote_text:
                        footnotes.append((num, footnote_text))
    
    return footnotes


def extract_sections(soup):
    """Extract sections and their content"""
    sections = []
    current_chapter = None
    
    # Process sections
    for row in soup.find_all('div', class_='lineremoves'):
        # Check for chapter group
        chapter_group = row.find('div', class_='act-chapter-group')
        if chapter_group:
            chapter_no = chapter_group.find('p', class_='act-chapter-no')
            chapter_name = chapter_group.find('p', class_='act-chapter-name')
            if chapter_no and chapter_name:
                chapter_text = clean_text(chapter_no.get_text())
                chapter_desc = clean_text(chapter_name.get_text())
                current_chapter = {
                    'type': 'chapter',
                    'number': chapter_text,
                    'name': chapter_desc
                }
                sections.append(current_chapter)
        
        # Check for section heading and content
        heading_div = row.find('div', class_='txt-head')
        content_div = row.find('div', class_='txt-details')
        
        if heading_div and content_div:
            heading = clean_text(heading_div.get_text())
            
            # Skip empty headings
            if not heading:
                continue
            
            # Process footnotes inline - do this BEFORE getting text
            for footnote in content_div.find_all('span', class_='footnote'):
                title = footnote.get('title', '')
                sup_tag = footnote.find('sup', class_='en')
                if sup_tag:
                    a_tag = sup_tag.find('a')
                    if a_tag:
                        num = clean_text(a_tag.get_text())
                        href = a_tag.get('href', '1')
                        # NO SPACE between footnote ref and following bracket
                        footnote.replace_with(f'[{num}]({href})')
            
            # Get the entire content as one block
            content_text = content_div.get_text()
            
            # Clean up whitespace - collapse ALL whitespace to single spaces
            content_text = re.sub(r'\s+', ' ', content_text)
            # Remove space before closing punctuation
            content_text = re.sub(r' +\)', ')', content_text)
            content_text = re.sub(r' +,', ',', content_text)
            content_text = re.sub(r' +;', ';', content_text)
            # Remove space after opening punctuation
            content_text = re.sub(r'\( +', '(', content_text)
            # Remove space before dash when after comma/colon
            content_text = re.sub(r'(,|:) +-', r'\1-', content_text)
            # Remove space after ")." before "(" (for sub-sections like ").(2)")
            content_text = re.sub(r'\)\. +\(', ').(', content_text)
            # Remove space after comma before opening parenthesis  
            content_text = re.sub(r', +\(', ',(', content_text)
            # No space between brackets
            content_text = re.sub(r'\] +\[', '][', content_text)
            content_text = re.sub(r'\) +\[', ')[', content_text)  # NO space between )[ 
            # Escape asterisks in [* * *] patterns
            content_text = re.sub(r'\[\*\s\*\s\*\]', r'[\* \* \*]', content_text)
            content_text = content_text.strip()
            
            # Create section - content is ONE LINE
            if content_text:
                sections.append({
                    'type': 'section',
                    'heading': heading,
                    'content': content_text
                })
    
    return sections


def generate_markdown(metadata, preamble, sections, footnotes, act_id):
    """Generate final markdown content"""
    lines = []
    
    # Frontmatter
    lines.append('---')
    lines.append(f'title: "{metadata["title"]}"')
    lines.append(f'sidebarTitle: "{metadata["sidebarTitle"]}"')
    lines.append(f'description: "{metadata["description"]}"')
    lines.append('---')
    lines.append('')
    
    # Publication date
    if metadata['date']:
        lines.append(f'**Date of Publication:** {metadata["date"]}')
        lines.append('')
    
    # Preamble
    if preamble:
        lines.append('## Preamble')
        lines.append('')
        lines.append(preamble)
        lines.append('')
    
    # Sections
    if sections:
        lines.append('## Sections/Articles')
        lines.append('')
        
        for section in sections:
            if section['type'] == 'chapter':
                lines.append(f'### {section["number"]}')
                lines.append('')
                lines.append(f'**{section["name"]}**')
                lines.append('')
            elif section['type'] == 'section':
                heading = section['heading']
                # Don't add ### for empty or very short headings
                if heading and heading not in ['', ' ']:
                    lines.append(f'### {heading}')
                    lines.append('')
                lines.append(section['content'])
                lines.append('')
    
    # Footnotes
    if footnotes:
        lines.append('## Footnotes')
        lines.append('')
        for num, text in footnotes:
            lines.append(f'- ###### {num}')
            lines.append('')
            # Escape asterisks in footnote text
            text = text.replace('* * *', r'\* \* \*')
            lines.append(f'  {text}')
            lines.append('')
    
    # Footer note with actual act_id
    lines.append('<Note>')
    lines.append(f'  Click [here](http://bdlaws.minlaw.gov.bd/act-details-{act_id}.html) to see the original act on the Bangladesh Legal Database.')
    lines.append('</Note>')
    
    return '\n'.join(lines)


def convert_html_to_markdown(html_file, output_file):
    """Convert a single HTML file to markdown"""
    # Read HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Extract act ID from filename
    act_id = Path(html_file).stem.replace('act-', '')
    
    # Convert internal links in the entire soup first
    soup = convert_internal_links(None, soup)
    
    # Extract components
    metadata = extract_metadata(soup)
    preamble = extract_preamble(soup)
    footnotes = process_footnotes(soup)
    sections = extract_sections(soup)
    
    # Generate markdown with act_id
    markdown = generate_markdown(metadata, preamble, sections, footnotes, act_id)
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    return True


def main():
    """Main conversion function"""
    # Set up paths
    base_dir = Path(__file__).parent.parent
    html_dir = base_dir / 'files' / 'htmls' / 'laws'
    output_dir = base_dir / 'files' / 'md'
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test on specific acts
    test_acts = ['21', '1468', '1501']
    
    print("=" * 70)
    print("HTML to Markdown Converter (COMPLETE REWRITE)")
    print("=" * 70)
    
    for act_id in test_acts:
        # Find the HTML file
        html_file = None
        for volume_dir in html_dir.iterdir():
            if volume_dir.is_dir():
                test_file = volume_dir / f'act-{act_id}.html'
                if test_file.exists():
                    html_file = test_file
                    break
        
        if not html_file:
            print(f"✗ Act {act_id}: HTML file not found")
            continue
        
        # Convert
        output_file = output_dir / f'act-{act_id}.mdx'
        try:
            print(f"Converting act-{act_id}...")
            convert_html_to_markdown(html_file, output_file)
            print(f"  ✓ Saved to: {output_file}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("=" * 70)
    print("Conversion completed!")
    print(f"Output directory: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
