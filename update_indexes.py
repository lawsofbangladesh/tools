#!/usr/bin/env python3
"""
Update Volume and Year Index MDX Files
========================================

This script updates the volume-*.mdx and year-*.mdx index files
based on the latest data from CSV files in files/volumes/csv/

Features:
- Reads all volume CSV files
- Generates/updates volume-*.mdx files with act listings
- Generates/updates year-*.mdx files with acts grouped by year
- Creates main index.mdx with all volumes

Author: Laws of Bangladesh Project
Date: November 2025
"""

import csv
from pathlib import Path
from collections import defaultdict
import argparse

def read_volume_csv(csv_path):
    """Read a volume CSV file and return list of acts
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        List of dictionaries with act information
    """
    acts = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            acts.append({
                'volume': row['volume_number'],
                'year': row['year'],
                'title': row['act_title'],
                'number': row['act_number'],
                'id': row['act_id'],
                'link': row['link']
            })
    return acts

def generate_volume_mdx(volume_number, acts, output_dir):
    """Generate a volume-*.mdx file
    
    Args:
        volume_number: Volume number (e.g., "56")
        acts: List of act dictionaries
        output_dir: Output directory path
    """
    if not acts:
        return
    
    # Create volume subdirectory
    volume_dir = output_dir / "volume"
    volume_dir.mkdir(parents=True, exist_ok=True)
    
    # Get volume title from first act
    first_act = acts[0]
    year = first_act['year']
    
    # Group by year to determine title
    years = sorted(set(act['year'] for act in acts))
    
    # Create title
    if len(years) == 1:
        # Single year
        title = f"{year} সনের {acts[0]['number']} নং অধ্যাদেশ হইতে {acts[-1]['number']} নং অধ্যাদেশ"
    else:
        # Multiple years - use range
        title = f"{years[0]} থেকে {years[-1]} সনের আইন"
    
    # Build MDX content
    mdx = []
    mdx.append("---")
    mdx.append(f'title: "{title}"')
    mdx.append(f'sidebarTitle: "Volume {volume_number}"')
    mdx.append('description: ""')
    mdx.append("---")
    mdx.append("")
    mdx.append("| Year | Short Title | Act No |")
    mdx.append("|------|-------------|--------|")
    
    for act in acts:
        mdx.append(f"| {act['year']} | [{act['title']}](/laws/act-{act['id']}) | {act['number']} |")
    
    # Save file in volume subdirectory
    output_path = volume_dir / f"volume-{volume_number}.mdx"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mdx))
    
    return output_path

def generate_year_mdx(year, acts, output_dir):
    """Generate a year-*.mdx file (e.g., 2025.mdx)
    
    Args:
        year: Year (e.g., "2025")
        acts: List of act dictionaries for that year
        output_dir: Output directory path
    """
    if not acts:
        return
    
    # Create year subdirectory
    year_dir = output_dir / "year"
    year_dir.mkdir(parents=True, exist_ok=True)
    
    # Sort acts by ID (newest first)
    acts_sorted = sorted(acts, key=lambda x: int(x['id']), reverse=True)
    
    # Build MDX content
    mdx = []
    mdx.append("---")
    mdx.append(f'title: "Laws of {year}"')
    mdx.append(f'sidebarTitle: "{year}"')
    mdx.append(f'description: "Laws published in {year}."')
    mdx.append("---")
    mdx.append("")
    mdx.append(f"## Browse the laws of {year}")
    mdx.append("")
    mdx.append("| Act Title |")
    mdx.append("|-----------|")
    
    for act in acts_sorted:
        mdx.append(f"| [{act['title']}](/laws/act-{act['id']}) |")
    
    # Save file in year subdirectory
    output_path = year_dir / f"{year}.mdx"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mdx))
    
    return output_path

