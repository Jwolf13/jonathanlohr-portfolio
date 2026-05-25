from pathlib import Path
import requests
import json

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

#download employment projections data from BLS

url = "https://api.bls.gov/publicAPI/v2/timeseries/data/CEU0000000001"

if not url:
    print("ERROR: BLS API URL required")
    print("Add the BLS API URL to the url variable")
    exit(1)

#requset detailed occupation categories

occupation_vars = [
    "CEU0000000001",  # Total nonfarm
    "CEU0000000002",  # Total private   
    "CEU0000000003",  # Goods-producing
    "CEU0000000004",  # Service-providing
    "CEU0000000005",  # Private service-providing
    "CEU0000000006",  # Mining and logging
    "CEU0000000007",  # Construction
    "CEU0000000008",  # Manufacturing
    "CEU0000000009",  # Durable goods
    "CEU0000000010",  # Nondurable goods
    "CEU0000000011",  # Wholesale trade
    "CEU0000000012",  # Retail trade
    "CEU0000000013",  # Transportation and warehousing
    "CEU0000000014",  # Utilities
    "CEU0000000015",  # Information
    "CEU0000000016",  # Financial activities
    "CEU0000000017",  # Professional and business services
    "CEU0000000018",  # Education and health services
    "CEU0000000019",  # Leisure and hospitality
    "CEU0000000020",  # Other services
    "CEU0000000021",  # Government
]

#Fetch county level data for North Carolina (more granular)
params = {
    "get": ",".join(occupation_vars) + ",NAME",
    "for": "county:*",  # All counties
    "in": "state:37",  # Within North Carolina
}

response = requests.get(url, params=params, timeout=30)
print("Status code:", response.status_code)
response.raise_for_status()

data = response.json()
output_file = raw_dir / "bls_employment_projections_NC.json"
output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

print(f"Saved employment projections data to {output_file}")
print("\nTo get detailed employment projections, register for a BLS API key:")
print("https://www.bls.gov/developers/")
