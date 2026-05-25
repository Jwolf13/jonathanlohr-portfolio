from pathlib import Path
import requests
import json

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

# BLS API Key
api_key = "368db8e456d545809cec2948e0f670cd"

url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Try State & Area Employment, Hours, and Earnings (SMU) - Monthly data
# Format: SMU{state}{area}{industry}{datatype}
# NC = 37, Statewide = 00000
series_ids = [
    "SMU370000000000001",  # NC Statewide - Total nonfarm employment
    "SMU370600000000001",  # NC - Education & Health Services
    "SMU370000000100001",  # NC - Construction
]

payload = {
    "seriesid": series_ids,
    "startyear": "2022",
    "endyear": "2023",
    "registrationkey": api_key
}

response = requests.post(url, json=payload, timeout=30)
print("Status code:", response.status_code)
response.raise_for_status()

output_file = raw_dir / "bls_state_employment_nc.json"
output_file.write_text(json.dumps(response.json(), indent=2), encoding="utf-8")

print(f"Saved BLS employment data to {output_file}")

# Check what was returned
data = response.json()
if data.get("status") == "REQUEST_SUCCEEDED":
    print(f"Successfully retrieved {len(data['Results']['series'])} series")
    for series in data['Results']['series']:
        print(f"  - {series['seriesID']}: {len(series['data'])} data points")
else:
    print(f"Response status: {data.get('status')}")
    if data.get("message"):
        print(f"Messages: {data['message']}")