def generate_index_mdx(volumes, output_dir):
    """Generate main index.mdx with all volumes
    
    Args:
        volumes: Dictionary of volume_number -> list of acts
        output_dir: Output directory path
    """
    # Build MDX content
    mdx = []
    mdx.append("---")
    mdx.append('title: "Laws of Bangladesh"')
    mdx.append('sidebarTitle: "All Volumes"')
    mdx.append('description: "Complete collection of Bangladesh laws organized by volume."')
    mdx.append("---")
    mdx.append("")
    mdx.append("## Browse by Volume")
    mdx.append("")
    mdx.append("| Volume | Acts | Years |")
    mdx.append("|--------|------|-------|")
    
    # Sort volumes
    for volume_num in sorted(volumes.keys(), key=lambda x: int(x)):
        acts = volumes[volume_num]
        years = sorted(set(act['year'] for act in acts))
        year_range = f"{years[0]}" if len(years) == 1 else f"{years[0]}-{years[-1]}"
        
        mdx.append(f"| [Volume {volume_num}](/laws/volume-{volume_num}) | {len(acts)} | {year_range} |")
    
    # Save file
    output_path = output_dir / "index.mdx"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(mdx))
    
    return output_path

def update_indexes(csv_dir, output_dir, verbose=False):
    """Update all index files based on CSV data
    
    Args:
        csv_dir: Directory containing volume CSV files
        output_dir: Directory to save index MDX files
        verbose: Print detailed progress
    
    Returns:
        Tuple of (volume_count, year_count, total_acts)
    """
    csv_path = Path(csv_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Read all CSV files
    volumes = {}  # volume_number -> [acts]
    years = defaultdict(list)  # year -> [acts]
    
    csv_files = sorted(csv_path.glob("volume-*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {csv_dir}")
        return 0, 0, 0
    
    print(f"Reading {len(csv_files)} CSV files...")
    print("-" * 60)
    
    total_acts = 0
    for csv_file in csv_files:
        acts = read_volume_csv(csv_file)
        if acts:
            volume_num = acts[0]['volume']
            volumes[volume_num] = acts
            
            # Group by year
            for act in acts:
                years[act['year']].append(act)
            
            total_acts += len(acts)
            
            if verbose:
                print(f"Read volume {volume_num}: {len(acts)} acts")
    
    print(f"\nTotal acts: {total_acts}")
    print(f"Volumes: {len(volumes)}")
    print(f"Years: {len(years)}")
    print("-" * 60)
    
    # Generate volume index files
    print("\nGenerating volume index files...")
    for volume_num, acts in sorted(volumes.items(), key=lambda x: int(x[0])):
        output_file = generate_volume_mdx(volume_num, acts, output_path)
        if verbose:
            print(f"  Created: volume-{volume_num}.mdx ({len(acts)} acts)")
        elif int(volume_num) % 10 == 0:
            print(f"  Progress: Volume {volume_num}...")
    
    # Generate year index files
    print("\nGenerating year index files...")
    for year, acts in sorted(years.items()):
        output_file = generate_year_mdx(year, acts, output_path)
        if verbose:
            print(f"  Created: {year}.mdx ({len(acts)} acts)")
    
    # Generate main index
    print("\nGenerating main index...")
    generate_index_mdx(volumes, output_path)
    print("  Created: index.mdx")
    
    return len(volumes), len(years), total_acts

def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Update volume and year index MDX files from CSV data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update indexes with default paths
  python update_indexes.py
  
  # Update with verbose output
  python update_indexes.py --verbose
  
  # Specify custom paths
  python update_indexes.py --csv files/volumes/csv --output files/index
        """
    )
    
    parser.add_argument(
        '--csv', '-c',
        default='files/volumes/csv',
        help='Directory containing volume CSV files (default: files/volumes/csv)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='files/index',
        help='Output directory for index MDX files (default: files/index)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress for each file'
    )
    
    args = parser.parse_args()
    
    # Run update
    print("=" * 60)
    print("Bangladesh Laws Index Updater")
    print("=" * 60)
    print()
    
    volume_count, year_count, total_acts = update_indexes(
        args.csv,
        args.output,
        verbose=args.verbose
    )
    
    # Print summary
    print()
    print("=" * 60)
    print("Update Summary")
    print("=" * 60)
    print(f"Volume index files:  {volume_count}")
    print(f"Year index files:    {year_count}")
    print(f"Total acts indexed:  {total_acts}")
    print(f"Main index:          index.mdx")
    print("=" * 60)

if __name__ == "__main__":
    main()
