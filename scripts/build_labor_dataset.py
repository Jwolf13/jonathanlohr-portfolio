from pathlib import Path
import pandas as pd
import json

raw_file = Path("data/raw/census_labor_nc_2022.json")
processed_dir = Path("data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)

data = json.loads(raw_file.read_text(encoding="utf-8"))

# Census API returns [headers, row1, row2, ...]
headers = data[0]
rows = data[1:]

df = pd.DataFrame(rows, columns=headers)

# Rename Census columns to human-readable names
rename_dict = {
    "B23001_001E": "Labor Force Total",
    "B23025_002E": "In Labor Force",
    "B23025_005E": "Unemployed",
    "C24010_002E": "Management/Business/Science/Arts",
    "C24010_011E": "Service Occupations",
    "C24010_020E": "Sales and Office",
    "C24010_029E": "Natural Resources/Construction/Maintenance",
    "C24010_038E": "Production/Transportation/Material Moving",
    "NAME": "County",
}
df = df.rename(columns=rename_dict)

output_csv = processed_dir / "labor_preview.csv"
output_json = processed_dir / "labor_preview.json"

df.to_csv(output_csv, index=False)
df.to_json(output_json, orient="records", indent=2)

print(f"Saved CSV to {output_csv}")
print(f"Saved JSON to {output_json}")