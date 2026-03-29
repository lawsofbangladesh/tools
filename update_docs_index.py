#!/usr/bin/env python3
"""
Update docs.json, list.mdx, and years.mdx Index Files
======================================================

This script updates the docs, list, and years index files by adding
new acts, volumes, and years from the latest CSV data while preserving
all existing content and structure.

Features:
- Reads all volume CSV files from files/volumes/csv/
- Updates files/index/list.mdx   – prepends newly added acts at the top of
  the chronological table (newest act-id first)
- Updates files/index/years.mdx  – inserts any new years into the 6-column
  grid, sorted newest first
- Updates files/index/docs.json  – adds new volume groups and year groups to
  the Mintlify navigation, and appends missing acts to existing groups

All three operations are additive: no existing entry is ever deleted.

Author: Laws of Bangladesh Project
"""

import csv
import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

# Mapping from ASCII digits to Bengali (Unicode) digits
BENGALI_DIGITS = {
    "0": "০",
    "1": "১",
    "2": "২",
    "3": "৩",
    "4": "৪",
    "5": "৫",
    "6": "৬",
    "7": "৭",
    "8": "৮",
    "9": "৯",
}


def to_bengali_digits(text: str) -> str:
    """Convert ASCII digit characters in *text* to their Bengali equivalents."""
    return "".join(BENGALI_DIGITS.get(ch, ch) for ch in str(text))


# ---------------------------------------------------------------------------
# CSV reading
# ---------------------------------------------------------------------------

