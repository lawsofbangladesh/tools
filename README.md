# Bangladesh Laws HTML to MDX Converter

This tool converts Bangladesh law HTML files from the Bangladesh Legal Database (bdlaws.minlaw.gov.bd) to clean MDX format suitable for documentation websites.

## Features

- ✅ Extracts metadata (title, description, publication date)
- ✅ Preserves preamble text (Bengali and English)
- ✅ Converts sections with proper heading hierarchy
- ✅ Extracts and links footnotes (clickable superscript references)
- ✅ Converts internal act references to markdown links
- ✅ Handles both Bengali (বাংলা) and English laws
- ✅ Supports repealed act notices
- ✅ Uses html.parser to handle malformed HTML
- ✅ Updates volume and year index files automatically

## Requirements

```bash
pip install beautifulsoup4
```

## Quick Start

### 1. Convert All Laws

```bash
# Convert all laws with default paths
python convert_all_laws.py

# Convert with verbose output (shows progress for each file)
python convert_all_laws.py --verbose

# Skip already converted files
python convert_all_laws.py --skip-existing
```

### 2. Update Index Files

After converting laws or when CSV data is updated, regenerate index files:

```bash
# Update all volume and year index files
python update_indexes.py

# With verbose output
python update_indexes.py --verbose
```

This will create/update:
- `files/index/volume/volume-1.mdx` through `volume-56.mdx` - Act listings per volume
- `files/index/year/1799.mdx` through `2025.mdx` - Acts grouped by publication year
- `files/index/index.mdx` - Main index with all volumes

### Custom Input/Output Directories

**For Law Conversion:**
```bash
# Specify custom paths
python convert_all_laws.py --input files/htmls/laws --output files/mdx_output
```

**For Index Updates:**
```bash
# Specify custom CSV and output paths
python update_indexes.py --csv files/volumes/csv --output files/index
```

### Command-Line Options

**convert_all_laws.py:**
```
--input, -i      Input directory containing volume-*/act-*.html files
                 Default: files/htmls/laws

--output, -o     Output directory for MDX files
                 Default: files/md_output

--verbose, -v    Print detailed progress for each file

--skip-existing  Skip files that already exist in output directory
```

**update_indexes.py:**
```
--csv, -c        Directory containing volume CSV files
                 Default: files/volumes/csv

--output, -o     Output directory for index MDX files
                 Default: files/index

--verbose, -v    Print detailed progress for each file
```

## Directory Structure

```
tools/
├── convert_all_laws.py          # Main law converter script
├── update_indexes.py             # Index file updater script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── PROJECT_STRUCTURE.md          # Detailed project documentation
├── files/
│   ├── htmls/
│   │   └── laws/
│   │       ├── volume-1/
│   │       │   ├── act-1.html
│   │       │   ├── act-2.html
│   │       │   └── ...
│   │       ├── volume-2/
│   │       └── ...
│   ├── volumes/
│   │   └── csv/                  # Volume metadata CSV files
│   │       ├── volume-1.csv
│   │       ├── volume-2.csv
│   │       └── ...
│   ├── md_output/                # Converted MDX files (generated)
│   │   ├── act-1.mdx
│   │   ├── act-2.mdx
│   │   └── ...
│   └── index/                    # Index files (generated)
│       ├── index.mdx             # Main index
│       ├── volume/               # Volume index files
│       │   ├── volume-1.mdx
│       │   ├── volume-2.mdx
│       │   └── ...
│       └── year/                 # Year index files
│           ├── 1799.mdx
│           ├── 2025.mdx
│           └── ...
├── lawsmd/                       # Reference MDX files (1500+ examples)
└── scripts/                      # Utility scripts
```

## Output Format

Each converted MDX file contains:

1. **Frontmatter** (YAML metadata):
   ```yaml
   ---
   title: Act Title
   sidebarTitle: ( Act Number )
   description: Act description or purpose
   ---
   ```

