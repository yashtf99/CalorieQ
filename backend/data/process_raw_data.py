"""
process_raw_data.py
-------------------
Converts all source Excel files to CSV, placing outputs in a
parallel *-processed/ folder next to each *-raw-data/ folder.

Current sources handled:
  - INDB-raw-data/  → INDB-processed/
      INDB.xlsx              → indb.csv          (per-100g nutrient data, unit_serving_* dropped)
      recipes.xlsx           → recipes.csv
      recipes_names.xlsx     → recipes_names.csv
      recipes_servingsize.xlsx → recipes_servingsize.csv
      recipe_links.xlsx      → recipe_links.csv
      UK_fct.xlsx            → uk_fct.csv        (Sheet1 only)
      US_fct.xlsx            → us_fct.csv        (Sheet1 only)
      USDA_nrf.xlsx          → usda_nrf.csv      (Sheet1 only)
      Units.xlsx             → units.csv

Usage:
    python data/process_raw_data.py
"""

import csv
import openpyxl
from pathlib import Path

DATA_DIR = Path(__file__).parent


def xlsx_to_csv(src: Path, dst: Path, sheet_index: int = 0, drop_col_prefix: str = None):
    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    ws = wb.worksheets[sheet_index]

    rows = ws.iter_rows(values_only=True)
    headers = next(rows)

    if drop_col_prefix:
        keep = [i for i, h in enumerate(headers) if not str(h or "").startswith(drop_col_prefix)]
    else:
        keep = list(range(len(headers)))

    dst.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([headers[i] for i in keep])
        for row in rows:
            writer.writerow([row[i] for i in keep])
            written += 1

    print(f"  {src.name} > {dst.name}  ({written} rows, {len(keep)} cols)")
    wb.close()


def process_indb():
    raw = DATA_DIR / "INDB-raw-data"
    out = DATA_DIR / "INDB-processed"

    conversions = [
        # (source_file, output_file, sheet_index, drop_col_prefix)
        ("INDB.xlsx",                "indb.csv",                0, "unit_serving_"),
        ("recipes.xlsx",             "recipes.csv",             0, None),
        ("recipes_names.xlsx",       "recipes_names.csv",       0, None),
        ("recipes_servingsize.xlsx", "recipes_servingsize.csv", 0, None),
        ("recipe_links.xlsx",        "recipe_links.csv",        0, None),
        ("UK_fct.xlsx",              "uk_fct.csv",              0, None),
        ("US_fct.xlsx",              "us_fct.csv",              0, None),
        ("USDA_nrf.xlsx",            "usda_nrf.csv",            0, None),
        ("Units.xlsx",               "units.csv",               0, None),
    ]

    print("Processing INDB-raw-data >")
    for src_name, dst_name, sheet_idx, drop_prefix in conversions:
        xlsx_to_csv(raw / src_name, out / dst_name, sheet_idx, drop_prefix)


if __name__ == "__main__":
    process_indb()
    print("Done.")
