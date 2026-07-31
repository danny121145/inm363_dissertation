## Raw Exchange-Rate Data Acquisition and Initial Inspection

Historical USD/IRR exchange-rate data were retrieved from the TGJU API using
the `price_dollar_rl` market indicator endpoint:


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
1. Define the location of the raw TGJU JSON file and the location where the cleaned interim CSV file will be saved.
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

## daily data prep results
The cleaning process created an interim dataset with 3,916 daily observations, covering the period from 26 November 2011 to 30 July 2026.

There were no duplicate dates, and none of the required fields had missing values. However, the change column had 179 missing values, and the change_percent column had 190 missing values. These missing values were accepted because these columns are not needed to calculate returns or volatility later.

Eight rows had problems with the open, high, low, and close values. In some cases, the opening or closing price was outside the reported daily low and high range. In other cases, the reported low price was higher than the high price.

These rows were kept in the dataset and marked as ohlc_valid=False. They were not removed or changed because they may still be useful later, and keeping them makes it possible to compare them with the original raw data.

## Weekly Dataset and Target Variable Construction

1. The cleaned exchange-rate dataset initially contains one observation for
   each available day. It must therefore be converted into a weekly dataset
   for the modelling stage.
2. Load the cleaned interim CSV file and retain the Gregorian date and closing
   price columns.
3. Sort the daily observations in chronological order.
4. Divide the daily observations into weeks ending on Friday. For each week,
   select the latest available daily closing price. When no observation exists
   on the Friday itself, use the most recent available observation from that
   week.
5. Record the date of the daily observation selected for each week in an
   observation_date column. This distinguishes the Friday week-ending label
   from the date on which the selected closing price was actually observed.
6. Calculate the weekly logarithmic return as:
   log_return = log(current weekly close / previous weekly close)
7. Calculate squared_return by squaring the weekly log return. This removes
   the direction of the movement and measures the size of the movement during
   that week.
8. Calculate rolling_volatility_4w as the standard deviation of the current
   weekly log return and the previous three weekly log returns. This represents
   volatility observed over the most recent four weeks.
9. Create target_volatility_4w as the primary forecasting target. For each
   week, this is the standard deviation of the following four weekly log
   returns.
10. Create target_squared_volatility_1w as the robustness forecasting target.
    For each week, this is the squared log return from the following week.
11. Retain missing values created at the beginning and end of the dataset where
    the required previous or future returns are unavailable.

## Exploring the Weekly Data and Assessing the Volatility Target
1. first we load the processed weekly dataset and parse the week_ending and observation_date columns as dates.
2. drop the log returns that are missing
3. print all the weekly observations and usable log returns
4. print the first and last weeks to show historical period and the datasheet was created correctly
5. use .describe on the variable with dropped empty log returns to show count (value of non-missing weekly returns), mean (average weekly log return, positive means the rates increased on average and negative suggests otherwise), standard deviation (measures how much weekly returns vary around their average, larger sd means higher volatily and smaller means the opposite), minimum and maximum (minimum is the largest negative weekly return and maximum is the largest positive weekly return)
6. use .skew on the same variable to show if the return distribuition is more balanced or has more extreme movements on either side. close to 0 means balanced, positive means large positive returns are more common or extreme, negative means large negative returns are more common or extreme
7. use .kurt on the same variable to show if the return has common extreme movements. if close to zero then the distrbuition has a similar level of extreme observations to a normal distribution. A large positive value suggests that the dataset contains more extreme weekly returns than would normally be expected under a normal distribution. High kurtosis could support the use of GARCH models because they are designed for periods of large movements 
8. then show the weeks with the largest fall in the exchange rate return and the largest rise. 
9. after creating the explore_weekly_data.py the returned stats were:
Descriptive statistics of weekly dataset
rows: 763
usable returns: 762
date range: 2011-12-02 to 2026-07-31

Log-return descriptive statistics:
count    762.000000
mean       0.006500
std        0.038917
min       -0.308751
25%       -0.006991
50%        0.002766
75%        0.020355
max        0.199920

Additional statistics:
Skewness: -0.220024
Excess kurtosis: 9.245460
Minimum return date: 2018-10-05
Maximum return date: 2018-09-07

