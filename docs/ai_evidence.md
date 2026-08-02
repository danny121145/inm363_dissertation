# Generative AI Evidence

## EVIDENCE-AI-001 — Writing the raw-data acquisition methodology

**Date:** 31 July 2026

**Related register entry:** AI-001

**Related activity:** TGJU API acquisition and initial response inspection

**Related commit:** c05cceb

### Context

I had already selected TGJU as the exchange-rate data source, accessed the API,
written and executed the inspection code, recorded the terminal outputs and
written informal conclusions.

The notes were disorganised, so I used ChatGPT to turn the material into a
structured Markdown methodology section.

### Exact prompt

> what i have is my methodolgy for gaterhing the data from this api and short information i gathered from it. its really messy i need you to clean it up. 
> first log
>
> ```python
> import requests
>
> url = (
>     "https://api.tgju.org/v1/market/indicator/"
>     "summary-table-data/price_dollar_rl"
> )
>
> response = requests.get(url, timeout=30)
> response.raise_for_status()
>
> payload = response.json()
>
> print("Top-level type:", type(payload).__name__)
> print("Top-level keys:", list(payload.keys()))
>
> for key, value in payload.items():
>     if key != "data":
>         print(f"{key}: {value!r}")
>
> rows = payload.get("data")
>
> print("\nData type:", type(rows).__name__)
> print("Number of rows:", len(rows) if isinstance(rows, list) else "N/A")
>
> if isinstance(rows, list) and rows:
>     print("\nFirst row:")
>     print(rows[0])
>
>     print("\nColumns in first row:")
>     print(len(rows[0]))
>
>     print("\nLast row:")
>     print(rows[-1])
>
>     print("\nColumns in last row:")
>     print(len(rows[-1]))
> PY
> ```
>
> first response
>
> ```text
> /Users/danielasghari/Desktop/inm363_dissertation/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
>   warnings.warn(
> Top-level type: dict
> Top-level keys: ['draw', 'recordsTotal', 'recordsFiltered', 'data']
> draw: None
> recordsTotal: 3916
> recordsFiltered: 3916
>
> Data type: list
> Number of rows: 3916
>
> First row:
> ['1,935,850', '1,920,800', '1,936,200', '1,924,000', '<span class="low" dir="ltr">11000</span>', '<span class="low" dir="ltr">0.57%</span>', '2026/07/30', '1405/05/08']
>
> Columns in first row:
> 8
>
> Last row:
> ['13,700', '13,700', '13,700', '13,700', '<span class="low" dir="ltr">260</span>', '<span class="low" dir="ltr">1.93%</span>', '2011/11/26', '1390/09/05']
>
> Columns in last row:
> 8
> ```
>
> verdict: json object, 3916 rows, 8 columns, newest to oldest, from 2011-11-26 till 2026-07-30
>
> second log:
>
> ```python
> python - <<'PY'
> import requests
> from collections import Counter
>
> url = (
>     "https://api.tgju.org/v1/market/indicator/"
>     "summary-table-data/price_dollar_rl"
> )
>
> response = requests.get(url, timeout=30)
> response.raise_for_status()
>
> rows = response.json()["data"]
>
> column_counts = Counter(len(row) for row in rows)
>
> print("Row-length counts:")
> for length, count in sorted(column_counts.items()):
>     print(f"{length} columns: {count} rows")
>
> invalid_rows = [
>     (index, row)
>     for index, row in enumerate(rows)
>     if len(row) != 8
> ]
>
> print("\nRows not containing 8 columns:", len(invalid_rows))
>
> for index, row in invalid_rows[:5]:
>     print(index, row)
> PY
> ```
>
> second response:
>
> ```text
> /Users/danielasghari/Desktop/inm363_dissertation/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
>   warnings.warn(
> Row-length counts:
> 8 columns: 3916 rows
>
> Rows not containing 8 columns: 0
> ```
>
> verdict: all records contain 8 fields

### Follow-up prompt

> i need this in markdown so i can save it in my file

### Exact response used

The complete following response was copied into `docs/methodology.md`:

> ## Raw Exchange-Rate Data Acquisition and Initial Inspection
>
> Historical USD/IRR exchange-rate data were retrieved from the TGJU API using
> the `price_dollar_rl` market indicator endpoint:
>
> ```text
> https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl
> ```
>
> The API was accessed using Python's `requests` library. A 30-second timeout was
> used, and `raise_for_status()` was called so that unsuccessful HTTP responses
> would raise an error rather than be processed silently.
>
> The response was parsed as JSON and inspected before any cleaning or
> transformation was performed.
>
> ### Initial Response Inspection
>
> The following temporary inspection code was used:
>
> ```python
> import requests
>
> url = (
>     "https://api.tgju.org/v1/market/indicator/"
>     "summary-table-data/price_dollar_rl"
> )
>
> response = requests.get(url, timeout=30)
> response.raise_for_status()
>
> payload = response.json()
>
> print("Top-level type:", type(payload).__name__)
> print("Top-level keys:", list(payload.keys()))
>
> for key, value in payload.items():
>     if key != "data":
>         print(f"{key}: {value!r}")
>
> rows = payload.get("data")
>
> print("\nData type:", type(rows).__name__)
> print("Number of rows:", len(rows) if isinstance(rows, list) else "N/A")
>
> if isinstance(rows, list) and rows:
>     print("\nFirst row:")
>     print(rows[0])
>
>     print("\nFields in first row:")
>     print(len(rows[0]))
>
>     print("\nLast row:")
>     print(rows[-1])
>
>     print("\nFields in last row:")
>     print(len(rows[-1]))
> ```
>
> The response was a JSON object containing four top-level fields:
>
> - `draw`
> - `recordsTotal`
> - `recordsFiltered`
> - `data`
>
> Both `recordsTotal` and `recordsFiltered` reported 3,916 observations. The
> `data` field contained a list of 3,916 records.
>
> The first returned record was:
>
> ```text
> [
>   "1,935,850",
>   "1,920,800",
>   "1,936,200",
>   "1,924,000",
>   "<span class=\"low\" dir=\"ltr\">11000</span>",
>   "<span class=\"low\" dir=\"ltr\">0.57%</span>",
>   "2026/07/30",
>   "1405/05/08"
> ]
> ```
>
> The final returned record was:
>
> ```text
> [
>   "13,700",
>   "13,700",
>   "13,700",
>   "13,700",
>   "<span class=\"low\" dir=\"ltr\">260</span>",
>   "<span class=\"low\" dir=\"ltr\">1.93%</span>",
>   "2011/11/26",
>   "1390/09/05"
> ]
> ```
>
> This showed that the records were returned in reverse chronological order,
> from 30 July 2026 to 26 November 2011.
>
> Each record contained eight fields representing:
>
> 1. opening price
> 2. low price
> 3. high price
> 4. closing price
> 5. absolute change
> 6. percentage change
> 7. Gregorian date
> 8. Jalali date
>
> The change fields were returned as HTML-formatted strings, while the OHLC
> prices were returned as strings containing thousands separators.
>
> ### Structural Consistency Check
>
> A second inspection checked whether every record contained the expected eight
> fields:
>
> ```python
> from collections import Counter
>
> import requests
>
> url = (
>     "https://api.tgju.org/v1/market/indicator/"
>     "summary-table-data/price_dollar_rl"
> )
>
> response = requests.get(url, timeout=30)
> response.raise_for_status()
>
> rows = response.json()["data"]
>
> column_counts = Counter(len(row) for row in rows)
>
> print("Row-length counts:")
> for length, count in sorted(column_counts.items()):
>     print(f"{length} fields: {count} rows")
>
> invalid_rows = [
>     (index, row)
>     for index, row in enumerate(rows)
>     if len(row) != 8
> ]
>
> print("\nRows not containing 8 fields:", len(invalid_rows))
>
> for index, row in invalid_rows[:5]:
>     print(index, row)
> ```
>
> The result was:
>
> ```text
> 8 fields: 3916 rows
> Rows not containing 8 fields: 0
> ```
>
> All 3,916 records therefore had a consistent eight-field structure.
>
> ### Raw-Data Preservation
>
> After the response structure had been inspected, the API response was saved
> unchanged as:
>
> ```text
> data/raw/usd_irr_tgju_history_raw.json
> ```
>
> The raw file preserves the compact JSON returned by the API. No field names
> were added, HTML was not removed, dates were not reformatted, and price values
> were not converted at this stage.
>
> All cleaning and transformation are carried out separately so that the
> original source response remains available for reproducibility and validation.
>
> ### Environment Warning
>
> During retrieval, `urllib3` produced a `NotOpenSSLWarning` because the Python
> 3.9 installation was compiled using LibreSSL 2.8.3 rather than a supported
> OpenSSL version.
>
> The warning did not prevent the request from completing. The API returned HTTP
> status 200 and the expected JSON response, so the message was treated as an
> environment warning rather than a data-retrieval failure.

