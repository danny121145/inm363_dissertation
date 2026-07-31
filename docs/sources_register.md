# Data Source Register

## USD/IRR Exchange Rate

**Variable:** United States dollar to Iranian rial exchange rate

**Provider:** TGJU

**Source type:** Historical exchange-rate archive

**Reason for selection:**

I selected TGJU because it provides historical observations for the USD/IRR
exchange rate over the period required for the project. I reviewed the source
and determined that its historical coverage and price fields were suitable
for constructing a weekly exchange-rate and volatility dataset.

**Available fields:**

- date;
- opening price;
- highest price;
- lowest price;
- closing price.

**Original frequency:** Daily observations

**Planned project frequency:** Weekly, using Friday-ending weeks

**Retrieval method:** TGJU archive API

**Raw-data treatment:**

The API response will be preserved in its original form in `data/raw/`.
Cleaning and transformation will be performed separately so that the original
download remains available for validation and reproducibility.

**Known limitations:**

- TGJU is not an official central-bank exchange-rate source.
- The precise market represented by the quoted rate must be stated clearly in
  the dissertation.
- Historical observations may contain missing dates or inconsistent OHLC
  relationships.
- The dataset must be validated before modelling.
- The availability and stability of the API endpoint may change.

