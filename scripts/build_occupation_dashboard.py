from pathlib import Path
import pandas as pd
import json

raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)

# Load Census occupation data for NC
occupation_file = raw_dir / "census_occupations_nc_2022.json"
occupation_data = json.loads(occupation_file.read_text(encoding="utf-8"))

headers = occupation_data[0]
rows = occupation_data[1:]

df = pd.DataFrame(rows, columns=headers)

# Rename for clarity
rename_dict = {
    "C24010_002E": "Management_Business_Science",
    "C24010_011E": "Service",
    "C24010_020E": "Sales_Office",
    "C24010_029E": "Natural_Resources_Construction",
    "C24010_038E": "Production_Transportation",
    "NAME": "County",
}
df = df.rename(columns=rename_dict)

# Convert employment counts to integers
employment_cols = [
    "Management_Business_Science",
    "Service",
    "Sales_Office",
    "Natural_Resources_Construction",
    "Production_Transportation",
]

for col in employment_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# Calculate totals and percentages by occupation category
dashboard = {
    "state": "North Carolina",
    "year": 2022,
    "data_source": "U.S. Census Bureau American Community Survey (ACS)",
    "occupations": []
}

occupation_titles = {
    "Management_Business_Science": "Management, Business, Science & Arts",
    "Service": "Service",
    "Sales_Office": "Sales & Office",
    "Natural_Resources_Construction": "Natural Resources, Construction & Maintenance",
    "Production_Transportation": "Production, Transportation & Material Moving",
}

# Aggregate by occupation type (statewide)
statewide_totals = df[employment_cols].sum()

for col in employment_cols:
    count = int(statewide_totals[col])
    total = statewide_totals.sum()
    percentage = (count / total * 100) if total > 0 else 0
    
    dashboard["occupations"].append({
        "title": occupation_titles[col],
        "employment_count": count,
        "employment_percentage": round(percentage, 1),
        "counties": df[["County", col]].rename(columns={col: "employment"}).to_dict("records"),
    })

# Sort by employment count
dashboard["occupations"].sort(key=lambda x: x["employment_count"], reverse=True)

# Save dashboard data
output_file = processed_dir / "occupation_dashboard.json"
output_file.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

print(f"Dashboard created: {output_file}")
print(f"\nOccupation Categories (NC Statewide):")
for occ in dashboard["occupations"]:
    print(f"  {occ['title']}: {occ['employment_count']:,} workers ({occ['employment_percentage']}%)")