2. **Publication Date**:
   ```markdown
   **Date of Publication:** [ Date ]
   ```

3. **Preamble** (if present):
   ```markdown
   ## Preamble
   
   WHEREAS... It is hereby enacted as follows:-
   ```
   Or in Bengali:
   ```markdown
   ## Preamble
   
   যেহেতু... সেহেতু এতদ্দ্বারা নিম্নরূপ আইন করা হইল :-
   ```

4. **Sections/Articles**:
   ```markdown
   ## Sections/Articles
   
   ### Section Title
   
   Section content with [internal links](/laws/act-123) and footnotes<sup>[[1]](#footnote-1)</sup>
   ```

5. **Footnotes** (clickable links):
   ```markdown
   ## Footnotes
   
   <span id="footnote-1"></span>
   - ###### 1
   
     Footnote text with [act references](/laws/act-123)
   ```

6. **Original Source Link**:
   ```markdown
   <Note>
     Click [here](http://bdlaws.minlaw.gov.bd/act-details-123.html) to see the original act.
   </Note>
   ```

## Technical Details

### Preamble Extraction

The converter handles two preamble structures:

- **English Laws**: Extracts text from `<p>` tags starting with "WHEREAS" and ending with "It is hereby enacted" or "NOW, THEREFORE"
- **Bengali Laws**: Extracts text between `<div class="clbr">` tags, starting with "যেহেতু" and ending with "সেহেতু"

### Footnote Processing

Footnotes are extracted from two sources:

1. **Inline footnotes**: From `<span class="footnote" title="[text]">` tags in content
2. **Bottom footnotes**: From `<div class="footnoteListAll">` section

Both are merged and numbered sequentially. Inline references use clickable superscript links:
- Reference: `<sup>[[1]](#footnote-1)</sup>`
- Definition: `<span id="footnote-1"></span>`

### Internal Links

Act references are automatically converted to markdown links:
- Input: `<a href="/act-123" title="Act Title">Act Name</a>`
- Output: `[Act Name](/laws/act-123 "Act Title")`

## Conversion Statistics

Based on test conversions:
- Average conversion time: ~0.5-1 second per file
- Successfully handles 1500+ law files
- Supports both Bengali and English content
- Preserves all metadata, sections, and footnotes

## Examples

### Example 1: Convert All Laws

```bash
python convert_all_laws.py --verbose
```

Output:
```
============================================================
Bangladesh Laws HTML to MDX Converter
============================================================
Started at: 2025-11-11 10:30:00

Found 1523 HTML files to convert
Output directory: files/md_output
------------------------------------------------------------
[1/1523] ✓ Converted: act-1.mdx
[2/1523] ✓ Converted: act-2.mdx
...
[1523/1523] ✓ Converted: act-1871.mdx

============================================================
Conversion Summary
============================================================
Successfully converted: 1523 files
Errors encountered:    0 files
Skipped:               0 files
Total time:            762.45 seconds
Completed at:          2025-11-11 10:42:42
============================================================
```

### Example 2: Resume Conversion (Skip Existing)

```bash
python convert_all_laws.py --skip-existing --verbose
```

This is useful if the conversion was interrupted and you want to continue without reconverting files.

## Troubleshooting

### Missing Dependencies

If you get `ModuleNotFoundError: No module named 'bs4'`:
```bash
pip install beautifulsoup4
```

### No HTML Files Found

Ensure your input directory structure matches:
```
files/htmls/laws/
  volume-1/
    act-1.html
    act-2.html
  volume-2/
    ...
```

### Encoding Issues

The script uses UTF-8 encoding by default. If you encounter encoding errors, ensure your HTML files are UTF-8 encoded.

## Contributing

This is part of the Laws of Bangladesh project to make Bangladesh laws accessible in modern formats.

## License

This tool is provided as-is for converting publicly available Bangladesh legal documents.

## Author

Laws of Bangladesh,  [Sayed](https://sayed.page)
November 2025