10. The positive mean weekly log return of 0.0065 indicates that the USD/IRR rate increased on average. Since the rate measures Iranian rials per US dollar, this corresponds to an average depreciation of the rial against the dollar, the standard deviation of weekly log returns was 0.0389, approximately 3.89%, indicating substantial variation around the average weekly return. the quartiles show half of all weekly returns were between -0.7% and 2.04%, so most weeks movements were moderate but some weeks experienced much larger changes. both extremes happened within weeks of each other meaning some events could have occured here could be checked later. The skewness of −0.220 indicates a slightly heavier or longer negative tail, suggesting that extreme negative returns were somewhat more pronounced than extreme positive returns. kurtosis has an incredibly large number, meaning extreme weekly movements occurred much more frequently, or were much larger, than would be expected under a normal distribution.
11. due to these resutls we need more tests to find out if large movements occur randomly or in clusters. we use a Ljung-box test on returns to see if the weekly returns are related to previous weekly returns. use 5, 10, 20 lags. 
12. use p-values to determine auto-correlation, higher than 0.05 means no strong evidence of auto correlation. lower than is the opposite. If the returns are not autocorrelated, this would mean that past returns do not strongly predict future returns in a simple linear way. If they are autocorrelated, the return equation may need to include additional terms, such as autoregressive lags, before modelling volatility.
13. do a ljung box test on squared returns. squaring it removes direction and focuses on size. this test ask if large exchange-rate movements tend to be followed by other large movements. with this we can find volatilty clustering which means calm weeks are followed by calm weeks and high volatility weeks are followed by high volatility weeks. 
14. use the same p-value as the previous test to determine if volatility is determined over time or not. If the squared-return test is significant while the return test is not, it would mean that the direction of returns may be difficult to predict, but the size of future movements may still depend on recent volatility.
15. use an ARCH LM test to check if variance of returns changes over time. use10 lags. use same p-value scores as previous tests. if p-value is low we would need the GARCH model because it shows that variance is not constant over time. 
16. after adding the Ljung box and ARCH LM test these are the results:
Ljung-Box test for autocorrelation of returns:
      lb_stat  lb_pvalue
5    3.484374   0.625753
10  21.382636   0.018578
20  26.989824   0.135551

Ljung-Box test for autocorrelation of squared returns:
       lb_stat     lb_pvalue
5   160.285392  8.604623e-33
10  224.216129  1.399766e-42
20  255.964852  7.143730e-43

ARCH LM test:
ARCH LM statistic: 124.485615
ARCH LM p-value: 0.000000

17. for the autocorrelation of returns at lag 5, the null hypothesis of no autocorrelation was not rejected. At lag 10, it was rejected at the 5% level, indicating evidence of joint autocorrelation across the first ten lags. At lag 20, the null was not rejected. The evidence of return autocorrelation is therefore limited and not consistent across the tested lag lengths. all the p-values for the squared reuturns are extremely small, this means there is very strong evidence that squared returns are autocorrelated. Because squared returns represent the size of movements, this suggests that large exchange-rate changes tend to be followed by other large changes, while smaller changes tend to occur near other smaller changes. For the ARCH LM the p-value is far below 0.05, so the null hypothesis of no ARCH effects is rejected. This means that current volatility is related to previous return shocks. 
18. analysis: 
The results suggest that the weekly returns themselves have only limited and inconsistent autocorrelation. Therefore, past return direction does not appear to provide strong and stable information about future return direction.
In contrast, the squared returns show extremely strong autocorrelation at all tested lag lengths. The ARCH LM test also strongly rejects constant variance. Together, these results provide clear evidence of volatility clustering and ARCH effects.
Therefore, the main predictable feature of the series is not necessarily whether the USD/IRR rate will rise or fall, but whether the next period is likely to remain relatively calm or volatile. These findings provide statistical support for using a GARCH model as the traditional volatility forecasting model.
19. Based on the strong autocorrelation in squared returns and the significant ARCH LM result, use future volatility rather than return direction as the modelling target.
20. Use target_volatility_4w as the primary forecasting target. It represents the standard deviation of the following four weekly log returns.
21. Use target_squared_volatility_1w as a robustness target. It represents the squared log return of the following week.
22. Use rolling_volatility_4w and squared_return as historical volatility measures. These variables describe volatility already observed and do not contain future information.
23. Do not use either forecasting-target column as a model input. They are the outcomes that the models will attempt to predict.
24. Descriptive statistics were then calculated for the historical four-week volatility measure and both forecasting targets.
The results were:

rolling_volatility_4w:
count    759.000000
mean       0.027649
std        0.027327
min        0.000262
25%        0.008927
50%        0.019496
75%        0.036681
max        0.218188

target_volatility_4w:
count    759.000000
mean       0.027649
std        0.027327
min        0.000262
25%        0.008927
50%        0.019496
75%        0.036681
max        0.218188

target_squared_volatility_1w:
count    762.000000
mean       0.001555
std        0.005052
min        0.000000
25%        0.000020
50%        0.000176
75%        0.000976
max        0.095327

25. rolling_volatility_4w and target_volatility_4w have identical
descriptive statistics because they contain the same calculated
four-week volatility values at different dates. The historical variable
places each value at the end of the four-week period, while the target
places it four weeks earlier so that it represents future volatility.

26. The one-week squared-volatility target has a different scale because it is
based on one squared weekly return rather than the standard deviation of
four weekly returns. Its values will therefore be evaluated separately
from the primary target.