## Raw Exchange-Rate Data Acquisition and Initial Inspection

Historical USD/IRR exchange-rate data were retrieved from the TGJU API using
the `price_dollar_rl` market indicator endpoint:

```text
https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl

The API was accessed using Python's requests library. A 30-second timeout was
used, and raise_for_status() was called to ensure that unsuccessful HTTP
responses caused the request to fail rather than being processed silently.

The response was parsed as JSON and inspected before being saved or
transformed.

Initial response inspection

The following temporary inspection code was used:
import requests

url = (
    "https://api.tgju.org/v1/market/indicator/"
    "summary-table-data/price_dollar_rl"
)

response = requests.get(url, timeout=30)
response.raise_for_status()

payload = response.json()

print("Top-level type:", type(payload).__name__)
print("Top-level keys:", list(payload.keys()))

for key, value in payload.items():
    if key != "data":
        print(f"{key}: {value!r}")

rows = payload.get("data")

print("\nData type:", type(rows).__name__)
print("Number of rows:", len(rows) if isinstance(rows, list) else "N/A")

if isinstance(rows, list) and rows:
    print("\nFirst row:")
    print(rows[0])

    print("\nColumns in first row:")
    print(len(rows[0]))

    print("\nLast row:")
    print(rows[-1])

    print("\nColumns in last row:")
    print(len(rows[-1]))

The response was a JSON object containing four top-level fields:

draw;
recordsTotal;
recordsFiltered;
data.

Both recordsTotal and recordsFiltered reported 3,916 observations. The
data field contained a list of 3,916 records.

The first returned record was:

[
  "1,935,850",
  "1,920,800",
  "1,936,200",
  "1,924,000",
  "<span class=\"low\" dir=\"ltr\">11000</span>",
  "<span class=\"low\" dir=\"ltr\">0.57%</span>",
  "2026/07/30",
  "1405/05/08"
]

The final returned record was:

[
  "13,700",
  "13,700",
  "13,700",
  "13,700",
  "<span class=\"low\" dir=\"ltr\">260</span>",
  "<span class=\"low\" dir=\"ltr\">1.93%</span>",
  "2011/11/26",
  "1390/09/05"
]

This showed that the records were returned in reverse chronological order,
from 30 July 2026 to 26 November 2011.

Each record contained eight fields representing:

opening price;
low price;
high price;
closing price;
absolute change;
percentage change;
Gregorian date;
Jalali date.

The change fields were returned as HTML-formatted strings, while the OHLC
prices were returned as strings containing thousands separators.

Structural consistency check

A second inspection checked whether every record contained the expected eight
fields:

from collections import Counter

import requests

url = (
    "https://api.tgju.org/v1/market/indicator/"
    "summary-table-data/price_dollar_rl"
)

response = requests.get(url, timeout=30)
response.raise_for_status()

rows = response.json()["data"]

column_counts = Counter(len(row) for row in rows)

print("Row-length counts:")
for length, count in sorted(column_counts.items()):
    print(f"{length} columns: {count} rows")

invalid_rows = [
    (index, row)
    for index, row in enumerate(rows)
    if len(row) != 8
]

print("\nRows not containing 8 columns:", len(invalid_rows))

The result was:

8 columns: 3916 rows
Rows not containing 8 columns: 0

All 3,916 records therefore had a consistent eight-field structure.

Raw-data preservation

After the response structure had been inspected, the API response was saved
unchanged as:

data/raw/usd_irr_tgju_history_raw.json