### What I used

I copied the entire response into `docs/methodology.md`.

The full wording, organisation, headings and explanatory presentation were
generated by ChatGPT.

The underlying API retrieval, inspection code, terminal outputs, numerical
results, observations and initial conclusions were produced by me before the
prompt was submitted.

### What I changed or rejected

I used the complete response without material changes.

No generated numerical result, dataset value or source-selection decision was
introduced.

### Verification

I checked the generated methodology against:

- the original Python inspection code;
- the original terminal outputs;
- the saved raw JSON file;
- the reported total of 3,916 records;
- the result showing that all 3,916 records contained eight fields;
- the first and last returned records;
- the observed coverage from 26 November 2011 to 30 July 2026.

I confirmed that the generated methodology accurately represented my original
work and results.


## Add to `docs/ai_evidence.md`

````md
## EVIDENCE-AI-002 — Generating the OFAC candidate-announcement downloader

**Date:** 1 August 2026

**Related register entry:** AI-002

**Related file:** `src/download_ofac_sanctions.py`

**Related commit:** To be added after committing the downloader

### Context

I had already selected OFAC as the primary sanctions-event source and inspected
the Recent Actions archive.

My inspection established that:

- archive searches could be filtered by keyword and date;
- pagination used a predictable `page` parameter;
- dated announcement links could be extracted from the archive HTML;
- a 2012 search returned 41 candidate announcements;
- all 41 detail pages had extractable titles, dates and descriptions;
- searches from 2011 to 2026 returned 554 candidate announcements.

I then wrote the methodology describing how the raw candidate JSON should be
created.

### Exact prompt

> this is my methodology for creating the raw json file:
>
> ## OFAC data gathering and creation of the raw and interm files for sanctions events
> 1. look through the recent actions archives pages and use filters per year from 2011 to 2026 to gather all sources related to iran
> 2. there are 554 results so the title of each that mentions iran doesnt need clicking through but titles that dont include iran but be searched so see if they are related or not
> 3. create a download_ofac_sanctions.py to collect candidate announcement automatically. gather specifically, official release date, title, announcement body, optional press-release url, OFAC source url.
> 4. save the collected source info as a json file. dont add any sanctions classifications yet.
> 5. review each candidate announcement including records whose titles contain the word Iran to decide relevancy.
> 6. create an interm csv that contains: event_date, issuing_authority, action_type, sector, title, description, press_release_url, source_reference, relevant, classification_notes
> 7. assign classification such as tightening, relief, license, regulatory change and sector categories during manual review
>
> this is my methodlogy to create a raw json file from the link
> https://ofac.treasury.gov/recent-actions?search_api_fulltext=Iran&ra-start-date=01%2F01%2F2011&ra-end-date=12%2F31%2F2026&ra_year=
> i want to create the doanload_ofac_sanctions.py, create the script for me

### Exact response used

ChatGPT generated the complete contents of
`src/download_ofac_sanctions.py`.

The response included:

- project and output paths;
- archive and base URLs;
- the `Iran` search keyword;
- the 2011–2026 collection period;
- request timeout and delay settings;
- a regular expression for dated announcement links;
- `collect_year_links()` for archive pagination;
- `extract_text()` for cleaning extracted HTML text;
- `extract_candidate()` for extracting announcement fields;
- `main()` for collecting, validating and saving all records;
- collection metadata and yearly candidate counts;
- JSON output using UTF-8 and indentation;
- overwrite protection and final validation output.

The complete generated response is preserved in the conversation record. The
complete code used is also preserved in:

```text
src/download_ofac_sanctions.py

How the response was used

I copied the complete generated Python script into:
src/download_ofac_sanctions.py
The script was then run locally to create the fixed raw OFAC candidate dataset.

Division of work

My contribution included:

source selection;
source inspection;
archive-filter testing;
pagination testing;
HTML-structure inspection;
candidate-count checks;
defining the study period;
defining the required fields;
writing the collection methodology;
deciding that classification would occur only after raw collection.

ChatGPT's contribution was the complete implementation of the downloader based
on those requirements.

Verification

The generated script was executed locally.
The saved raw file contained:

554 candidate announcements;
554 unique OFAC source URLs;
0 duplicate source URLs;
0 missing titles;
0 missing release dates;
0 missing descriptions.

The yearly candidate counts matched the counts obtained during the earlier
archive inspection.

The first extracted record was dated 13 January 2011 and the final extracted
record was dated 30 July 2026, confirming coverage across the intended study
period.
