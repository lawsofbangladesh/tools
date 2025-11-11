"""
Complete HTML to Clean MDX Converter
Converts Bangladesh law HTML files to clean MDX format matching reference files
"""
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def extract_act_id(html_path):
    """Extract act ID from filename"""
    filename = Path(html_path).stem
    # Extract number from act-123.html
    match = re.search(r'act-(\d+)', filename)
    if match:
        return match.group(1)
    return None

def extract_metadata(soup):
    """Extract metadata for frontmatter"""
    metadata = {
        'title': '',
        'sidebarTitle': '',
        'description': '',
        'date': ''
    }
    
    # Extract title from h3
    h3 = soup.find('h3')
    if h3:
        metadata['title'] = h3.get_text(strip=True)
    
    # Extract act number from h4 - clean up whitespace
    h4 = soup.find('h4')
    if h4:
        # Get text and clean up excessive whitespace
        text = h4.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        metadata['sidebarTitle'] = f"( {text} )"
    
    # Extract date
    date_p = soup.find('p', class_='publish-date')
    if date_p:
        metadata['date'] = date_p.get_text(strip=True)
    
    # Extract description from act-role-style div
    desc_div = soup.find('div', class_='act-role-style')
    if desc_div:
        # Remove <strong> tags but keep content
        for strong in desc_div.find_all('strong'):
            strong.unwrap()
        metadata['description'] = desc_div.get_text(strip=True)
    
    return metadata

def extract_preamble(soup):
    """Extract preamble text"""
    # Find the preamble div - it's in lineremove but NOT in lineremoves
    for div in soup.find_all('div', class_='lineremove'):
        # Skip if it has lineremoves class (sections)
        if 'lineremoves' in div.get('class', []):
            continue
        
        # This should be the preamble
        # Get only the paragraph text, not headers
        paragraphs = div.find_all('p')
        if paragraphs:
            text = ' '.join(p.get_text(separator=' ', strip=True) for p in paragraphs)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            return text
    
    return ''

def clean_markdown_content(md_content, act_id):
    """Clean up markdown content to match reference format"""
    
    # Remove image tags
    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)
    
    # Remove copyright section
    md_content = re.sub(r'Copyright\s*©.*?Ministry of Law.*?$', '', md_content, flags=re.DOTALL | re.MULTILINE)
    
    # Remove hr tags
    md_content = re.sub(r'^---+$', '', md_content, flags=re.MULTILINE)
    
    # Fix footnote markers: <1> to [1]
    md_content = re.sub(r'<(\d+)>', r'[\1]', md_content)
    
    # Fix asterisks in brackets: [* * *] to [\* \* \*]
    md_content = re.sub(r'\[\*\s*\*\s*\*\]', r'[\\* \\* \\*]', md_content)
    
    # Fix internal links: /act-123.html to /laws/act-123
    def fix_link(match):
        link_text = match.group(1)
        link_href = match.group(2)
        link_title = match.group(3) if match.lastindex >= 3 else ''
        
        # Convert /act-123.html to /laws/act-123
        if '/act-' in link_href and '.html' in link_href:
            link_href = link_href.replace('.html', '').replace('/act-', '/laws/act-')
        
        if link_title:
            return f'[{link_text}]({link_href} "{link_title}")'
        else:
            return f'[{link_text}]({link_href})'
    
    md_content = re.sub(r'\[([^\]]+)\]\(([^)]+?)(?:\s+"([^"]+)")?\)', fix_link, md_content)
    
    # Remove extra blank lines (more than 2 consecutive)
    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    
    return md_content.strip()

