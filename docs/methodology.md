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

## RAW TGJU data cleaning methodology
1.Define the location of the raw TGJU JSON file and the location where the cleaned interim CSV file will be saved.
2. Open the raw JSON file without changing it, so the original downloaded data remains preserved.
3. Extract the historical exchange-rate rows from the data section of the JSON structure.
4. Assign clear column names to the values in each row: open, low, high, close, change, change_percent, date, and jalali_date.
5. Convert the raw rows into a pandas dataframe so that the observations can be cleaned and validated as a table.
6. Clean the numerical columns by:
removing any HTML tags;
removing commas used as thousands separators;
removing percentage signs;
removing unnecessary spaces;
replacing blank values or hyphens with missing values;
converting the remaining values into numbers.
7. Convert the Gregorian date column from text in YYYY/MM/DD format into a proper date value.
8. Stop the process if any Gregorian date cannot be parsed correctly. This prevents invalid dates from entering the interim dataset.
9. Sort all observations by Gregorian date, starting with the earliest date and ending with the most recent date.
10. Check whether the dataset contains more than one row for the same Gregorian date.
11. Stop the process and report the affected dates if duplicate dates are found. Do not automatically delete duplicates because they should first be checked against the raw source.
12. Stop the process if any required values are missing. The change and change_percent columns are allowed to contain missing values because they can be recalculated later if necessary.
13. Check whether the daily open, high, low, and close values have valid relationships.
14. Treat a row as valid when:
the low value is not greater than the high value;
the open value is between the low and high;
the close value is between the low and high.
15. Create a new Boolean column called ohlc_valid.
16. Mark each row as True when its OHLC values are logically consistent and False when they are not.
17. Retain rows with invalid OHLC relationships instead of deleting or correcting them. Print a warning showing how many invalid rows were found so they can be investigated later.
18. Save the cleaned dataframe as a CSV file without adding a pandas row index.
19. Print a final summary containing:
the saved file location;
the number of rows;
the column names;
the date range;
the number of duplicate dates;
the total number of missing values.

##daily data prep results
The cleaning process created an interim dataset with 3,916 daily observations, covering the period from 26 November 2011 to 30 July 2026.

There were no duplicate dates, and none of the required fields had missing values. However, the change column had 179 missing values, and the change_percent column had 190 missing values. These missing values were accepted because these columns are not needed to calculate returns or volatility later.

Eight rows had problems with the open, high, low, and close values. In some cases, the opening or closing price was outside the reported daily low and high range. In other cases, the reported low price was higher than the high price.

These rows were kept in the dataset and marked as ohlc_valid=False. They were not removed or changed because they may still be useful later, and keeping them makes it possible to compare them with the original raw data.