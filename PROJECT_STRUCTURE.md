# Project Structure

## Bangladesh Laws HTML to MDX Converter

### Main Files
```
tools/
├── convert_all_laws.py          # Production converter (MAIN SCRIPT)
├── README.md                     # Documentation and usage guide
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore patterns
│
├── files/                        # Data directory
│   ├── htmls/                   # Input HTML files
│   │   ├── laws/                # Law HTML files by volume
│   │   │   ├── volume-1/
│   │   │   │   ├── act-1.html
│   │   │   │   └── ...
│   │   │   ├── volume-2/
│   │   │   └── ...
│   │   └── volumes/             # Volume list pages
│   │
│   ├── volumes/                 # Volume metadata
│   │   ├── csv/                 # Act listings per volume (CSV)
│   │   └── volume_list.json     # Master volume list
│   │
│   └── md_output/               # Converted MDX files (OUTPUT)
│       ├── act-1.mdx
│       ├── act-2.mdx
│       └── ...
│
├── lawsmd/                      # Reference MDX files (1500+ examples)
│   ├── act-1.mdx
│   ├── act-2.mdx
│   └── ...
│
└── scripts/                     # Utility scripts
    ├── fetch_volume_list.py          # Download volume list
    ├── extract_acts_from_volumes.py  # Extract act metadata
    ├── download_act_htmls.py         # Download all HTML files
    ├── convert_html_to_markdown.py   # OLD - deprecated
    └── html_to_clean_mdx.py          # OLD - deprecated
```

## Workflow

### 1. Data Collection (One-time setup)
```bash
# Step 1: Fetch list of all law volumes
cd scripts
python fetch_volume_list.py

# Step 2: Extract act metadata from each volume page
python extract_acts_from_volumes.py

# Step 3: Download all HTML files
python download_act_htmls.py
```

### 2. Conversion (Main process)
```bash
# Convert all laws to MDX
python convert_all_laws.py

# With options
python convert_all_laws.py --verbose --skip-existing
python convert_all_laws.py --output custom/path
```

## File Descriptions

### Main Scripts

**convert_all_laws.py** - Production converter
- Converts all Bangladesh law HTML files to MDX format
- Features: Preamble extraction, footnote linking, internal references
- Handles both Bengali and English laws
- Command-line interface with options

### Utility Scripts (scripts/)

**fetch_volume_list.py**
- Downloads the master list of law volumes from bdlaws.minlaw.gov.bd
- Saves to files/volumes/volume_list.json
- One-time data collection

**extract_acts_from_volumes.py**
- Visits each volume page and extracts act metadata
- Creates CSV files with act listings per volume
- Saves to files/volumes/csv/

**download_act_htmls.py**
- Downloads individual HTML files for each act
- Uses parallel processing for speed
- Organizes by volume: files/htmls/laws/volume-*/act-*.html

**convert_html_to_markdown.py** (DEPRECATED)
- Old conversion script - not used
- Keep for reference only

**html_to_clean_mdx.py** (DEPRECATED)
- Old conversion script - not used
- Keep for reference only

### Reference Files

**lawsmd/** - Contains 1500+ correctly formatted MDX examples
- Used as reference for conversion output format
- Hand-curated and verified files

## Important Directories

### Input Data
- `files/htmls/laws/volume-*/` - HTML source files (1509 files)
- `files/volumes/` - Volume and act metadata

### Output Data
- `files/md_output/` - Converted MDX files (gitignored)

### Reference Data
- `lawsmd/` - Reference MDX files for comparison

## Dependencies

```
beautifulsoup4>=4.12.0
requests (for download scripts)
```

Install:
```bash
pip install -r requirements.txt
```

## Git Strategy

### Tracked Files
- Source scripts (*.py)
- Documentation (README.md)
- Configuration (requirements.txt, .gitignore)
- Input HTML files (files/htmls/)
- Volume metadata (files/volumes/)
- Reference MDX (lawsmd/)

### Ignored Files (in .gitignore)
- Python cache (__pycache__/, *.pyc)
- Output MDX files (files/md_output/)
- Test directories (files/md_test*)
- IDE files (.vscode/, .idea/)

## Quick Start

### For First Time Setup:
```bash
# 1. Clone repository
git clone <repository-url>
cd tools

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download all HTML files (if not present)
cd scripts
python fetch_volume_list.py
python extract_acts_from_volumes.py
python download_act_htmls.py
cd ..

# 4. Convert to MDX
python convert_all_laws.py --verbose
```

### For Conversion Only (if HTML files exist):
```bash
python convert_all_laws.py --verbose
```

## Notes

1. **HTML Files**: The HTML source files are already downloaded and stored in `files/htmls/laws/`
2. **Reference Files**: The `lawsmd/` directory contains correctly formatted examples
3. **Output**: Converted files go to `files/md_output/` by default
4. **Encoding**: All files use UTF-8 encoding
5. **Parser**: Uses html.parser (not lxml) to handle malformed HTML correctly
6. **Performance**: Converts ~1500 files in approximately 12-15 minutes

## Troubleshooting

### No HTML files found
- Check that `files/htmls/laws/volume-*/` directories exist
- Run download scripts if needed

### Encoding errors
- Ensure Python uses UTF-8: `python -X utf8 convert_all_laws.py`
- Check HTML files are UTF-8 encoded

### Missing dependencies
```bash
pip install beautifulsoup4
```

### Conversion errors
- Check error messages in output
- Verify HTML file structure matches expected format
- Compare with reference files in lawsmd/

## Contact

Laws of Bangladesh Project
November 2025