def extract_sections_and_footnotes(soup):
    """Extract sections and footnotes separately"""
    sections = []
    footnotes = []
    
    # Extract sections from lineremoves divs
    for lineremove in soup.find_all('div', class_='lineremoves'):
        # Skip if it's marked as repealed
        if 'repealed' in lineremove.get('class', []):
            continue
        
        # Get section heading
        heading_div = lineremove.find('div', class_='txt-head')
        heading = heading_div.get_text(strip=True) if heading_div else ''
        
        # Get section content
        content_div = lineremove.find('div', class_='txt-details')
        if content_div:
            # Convert to markdown
            content_md = md(str(content_div), 
                          heading_style="ATX",
                          bullets="-",
                          strip=['script', 'style', 'div'],
                          escape_asterisks=False,
                          escape_underscores=False)
            
            # Clean up
            content_md = content_md.strip()
            
            if heading or content_md:
                sections.append({
                    'heading': heading,
                    'content': content_md
                })
    
    # Extract footnotes
    footnote_list = soup.find('div', class_='footnoteListAll')
    if footnote_list:
        for footnote_item in footnote_list.find_all('li', class_='footnoteList'):
            # Get footnote number from h6
            h6 = footnote_item.find('h6')
            footnote_num = ''
            if h6:
                sup = h6.find('sup')
                if sup:
                    footnote_num = sup.get_text(strip=True)
            
            # Get footnote text
            footnote_text = footnote_item.get_text(strip=True)
            # Remove the number from the beginning
            footnote_text = re.sub(r'^\d+\s*', '', footnote_text)
            
            if footnote_num and footnote_text:
                footnotes.append({
                    'number': footnote_num,
                    'text': footnote_text
                })
    
    return sections, footnotes

def generate_clean_mdx(metadata, preamble, sections, footnotes, act_id):
    """Generate final clean MDX content"""
    mdx = []
    
    # Frontmatter
    mdx.append('---')
    mdx.append(f'title: "{metadata["title"]}"')
    mdx.append(f'sidebarTitle: "{metadata["sidebarTitle"]}"')
    mdx.append(f'description: "{metadata["description"]}"')
    mdx.append('---')
    mdx.append('')
    
    # Date
    if metadata['date']:
        mdx.append(f'**Date of Publication:** {metadata["date"]}')
        mdx.append('')
    
    # Preamble
    if preamble:
        mdx.append('## Preamble')
        mdx.append('')
        mdx.append(preamble)
        mdx.append('')
    
    # Sections
    mdx.append('## Sections/Articles')
    mdx.append('')
    
    for section in sections:
        if section['heading']:
            mdx.append(f"### {section['heading']}")
            mdx.append('')
        if section['content']:
            mdx.append(section['content'])
            mdx.append('')
    
    # Footnotes
    if footnotes:
        mdx.append('## Footnotes')
        mdx.append('')
        for footnote in footnotes:
            mdx.append(f"- ###### {footnote['number']}")
            mdx.append('')
            mdx.append(f"  {footnote['text']}")
            mdx.append('')
    
    # Note with link
    mdx.append('<Note>')
    mdx.append(f'  Click [here](http://bdlaws.minlaw.gov.bd/act-details-{act_id}.html) to see the original act on the Bangladesh Legal Database.')
    mdx.append('</Note>')
    
    return '\n'.join(mdx)

def convert_html_to_clean_mdx(html_path, output_path):
    """Main conversion function"""
    print(f"\nProcessing: {html_path}")
    
    # Extract act ID
    act_id = extract_act_id(html_path)
    if not act_id:
        print(f"  ✗ Could not extract act ID")
        return False
    
    # Read HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Extract metadata
    metadata = extract_metadata(soup)
    
    # Extract preamble
    preamble = extract_preamble(soup)
    
    # Extract sections and footnotes
    sections, footnotes = extract_sections_and_footnotes(soup)
    
    # Generate clean MDX
    clean_mdx = generate_clean_mdx(metadata, preamble, sections, footnotes, act_id)
    
    # Clean up markdown content
    clean_mdx = clean_markdown_content(clean_mdx, act_id)
    
    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(clean_mdx)
    
    print(f"  ✓ Converted to: {output_path}")
    return True

def main():
    """Convert test files"""
    base_dir = Path(__file__).parent.parent
    
    # Test files
    test_files = [
        ('files/htmls/laws/volume-14/act-356.html', 'files/md_clean/act-356.mdx'),
        ('files/htmls/laws/volume-14/act-365.html', 'files/md_clean/act-365.mdx'),
        ('files/htmls/laws/volume-26/act-678.html', 'files/md_clean/act-678.mdx'),
    ]
    
    print("=" * 80)
    print("HTML to Clean MDX Converter")
    print("=" * 80)
    
    for html_file, output_file in test_files:
        html_path = base_dir / html_file
        output_path = base_dir / output_file
        
        if not html_path.exists():
            print(f"\n✗ HTML file not found: {html_path}")
            continue
        
        convert_html_to_clean_mdx(html_path, output_path)
    
    print("\n" + "=" * 80)
    print("Conversion completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