def read_all_acts(csv_dir: str):
    """Read every volume-*.csv file and return acts grouped by volume and year.

    Returns:
        (all_acts, volumes, years) where
          all_acts  – flat list of act dicts
          volumes   – {volume_number_str: [act, ...]}
          years     – {year_str: [act, ...]}
    """
    csv_path = Path(csv_dir)
    all_acts = []
    volumes: dict = defaultdict(list)
    years: dict = defaultdict(list)

    csv_files = sorted(csv_path.glob("volume-*.csv"))
    if not csv_files:
        print(f"  WARNING: No CSV files found in {csv_dir}")
        return all_acts, volumes, years

    for csv_file in csv_files:
        with open(csv_file, "r", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                act = {
                    "volume": row["volume_number"],
                    "year": row["year"],
                    "title": row["act_title"],
                    "number": row["act_number"],
                    "id": row["act_id"],
                    "link": row["link"],
                }
                all_acts.append(act)
                volumes[row["volume_number"]].append(act)
                years[row["year"]].append(act)

    return all_acts, volumes, years


# ---------------------------------------------------------------------------
# list.mdx
# ---------------------------------------------------------------------------

def update_list_mdx(list_mdx_path: Path, all_acts: list, verbose: bool = False) -> int:
    """Insert new acts into the chronological table in list.mdx.

    Only acts whose act-id is not already referenced in the file are added.
    Each new act is inserted at the position that preserves the table's
    descending act-id ordering, so:
      - newer high-id acts appear near the top
      - old gap-fill acts (low id) appear at the correct position further down

    Returns the number of rows added.
    """
    content = list_mdx_path.read_text(encoding="utf-8")

    # Collect every act-id already present in the file
    existing_ids = set(re.findall(r"/laws/act-(\d+)", content))

    # Identify acts that are missing and sort newest-first so we insert from
    # the top downward — this guarantees correct relative ordering after all
    # insertions because each new act is placed before the first existing row
    # whose act-id is strictly lower.
    new_acts = [a for a in all_acts if a["id"] not in existing_ids]
    new_acts.sort(key=lambda a: int(a["id"]), reverse=True)

    if not new_acts:
        if verbose:
            print("  list.mdx: no new acts to add")
        return 0

    # Locate the table header separator line (the dashes row)
    lines = content.split("\n")
    separator_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| ---") or line.startswith("| ----"):
            separator_idx = i
            break

    if separator_idx is None:
        print("  WARNING: Could not find table separator in list.mdx – skipping")
        return 0

    def make_row(act: dict) -> str:
        title_cell = f"[{act['title']}](/laws/act-{act['id']})"
        year_bn = to_bengali_digits(act["year"])
        return f"| {title_cell} | {act['number']} | {year_bn} | Not Verified | No |"

    # Insert each new act at the correct position, maintaining descending act-id
    # order.  We iterate new_acts from highest to lowest id; after each
    # insertion the `lines` list is updated so subsequent searches are correct.
    for act in new_acts:
        act_id_int = int(act["id"])
        new_row = make_row(act)

        # Scan the table (everything after the separator) to find the first
        # existing row whose act-id is *lower* than this act's id.
        insert_pos = None
        for i in range(separator_idx + 1, len(lines)):
            line = lines[i]
            if not line.startswith("|"):
                break  # end of table
            m = re.search(r"/laws/act-(\d+)", line)
            if m and int(m.group(1)) < act_id_int:
                insert_pos = i
                break

        if insert_pos is not None:
            lines.insert(insert_pos, new_row)
        else:
            # This act has the lowest id seen so far – append after the last
            # table row.
            end_pos = separator_idx + 1
            for i in range(separator_idx + 1, len(lines)):
                if lines[i].startswith("|"):
                    end_pos = i + 1
                else:
                    break
            lines.insert(end_pos, new_row)

    list_mdx_path.write_text("\n".join(lines), encoding="utf-8")

    if verbose:
        print(f"  list.mdx: added {len(new_acts)} new act(s)")

    return len(new_acts)


# ---------------------------------------------------------------------------
# years.mdx
# ---------------------------------------------------------------------------

def update_years_mdx(years_mdx_path: Path, all_years: dict, verbose: bool = False) -> int:
    """Add any new years to the 6-column grid in years.mdx.

    The table is rebuilt from all years (existing + new) sorted newest-first.
    All text outside the table (front-matter, headings, prose) is preserved.

    Returns the number of new years added.
    """
    content = years_mdx_path.read_text(encoding="utf-8")

    # Collect years already listed in the file
    existing_years: set = set(re.findall(r"/laws/(\d{4})", content))

    new_years = set(all_years.keys()) - existing_years
    if not new_years:
        if verbose:
            print("  years.mdx: no new years to add")
        return 0

    # Merge and sort all years descending
    all_year_list = sorted(existing_years | new_years, key=int, reverse=True)

    # Rebuild the 6-column table
    cols = 6
    header = (
        "| Year               | Year               | Year               "
        "| Year               | Year               | Year               |"
    )
    separator = (
        "| ------------------ | ------------------ | ------------------ "
        "| ------------------ | ------------------ | ------------------ |"
    )

    rows = []
    for i in range(0, len(all_year_list), cols):
        chunk = all_year_list[i : i + cols]
        cells = [f"[{y}](/laws/{y})" for y in chunk]
        while len(cells) < cols:
            cells.append("")
        rows.append("| " + " | ".join(cells) + " |")

    new_table = header + "\n" + separator + "\n" + "\n".join(rows)

    # Replace the existing table block in the file content
    table_pattern = re.compile(
        r"\| Year[^\n]*\n\| [-| ]+\n(?:\|[^\n]*\n)*",
        re.MULTILINE,
    )
    new_content, n_subs = table_pattern.subn(new_table + "\n", content)

    if n_subs == 0:
        print("  WARNING: Could not locate year table in years.mdx – skipping")
        return 0

    years_mdx_path.write_text(new_content, encoding="utf-8")

    if verbose:
        added_sorted = sorted(new_years, key=int, reverse=True)
        print(f"  years.mdx: added {len(new_years)} new year(s): {added_sorted}")

    return len(new_years)


# ---------------------------------------------------------------------------
# docs.json
# ---------------------------------------------------------------------------

def _extract_act_id_from_page(page: str) -> str | None:
    """Return the act-id string from a page path like 'laws/act-1234'."""
    if isinstance(page, str) and page.startswith("laws/act-"):
        return page.split("act-")[1]
    return None


def update_docs_json(
    docs_json_path: Path,
    all_acts: list,
    volumes_data: dict,
    years_data: dict,
    verbose: bool = False,
) -> tuple:
    """Update the Mintlify navigation in docs.json.

    For the **Laws of Bangladesh** dropdown (volumes):
      - Existing volume groups receive any missing act pages appended in
        CSV order.
      - New volume groups are inserted after the last existing volume group,
        sorted by volume number.

    For the **Yearly Laws** dropdown (years):
      - Existing year groups receive any missing act pages inserted at the
        top of the list (right after the year index page), sorted by
        act-id descending (newest first).
      - New year groups are inserted at the correct position so the list
        remains sorted newest-year-first.

    All existing pages and groups are left untouched.

    Returns (volumes_added, years_added, acts_added_total).
    """
    with open(docs_json_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    dropdowns = data["navigation"]["dropdowns"]

    volumes_added = 0
    years_added = 0
    acts_added_total = 0

    # ------------------------------------------------------------------
    # 1. "Laws of Bangladesh" – volume groups
    # ------------------------------------------------------------------
    laws_dropdown = next(
        (d for d in dropdowns if d.get("dropdown") == "Laws of Bangladesh"), None
    )
    if laws_dropdown:
        laws_group = next(
            (g for g in laws_dropdown.get("groups", []) if g.get("group") == "Laws"),
            None,
        )
        if laws_group:
            pages = laws_group["pages"]  # list of strings and volume-group dicts

            # Map volume number -> existing group dict (in-place reference)
            existing_vol_groups: dict = {}
            for item in pages:
                if isinstance(item, dict) and item.get("group", "").startswith("Volume "):
                    vol_num = item["group"].split(" ", 1)[1]
                    existing_vol_groups[vol_num] = item

            for vol_num in sorted(volumes_data.keys(), key=int):
                vol_acts = volumes_data[vol_num]

                if vol_num in existing_vol_groups:
                    # Add any acts missing from the group
                    vol_group = existing_vol_groups[vol_num]
                    existing_ids = {
                        _extract_act_id_from_page(p)
                        for p in vol_group["pages"]
                        if _extract_act_id_from_page(p)
                    }
                    missing = [a for a in vol_acts if a["id"] not in existing_ids]
                    if missing:
                        for act in missing:
                            vol_group["pages"].append(f"laws/act-{act['id']}")
                        acts_added_total += len(missing)
                        if verbose:
                            print(
                                f"  docs.json (volumes): added {len(missing)} act(s)"
                                f" to Volume {vol_num}"
                            )
                else:
                    # Create a new volume group and insert after the last existing one
                    new_group = {
                        "group": f"Volume {vol_num}",
                        "icon": "book",
                        "pages": [f"laws/volume-{vol_num}"]
                        + [f"laws/act-{a['id']}" for a in vol_acts],
                    }
                    # Find the index of the last volume group in pages
                    last_idx = 0
                    for idx, item in enumerate(pages):
                        if isinstance(item, dict) and item.get("group", "").startswith("Volume "):
                            last_idx = idx
                    pages.insert(last_idx + 1, new_group)
                    volumes_added += 1
                    if verbose:
                        print(
                            f"  docs.json (volumes): added new Volume {vol_num}"
                            f" ({len(vol_acts)} acts)"
                        )

    # ------------------------------------------------------------------
    # 2. "Yearly Laws" – year groups
    # ------------------------------------------------------------------
    yearly_dropdown = next(
        (d for d in dropdowns if d.get("dropdown") == "Yearly Laws"), None
    )
    if yearly_dropdown:
        years_group = next(
            (g for g in yearly_dropdown.get("groups", []) if g.get("group") == "Years"),
            None,
        )
        if years_group:
            year_pages = years_group["pages"]  # list of year-group dicts

            # Map year string -> existing group dict (in-place reference)
            existing_year_groups: dict = {}
            for item in year_pages:
                if isinstance(item, dict) and item.get("group", "").isdigit():
                    existing_year_groups[item["group"]] = item

            # Process years newest-first so insertions maintain descending order
            for year_str in sorted(years_data.keys(), key=int, reverse=True):
                year_acts = years_data[year_str]

                if year_str in existing_year_groups:
                    # Add any acts missing from the group (newest first)
                    year_group = existing_year_groups[year_str]
                    existing_ids = {
                        _extract_act_id_from_page(p)
                        for p in year_group["pages"]
                        if _extract_act_id_from_page(p)
                    }
                    missing = sorted(
                        [a for a in year_acts if a["id"] not in existing_ids],
                        key=lambda a: int(a["id"]),
                        reverse=True,
                    )
                    if missing:
                        # Insert right after the year index page (position 1)
                        for i, act in enumerate(missing):
                            year_group["pages"].insert(1 + i, f"laws/act-{act['id']}")
                        acts_added_total += len(missing)
                        if verbose:
                            print(
                                f"  docs.json (years): added {len(missing)} act(s)"
                                f" to year {year_str}"
                            )
                else:
                    # Create a new year group, inserting before the first
                    # existing year that is older than this one
                    acts_sorted = sorted(year_acts, key=lambda a: int(a["id"]), reverse=True)
                    new_group = {
                        "group": year_str,
                        "icon": "calendar",
                        "pages": [f"laws/{year_str}"]
                        + [f"laws/act-{a['id']}" for a in acts_sorted],
                    }
                    # Find insertion index (before the first group with a smaller year)
                    insert_idx = len(year_pages)  # default: append
                    for idx, item in enumerate(year_pages):
                        if isinstance(item, dict) and item.get("group", "").isdigit():
                            if int(item["group"]) < int(year_str):
                                insert_idx = idx
                                break
                    year_pages.insert(insert_idx, new_group)
                    years_added += 1
                    if verbose:
                        print(
                            f"  docs.json (years): added new year {year_str}"
                            f" ({len(year_acts)} acts)"
                        )

    # Write back, preserving Unicode characters
    with open(docs_json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    return volumes_added, years_added, acts_added_total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Update docs.json, list.mdx, and years.mdx with new acts from CSV data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default paths and verbose output
  python update_docs_index.py --verbose

  # Specify custom CSV directory and index directory
  python update_docs_index.py --csv files/volumes/csv --index files/index
        """,
    )
    parser.add_argument(
        "--csv",
        "-c",
        default="files/volumes/csv",
        help="Directory containing volume-*.csv files (default: files/volumes/csv)",
    )
    parser.add_argument(
        "--index",
        "-i",
        default="files/index",
        help="Directory containing docs.json, list.mdx, years.mdx (default: files/index)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress for each change",
    )
    args = parser.parse_args()

    index_dir = Path(args.index)
    list_mdx_path = index_dir / "list.mdx"
    years_mdx_path = index_dir / "years.mdx"
    docs_json_path = index_dir / "docs.json"

    print("=" * 60)
    print("Bangladesh Laws – Docs/List/Years Index Updater")
    print("=" * 60)
    print()

    # Read CSV data
    print(f"Reading CSV files from {args.csv}...")
    all_acts, volumes, years = read_all_acts(args.csv)
    print(f"  Found {len(all_acts)} acts across {len(volumes)} volumes and {len(years)} years")
    print()

    # Update list.mdx
    print("Updating list.mdx...")
    list_added = update_list_mdx(list_mdx_path, all_acts, verbose=args.verbose)

    # Update years.mdx
    print("Updating years.mdx...")
    years_added_count = update_years_mdx(years_mdx_path, years, verbose=args.verbose)

    # Update docs.json
    print("Updating docs.json...")
    vol_added, yr_added, acts_added = update_docs_json(
        docs_json_path, all_acts, volumes, years, verbose=args.verbose
    )

    # Summary
    print()
    print("=" * 60)
    print("Update Summary")
    print("=" * 60)
    print(f"list.mdx   – new acts added:          {list_added}")
    print(f"years.mdx  – new years added:          {years_added_count}")
    print(f"docs.json  – new volume groups added:  {vol_added}")
    print(f"docs.json  – new year groups added:    {yr_added}")
    print(f"docs.json  – act pages added (total):  {acts_added}")
    print("=" * 60)


if __name__ == "__main__":
    main()
