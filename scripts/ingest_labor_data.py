from pathlib import Path
import requests
import json

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

# Census Bureau American Community Survey (ACS) API
# Get comprehensive labor data for North Carolina
census_api_key = "4d5243a948465a2aa89ab53fa3c5263c9082c560"

url = "https://api.census.gov/data/2022/acs/acs5"

# Labor data variables all business secotors and labor force status
labor_vars = [
    "B23001_001E",  # Total population in labor force
    "B23025_002E",  # Total in labor force
    "B23025_005E",  # Unemployed
    "C24010_002E",  # Management, business, science, arts
    "C24010_011E",  # Service occupations
    "C24010_020E",  # Sales and office occupations
    "C24010_029E",  # Natural resources, construction, maintenance
    "C24010_038E",  # Production, transportation, material moving
]

# Fetch state and county-level data for North Carolina
params = {
    "get": ",".join(labor_vars) + ",NAME",
    "for": "county:*",
    "in": "state:37",
    "key": census_api_key
}

response = requests.get(url, params=params, timeout=30)
print("Status code:", response.status_code)
response.raise_for_status()

output_file = raw_dir / "census_labor_nc_2022.json"
output_file.write_text(json.dumps(response.json(), indent=2), encoding="utf-8")

print(f"Saved labor data to {output_file}")