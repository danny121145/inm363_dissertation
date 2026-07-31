from pathlib import Path

import requests


API_URL = (
    "https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl"
)

OUTPUT_PATH = Path(
    "data/raw/usd_irr_tgju_history_raw.json"
)

def download_data() -> None:
    response = requests.get(
        API_URL,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise TypeError("Expected the API response to be a JSON object.")

    rows = payload.get("data")

    if not isinstance(rows, list):
        raise ValueError("The API response does not contain a data list.")

    print("HTTP status:", response.status_code)
    print("Records downloaded:", len(rows))
    print("Reported total:", payload.get("recordsTotal"))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        raise FileExistsError(f"File already exists: {OUTPUT_PATH}")
    
    OUTPUT_PATH.write_bytes(response.content)

    print(f"Data saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    download_data()