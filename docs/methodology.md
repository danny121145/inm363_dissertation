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

### Target-Safe Chronological Splits
The data is split by date into training, validation, and test sets. Because the targets use future returns, some rows at the end of each set cannot be used. For the four-week volatility target, the last four rows of each set are removed because they need data from the next four weeks. For the one-week squared-return target, the last row of each set is removed because it needs the following week’s return. This stops data from one set being used to calculate targets in another set and prevents information leakage.

## OFAC data gathering and creation of the raw and interm and processed files for sanctions events
1. look through the recent actions archives pages and use filters per year from 2011 to 2026 to gather all sources related to iran
2. there are 554 results so the title of each that mentions iran doesnt need clicking through but titles that dont include iran but be searched so see if they are related or not
3. create a download_ofac_sanctions.py to collect candidate announcement automatically. gather specifically, official release date, title, announcement body, optional press-release url, OFAC source url. 
4. save the collected source info as a json file. dont add any sanctions classifications yet.
5. review each candidate announcement including records whose titles contain the word Iran to decide relevancy. 
6. create an interm csv that contains: event_date, issuing_authority, action_type, sector, title, description, press_release_url, source_reference, relevant, classification_notes
7. assign classification such as tightening, relief, license, regulatory change and sector categories during manual review
8. now that script is created we can inspect each record and decide relevance, the action type, sector and any classification notes. these will all be stored in a csv.
9. once that csv is created we will create a prepare_ofac_data.py script, which will load the json and the csv, match them with a source reference, verify each candidate has a classification, retain only the relvant events and from that create the interim sanctions-event csv.
10. preapre_ofac_data.py is created now and from the interim csv has been created which has 506 relvant cases, 0 duplicates, 314 tightening, 61 license, 60 regulatory, 52 other and 19 relief. the csv has coulmns with event_date,title,description,press_release_url,source_reference,action_type,sector,classification_notes. 
11. assign each event a week ending friday, count events by action type, split multi sector labels, count sectors by week, create one row for every exchange rate week, weeks with no sanctions events = 0. 
12. the columns before initally inspecting: week_ending, sanctions_event_count, sanctions_tightening_count, sanctions_relief_count, sanctions_license_count, sanctions_regulatory_change_count, sanctions_other_count
13. after inspecting prepare_weekly_sanctions_data.py about 38 weeks were removed because they arent part of the calendar that we have in the tgju dataset, before the 2nd of december 2011. the action events are 293 tightening + 19 relief + 53 license + 52 regulatory_change + 51 other = 468 total events. next I will add the sectors as columns as well because the action events are considered the same even if one is banking related or nuclear related. 
14. the prepare weekly file has been updated with the sectors and all 8 sectors have been seen enough to be relevant. 

## Exploring the Weekly Sanctions Data
1. load the processed weekly sanctions dataset and parse the week_ending column as a date.
2. check the number of rows and the date range to confirm that the sanctions dataset matches the weekly USD/IRR dataset.
3. calculate the maximum weekly value for each sanctions feature to check whether any weeks contain unusually large numbers of sanctions events.
4. calculate how many weeks each sanctions feature is greater than zero, and the percentage of total weeks this represents. This is used to check how sparse each feature is.
5. calculate a correlation matrix between the sanctions features to check whether some variables contain very similar information.
6. the dataset contained 763 weekly observations from 2011-12-02 to 2026-07-31. Sanctions activity occurred in 347 weeks, or 45.48% of the dataset. Tightening was the most common action type, while relief was the most sparse.
7. the strongest correlations were between total sanctions events and tightening events (0.783), tightening events and government/IRGC sanctions (0.765), and oil/energy sanctions and shipping sanctions (0.604).
8. none of the correlations were close enough to 1 to suggest that two variables contain exactly the same information. Therefore, all sanctions features were kept in the processed dataset for now, with final feature selection to be completed later when all explanatory variables are combined.

## Preparing weekly brent oil price data
1. use the official weekly Europe Brent Spot Price FOB dataset from the U.S. Energy Information Administration (EIA). The downloaded raw CSV is kept unchanged in the raw data folder.
2. the EIA dataset is already weekly, so no daily-to-weekly resampling is required. Each weekly value represents the average of the daily Brent closing spot prices during that week and the date represents the week ending date.
3. remove the three metadata rows at the beginning of the downloaded CSV and keep the week date and Brent price columns.
4. rename the columns to week_ending and brent_price, parse the date column and sort the observations from oldest to newest.
5. check for missing values, duplicate weeks, invalid prices and the historical date range before further processing.
6. calculate brent_log_return using the change in the log of the weekly Brent price from the previous week. Calculate this before restricting the historical period so that the first week of the USD/IRR dataset can still have a valid oil-price change.
7. restrict the processed dataset to the USD/IRR study period from 2011-12-02 to 2026-07-31.
8. save week_ending, brent_price and brent_log_return as the processed weekly Brent dataset. The Brent log return will be considered as the main candidate oil feature when the final modelling dataset is created.
9. processed Brent dataset contains 766 weekly observations from 2011-12-02 to 2026-07-31 with no missing prices, missing log returns or duplicate weeks.

## Exploring the Weekly Brent Oil Data
1. load the processed weekly Brent oil dataset and parse the week_ending column as a date.
2. check the number of rows and date range to confirm that the processed dataset was created correctly.
3. use descriptive statistics on brent_price to show the average, standard deviation, minimum, quartiles and maximum weekly Brent price.
4. use descriptive statistics on brent_log_return to measure the average weekly oil-price change and how much weekly changes vary.
5. calculate skewness and kurtosis of brent_log_return to check whether the distribution contains uneven or extreme weekly movements.
6. identify the dates of the largest negative and positive Brent log returns.
7. the dataset contained 766 weekly observations from 2011-12-02 to 2026-07-31. Brent prices had a mean of 75.84 dollars per barrel and ranged from 14.24 to 127.40 dollars.
8. the average weekly Brent log return was close to zero, while the standard deviation was approximately 0.0505. The skewness of -0.819 suggests more extreme negative movements, while the excess kurtosis of 12.58 shows that unusually large weekly oil-price changes occurred more often than under a normal distribution.
9. the largest negative weekly return occurred on 2020-03-13 and the largest positive weekly return occurred on 2020-05-08. These results show that the Brent series contains occasional large movements, supporting the use of weekly oil-price changes as a candidate explanatory variable.

## Preparing Iran Inflation Data
1. load the raw IMF monthly CPI dataset and keep only Iran, CPI, All Items, Index and Monthly observations.
2. remove the extra IMF metadata/footer row and keep the monthly time period and CPI value.
3. check for missing CPI values, duplicate months and the available historical period.
4. convert the monthly time period into a date and sort the observations from oldest to newest.
5. calculate the year-on-year inflation rate by comparing each monthly CPI value with the CPI value from 12 months earlier.
6. because the raw series begins at 2010-M12, the first usable year-on-year inflation observation is 2011-M12, which covers the beginning of the USD/IRR study period.
7. apply a one-month lag to inflation before converting it to weekly data. For example, December inflation becomes available from January and is therefore used for the weekly observations in January. This prevents inflation information from being used during the same month it measures.
8. use the existing USD/IRR week_ending dates as the weekly calendar. For each Friday, use the latest lagged inflation value available by that date.
9. keep reference_month, cpi_index and inflation_yoy in the processed dataset for traceability, while inflation_yoy is the main candidate inflation feature for modelling.
10. the final processed dataset contains 763 weekly rows from 2011-12-02 to 2026-07-31. The first five weeks have missing inflation values because December 2011 inflation only becomes available from January 2012. These values are left missing rather than filled using future information.

## Exploring the Weekly Iran Inflation Data
1. load the processed weekly inflation dataset and check the number of rows, date range, usable observations and missing values.
2. use descriptive statistics on inflation_yoy to show the average, standard deviation, minimum, quartiles and maximum inflation rate.
3. calculate skewness and kurtosis to check the shape of the inflation distribution.
4. identify the reference months associated with the minimum and maximum inflation values.
5. the processed dataset contained 763 weekly observations, with 758 usable inflation values and 5 missing observations at the beginning caused by the one-month lag.
6. average year-on-year inflation was 30.49%, with a standard deviation of 16.75 percentage points. Inflation ranged from 5.68% to 88.57%.
7. skewness of 0.439 shows that the distribution is slightly weighted toward higher inflation values. Kurtosis of 0.235 suggests that the distribution is not strongly dominated by extreme observations.
8. the minimum inflation value was associated with December 2016, while the maximum was associated with June 2026. The inflation feature is therefore considered suitable to keep as a candidate explanatory variable for the later multivariate model.

## Merge Explanatory Variables

1. Use the processed weekly USD/IRR dataset as the master modelling calendar.
2. Before merging, inspect each processed dataset to confirm:
   * column names;
   * number of rows;
   * date range;
   * duplicate week_ending values;
   * missing values.
3. The datasets to be merged are:
   * weekly USD/IRR data;
   * weekly Brent oil data;
   * weekly Iran inflation data;
   * weekly OFAC sanctions data.
4. Merge the datasets using week_ending.
5. Use left joins with the USD/IRR dataset as the master dataset so that the final modelling table follows the exchange-rate observation calendar.
6. Use one-to-one merge validation so that the merge fails if duplicate weekly observations are unexpectedly present in either dataset.
7. Keep all prepared explanatory-variable columns in the merged source dataset at this stage. Final feature selection for the univariate and multivariate LSTM models is carried out separately in the next phase.
7. After merging, sort the dataset chronoligcally and check:
   * one row per week;
   * chronological order;
   * duplicate weeks;
   * final date range;
   * total number of rows
   * missing-value pattern;
   * whether any explanatory variable is unavailable for particular weeks.
8. Confirm that feature timing rules are preserved:
   * Brent data corresponds to the relevant Friday-ending week;
   * inflation uses the previously defined one-month availability lag;
   * sanctions use their official event dates;
   * no feature uses information that would only have been available after the forecast date.
9. Keep the future target columns separate from input feature selection. They must never be used as explanatory variables.
11. The completed merge produced 763 weekly observations covering 2 December 2011 to 31 July 2026, which matches the USD/IRR master dataset.
12. The final merged dataset contains no duplicate weeks and remains in chronological order.
13. Brent oil and sanctions variables contain no missing values after the merge, showing that all USD/IRR weeks were successfully matched to these explanatory datasets.
14. The remaining missing values are expected from the way the variables were constructed: 
* one missing log_return and squared_return observation at the beginning of the series because no previous exchange-rate observation exists
* four missing rolling_volatility_4w observations at the beginning because four historical weekly returns are required
* four missing target_volatility_4w observations at the end because four future weekly returns are required
* one missing target_squared_volatility_1w observation at the end because the following week's return is unavailable
* five missing inflation observations at the beginning because of the one-month inflation availability lag
15. Do not fill or remove these missing values during the merge stage. They are retained so that modelling-row selection can be handled explicitly when the modelling datasets and LSTM sequences are created.
16. Save the completed merged weekly dataset as the final source table for the later GARCH evaluation and LSTM experiments.

## Create Modelling Datasets
1. Use the final merged weekly dataset as the source for all modelling experiments.
2. Create separate modelling setups for:
   * GARCH;
   * univariate LSTM;
   * multivariate LSTM.
3. For GARCH, use weekly log_return only. The economic and sanctions variables are not included in the main GARCH model.
4. For the univariate LSTM, use historical exchange-rate variables only:
   * log_return;
   * squared_return;
   * rolling_volatility_4w.
5. For the multivariate LSTM, use the same exchange-rate variables together with:
   * brent_log_return;
   * inflation_yoy;
   * sanctions_event_count;
   * sanctions_tightening_count;
   * sanctions_relief_count.
6. Use a smaller sanctions feature set instead of using every sanctions column. The remaining sanctions variables stay in the merged dataset and can be tested later if needed.
7. Use the same targets for the LSTM experiments:
   * primary target: target_volatility_4w;
   * robustness target: target_squared_volatility_1w.
8. Do not use either target column as an input feature.
9. Remove rows only when the variables needed for that experiment are missing.
10. For GARCH, remove the first row where log_return is missing.
11. For the univariate LSTM, use rows where all selected exchange-rate features and the chosen target are available.
12. For the multivariate LSTM, also require the selected Brent, inflation and sanctions variables to be available.
13. Do not fill the first five missing inflation values. These weeks are excluded naturally because the inflation data was not yet available under the one-month lag rule.
14. For the primary target, remove the final four weeks where the future four-week volatility target is unavailable.
15. For the robustness target, remove the final week where the next-week squared return is unavailable.
16. Keep all modelling data in chronological order and do not randomly shuffle the time series.
17. The final usable GARCH dataset contains 762 weekly observations from 9 December 2011 to 31 July 2026.
18. The univariate LSTM dataset contains:
    * 755 observations for the primary target, covering 30 December 2011 to 3 July 2026;
    * 758 observations for the robustness target, covering 30 December 2011 to 24 July 2026.
19. The multivariate LSTM dataset contains:
    * 754 observations for the primary target, covering 6 January 2012 to 3 July 2026;
    * 757 observations for the robustness target, covering 6 January 2012 to 24 July 2026.
20. All final modelling datasets contain no duplicate weeks and no missing values in the variables required for each experiment.
21. Recreate the train, validation and test splits using these final usable modelling datasets so that the splits match the final feature set and target.
22. Keep the same time-based split approach across comparable experiments so that model results can be compared fairly.
23. Do not create unnecessary copies of the full dataset. Keep one merged source dataset and define the required feature lists in code for each experiment.
24. The final modelling setups are:
    * GARCH: log_return;
    * univariate LSTM: historical USD/IRR features;
    * multivariate LSTM: historical USD/IRR features plus Brent oil, inflation and selected sanctions variables.

## Create Final Chronological Splits
1. Use fixed calendar dates for the train, validation and test periods so that comparable experiments use the same time boundaries.
2. Use the following main calendar split:
   * training period: up to 27 December 2019;
   * validation period: 3 January 2020 to 30 December 2022;
   * test period: from 6 January 2023 onward.
3. Keep all observations in chronological order. Do not randomly shuffle the time-series data.
4. For GARCH, use the full return observations available within each calendar split because GARCH is fitted directly to historical weekly returns.
5. For the primary LSTM target, remove the final four observations from the training and validation periods because target_volatility_4w uses the following four weekly returns.
6. This prevents primary-target values in one split from using exchange-rate returns belonging to the following split.
7. For the robustness target, remove the final observation from the training and validation periods because target_squared_volatility_1w uses the following week's squared return.
8. Do not remove additional observations from the test datasets. Rows where the required future target cannot be calculated have already been removed when the modelling datasets were created.
9. The final GARCH splits contain:
   * training: 420 observations from 9 December 2011 to 27 December 2019;
   * validation: 156 observations from 3 January 2020 to 30 December 2022;
   * test: 186 observations from 6 January 2023 to 31 July 2026.
10. The final univariate LSTM splits for the primary target contain:
    * training: 413 observations from 30 December 2011 to 29 November 2019;
    * validation: 152 observations from 3 January 2020 to 2 December 2022;
    * test: 182 observations from 6 January 2023 to 3 July 2026.
11. The final univariate LSTM splits for the robustness target contain:
    * training: 416 observations from 30 December 2011 to 20 December 2019;
    * validation: 155 observations from 3 January 2020 to 23 December 2022;
    * test: 185 observations from 6 January 2023 to 24 July 2026.
12. The final multivariate LSTM splits for the primary target contain:
    * training: 412 observations from 6 January 2012 to 29 November 2019;
    * validation: 152 observations from 3 January 2020 to 2 December 2022;
    * test: 182 observations from 6 January 2023 to 3 July 2026.
13. The final multivariate LSTM splits for the robustness target contain:
    * training: 415 observations from 6 January 2012 to 20 December 2019;
    * validation: 155 observations from 3 January 2020 to 23 December 2022;
    * test: 185 observations from 6 January 2023 to 24 July 2026.
14. These split rules are kept fixed before model development so that GARCH, univariate LSTM and multivariate LSTM experiments can be compared using consistent out-of-sample periods.

## Final Model Scope
1. The original modelling plan included three models:
   * GARCH;
   * univariate LSTM;
   * multivariate LSTM.
2. After completing the data-preparation stage, the modelling scope was reduced to:
   * GARCH;
   * multivariate LSTM.
3. The univariate LSTM was removed to keep the remaining modelling work manageable and allow enough time for model testing, repeated runs and error checking.
4. GARCH remains the traditional statistical benchmark and uses historical weekly USD/IRR log returns.
5. The multivariate LSTM uses historical exchange-rate information together with the selected explanatory variables:
   * log_return;
   * squared_return;
   * rolling_volatility_4w;
   * brent_log_return;
   * inflation_yoy;
   * sanctions_event_count;
   * sanctions_tightening_count;
   * sanctions_relief_count.
6. Both models are evaluated using the primary future four-week volatility experiment and the one-week squared-return robustness experiment.
7. Removing the univariate LSTM means the study will not separately test whether the explanatory variables improve an LSTM compared with an exchange-rate-only LSTM.
8. Instead, the main comparison focuses on whether the multivariate machine-learning approach provides improved volatility forecasting performance compared with the traditional GARCH benchmark.
9. The reduced model scope allows more time for model validation, repeated LSTM runs, reproducibility checks and a more complete comparison of the final model results.

## Implement GARCH Benchmark
1. Use weekly USD/IRR log_return as the input series for the GARCH benchmark.
2. Use the fixed training period ending on 27 December 2019.
3. Scale weekly log returns by 100 before fitting the GARCH models so that the model works with percentage-return units.
4. Start with a small set of standard GARCH specifications rather than a large model search.
5. Test the following candidate models:
   * GARCH(1,1) with Normal innovations;
   * GARCH(1,1) with Student’s t innovations;
   * GARCH(1,2) with Normal innovations;
   * GARCH(1,2) with Student’s t innovations;
   * GARCH(2,1) with Normal innovations;
   * GARCH(2,1) with Student’s t innovations.
6. Use a constant mean specification for all candidate models so that the comparison focuses on the volatility specification and innovation distribution.
7. Compare the candidate models using:
   * log-likelihood;
   * AIC;
   * BIC;
   * convergence status.
8. All six candidate models converged successfully.
9. The Student’s t models performed clearly better than the equivalent Normal models based on log-likelihood, AIC and BIC.
10. The best in-sample AIC was produced by GARCH(1,2) with Student’s t innovations:
    * log-likelihood: -873.586;
    * AIC: 1759.172;
    * BIC: 1783.414.
11. GARCH(1,1) with Student’s t innovations produced a slightly lower BIC of 1783.287, so both GARCH(1,1)-t and GARCH(1,2)-t were taken forward to validation rather than selecting a model from in-sample fit alone.
12. Use expanding-window validation. For each validation week:
    * fit the GARCH model using all weekly returns available up to that forecast date;
    * produce forecasts using information available at that date only;
    * move forward one week and include the newly observed return in the next fit.
13. For the primary experiment, produce four weekly variance forecasts and convert them into a four-week volatility forecast by taking the square root of the average forecast variance.
14. Convert the primary forecast back from percentage-return units to decimal-return units before comparing it with target_volatility_4w.
15. For the robustness experiment, use the one-week-ahead GARCH variance forecast and convert it back to decimal squared-return units before comparing it with target_squared_volatility_1w.
16. Keep the same target-safe validation rules used when creating the modelling datasets:
    * primary validation ends on 2 December 2022 so the following four weeks remain inside the validation period;
    * robustness validation ends on 23 December 2022 so the following week remains inside the validation period.
17. Evaluate validation forecasts using MAE and RMSE.
18. Validation results for the primary target were:
    * GARCH(1,1)-t — MAE: 0.022203, RMSE: 0.028575;
    * GARCH(1,2)-t — MAE: 0.022003, RMSE: 0.028345.
19. Validation results for the robustness target were:
    * GARCH(1,1)-t — MAE: 0.002201, RMSE: 0.004005;
    * GARCH(1,2)-t — MAE: 0.002195, RMSE: 0.004030.
20. The validation results were very similar, but GARCH(1,2) with Student’s t innovations performed slightly better overall and also had the best training AIC.
21. Select GARCH(1,2) with Student’s t innovations as the final GARCH specification.
22. Keep the test period untouched during model selection. The selected GARCH model will next be evaluated on the final test period using the same forecasting approach.

## Final GARCH Test Evaluation
1. After selecting GARCH(1,2) with Student’s t innovations using the training and validation periods, evaluate the selected model on the previously unused test period.
2. Keep the same expanding-window forecasting method used during validation.
3. For each test week, fit the GARCH model using all weekly returns available up to that forecast date and then produce the required future variance forecasts.
4. Do not use test performance to change the selected GARCH specification.
5. For the primary experiment, evaluate 182 test forecasts against target_volatility_4w.
6. The final primary-target GARCH results were:
   * MAE: 0.019744;
   * RMSE: 0.025903.
7. For the robustness experiment, evaluate 185 test forecasts against target_squared_volatility_1w.
8. The final robustness-target GARCH results were:
   * MAE: 0.001966;
   * RMSE: 0.003844.
9. These results are kept as the final GARCH benchmark for comparison with the multivariate LSTM.

## Prepare LSTM Sequences and Scaling
1. Use the final multivariate modelling dataset for the LSTM experiments.
2. Use the following eight input features:
   * log_return;
   * squared_return;
   * rolling_volatility_4w;
   * brent_log_return;
   * inflation_yoy;
   * sanctions_event_count;
   * sanctions_tightening_count;
   * sanctions_relief_count.
3. Create separate LSTM datasets for:
   * the primary target target_volatility_4w;
   * the robustness target target_squared_volatility_1w.
4. Use an initial sequence length of 12 weeks.
5. For each prediction date, use the previous 12 weeks of input features as the LSTM sequence.
6. The target for the current prediction date is kept separate from the 12-week input sequence.
7. For the primary experiment, the target at week t represents volatility over the following four weeks.
8. For the robustness experiment, the target at week t represents the squared return of the following week.
9. Do not include future target values inside the input sequences.
10. Allow validation and test sequences to use earlier historical observations as input context when those observations occurred before the prediction date.
11. This means the first validation and test predictions do not need to lose 12 weeks of data simply because their historical input window begins in the previous split.
12. Skip any sequence where one or more required feature values or the selected target are missing.
13. The primary experiment produced:
    * 400 training sequences;
    * 152 validation sequences;
    * 182 test sequences.
14. The robustness experiment produced:
    * 403 training sequences;
    * 155 validation sequences;
    * 185 test sequences.
15. Each LSTM input has the shape:
    * 12 historical weeks;
    * 8 input features.
16. Scale the LSTM input features using StandardScaler.
17. Fit the feature scaler using training data only.
18. Use the fitted training scaler to transform the validation and test inputs without refitting it.
19. Scale the primary and robustness targets separately because they represent different measures and have different numerical ranges.
20. Fit each target scaler using the relevant training target only.
21. Use the same fitted target scaler to transform validation and test targets.
22. After scaling, the training features have approximately zero mean and unit standard deviation.
23. Keep the fitted target scalers so that LSTM predictions can later be converted back to the original target units.
24. Calculate final MAE and RMSE after converting predictions back to their original units so that the LSTM results can be compared directly with the GARCH benchmark.
25. Keep the 12-week sequence length as the initial baseline. Alternative sequence lengths can be tested later during controlled model experiments.

## Implement Basic Multivariate LSTM
1. Use the prepared multivariate LSTM sequences with a 12-week lookback and 8 input features.
2. Build a simple baseline LSTM before carrying out any large hyperparameter search.
3. Use one LSTM layer with:
   * 32 hidden units;
   * one layer;
   * a linear output layer.
4. Use the same basic architecture for both the primary and robustness targets so that the initial experiments are directly comparable.
5. Use:
   * Adam optimizer;
   * learning rate of 0.001;
   * mean squared error loss;
   * maximum of 100 epochs;
   * early stopping patience of 10 epochs.
6. Set the random seed from config.py before training to improve reproducibility.
7. Train the LSTM using the training sequences and monitor performance using the validation sequences.
8. Save the model state with the lowest validation loss rather than keeping the model from the final training epoch.
9. Stop training when validation loss does not improve for 10 consecutive epochs.
10. For the primary target, the best validation loss was reached at approximately epoch 41 and training stopped at epoch 51.
11. Convert the scaled predictions back to the original target units before calculating MAE and RMSE.
12. The baseline primary-target LSTM results were:
* validation MAE: 0.017819;
* validation RMSE: 0.024623;
* test MAE: 0.018657;
* test RMSE: 0.023018.
13. For the robustness target, training stopped at epoch 34 with a best validation loss of 0.412362.
14. The baseline robustness-target LSTM results were:
* validation MAE: 0.002107;
* validation RMSE: 0.003802;
* test MAE: 0.002077;
* test RMSE: 0.003678.
15. Save the validation and test forecasts with:
* week_ending;
* actual target value;
* predicted target value.
16. Treat these LSTM results as baseline runs rather than final model results because the LSTM will later be repeated across different random seeds and controlled configurations.
17. Do not use the test results to tune the LSTM. Final tuning and repeated runs will be based on the training and validation setup before the final comparison is made.

## Validate LSTM Reproducibility and Data Alignment
1. Add checks before experiment tracking to confirm that the LSTM pipeline does not contain data leakage or alignment errors.
2. Use a fixed random seed for:
   * Python;
   * NumPy;
   * PyTorch.
3. Use deterministic PyTorch behaviour where possible so that repeated runs with the same seed can be reproduced.
4. Check that the LSTM feature list contains no duplicate feature names.
5. Confirm that neither target_volatility_4w nor target_squared_volatility_1w appears in the LSTM input features.
6. Confirm that all expected multivariate feature columns are present before creating sequences.
7. The final LSTM feature set contains:
   * log_return;
   * squared_return;
   * rolling_volatility_4w;
   * brent_log_return;
   * inflation_yoy;
   * sanctions_event_count;
   * sanctions_tightening_count;
   * sanctions_relief_count.
8. Check that every LSTM sequence has:
   * 12 historical weeks;
   * 8 input features;
   * one correctly aligned target;
   * one corresponding target date.
9. Confirm that the number of input sequences, targets and dates is the same for every train, validation and test dataset.
10. Keep the previously defined target-safe split boundaries:
    * primary training targets end on 29 November 2019;
    * primary validation targets end on 2 December 2022;
    * robustness training targets end on 20 December 2019;
    * robustness validation targets end on 23 December 2022.
11. Check that no training or validation target crosses into the following time split.
12. Fit all feature and target scalers using training data only.
13. Apply the fitted training scalers to validation and test data without refitting them.
14. Check that scaled train, validation and test inputs contain no missing values.
15. Confirm that saved prediction dates exactly match the expected validation and test target dates.
16. Convert model predictions back to the original target units before calculating MAE and RMSE.
17. During the checks, a duplicated log_return feature was identified in the LSTM feature list and replaced with the intended squared_return feature.
18. After correcting the feature list, recreate the LSTM sequences and rerun both baseline LSTM experiments.
19. The corrected primary-target LSTM produced:
    * best validation loss: 0.768636;
    * early stopping at epoch 48;
    * validation MAE: 0.017790;
    * validation RMSE: 0.024846;
    * test MAE: 0.018096;
    * test RMSE: 0.023109.
20. The corrected robustness-target LSTM produced:
    * best validation loss: 0.409958;
    * early stopping at epoch 34;
    * validation MAE: 0.002111;
    * validation RMSE: 0.003791;
    * test MAE: 0.002029;
    * test RMSE: 0.003675.
21. Both corrected LSTM pipelines passed the prediction-count and prediction-date alignment checks.
22. Save the corrected validation and test forecasts for later comparison with the GARCH benchmark.
23. Treat these LSTM runs as baseline results only. Final LSTM conclusions will be based on repeated and controlled experiments tracked after Wandb is integrated.

## Track and Tune LSTM Experiments with Weights & Biases
1. Integrate Weights & Biases (W&B) into the LSTM training script to track model configurations and experiment results.
2. Log the following configuration values for every run:
   * target type;
   * sequence length;
   * hidden size;
   * learning rate;
   * maximum epochs;
   * patience;
   * random seed;
   * number of input features.
3. Log training loss and validation loss after every epoch.
4. Log the final:
   * best validation loss;
   * validation MAE;
   * validation RMSE;
   * test MAE;
   * test RMSE;
   * early stopping epoch.
5. Refactor the LSTM script so that the same file can run either the primary or robustness target using a command-line argument.
6. Add command-line arguments for:
   * target;
   * random seed;
   * hidden size;
   * learning rate.
7. Use fixed random seeds so that the effect of different neural-network initialisations can be measured without changing the dataset, features or train-validation-test splits.
8. Use five seeds for the baseline stability experiments:
   * 1;
   * 7;
   * 21;
   * 42;
   * 99.
9. The original baseline configuration used:
   * sequence length = 12 weeks;
   * hidden size = 32;
   * learning rate = 0.001;
   * maximum epochs = 100;
   * patience = 10.
10. For the primary target, the five baseline runs produced a mean validation MAE of 0.018084 and a mean validation RMSE of 0.025322.
11. The standard deviation across the five primary baseline runs was:
    * MAE = 0.000350;
    * RMSE = 0.000343.
12. For the robustness target, the five baseline runs produced a mean validation MAE of 0.002091 and a mean validation RMSE of 0.003818.
13. The standard deviation across the five robustness baseline runs was:
    * MAE = 0.000094;
    * RMSE = 0.000015.
14. These repeated runs showed that both baseline LSTM models were reasonably stable across different random initialisations.
15. Keep hyperparameter tuning intentionally small because the purpose of the dissertation is to compare GARCH and LSTM forecasting performance rather than perform a large neural-network architecture search.
16. Use the primary target for the small controlled tuning experiment.
17. Test three hidden sizes while keeping the learning rate fixed at 0.001 and using seed 42:
    * 16;
    * 32;
    * 64.
18. The validation results were:
    * hidden size 16: MAE 0.017543, RMSE 0.024665;
    * hidden size 32: MAE 0.017790, RMSE 0.024846;
    * hidden size 64: MAE 0.018424, RMSE 0.025211.
19. Hidden size 16 produced the strongest primary validation performance and was therefore carried forward to the learning-rate experiment.
20. Test three learning rates with hidden size 16 and seed 42:
    * 0.0005;
    * 0.001;
    * 0.005.
21. The validation results were:
    * learning rate 0.0005: MAE 0.017540, RMSE 0.025531;
    * learning rate 0.001: MAE 0.017543, RMSE 0.024665;
    * learning rate 0.005: MAE 0.017750, RMSE 0.024705.
22. Learning rate 0.001 produced the lowest validation RMSE and best validation loss and was retained.
23. Run the selected primary configuration, hidden size 16 and learning rate 0.001, across all five seeds.
24. The selected primary configuration produced:
    * mean validation MAE = 0.017684;
    * standard deviation MAE = 0.000267;
    * mean validation RMSE = 0.024734;
    * standard deviation RMSE = 0.000209.
25. This was better than the original primary baseline on both mean validation MAE and RMSE and also showed lower variation across seeds.
26. The final primary LSTM configuration was therefore selected as:
    * sequence length = 12;
    * hidden size = 16;
    * learning rate = 0.001;
    * patience = 10;
    * maximum epochs = 100.
27. Apply the same hidden-size-16 configuration to the robustness target across the five seeds to check whether the primary tuning decision also improves the robustness target.
28. The hidden-size-16 robustness configuration produced:
    * mean validation MAE = 0.002107;
    * standard deviation MAE = 0.000124;
    * mean validation RMSE = 0.003833;
    * standard deviation RMSE = 0.000018.
29. This was slightly worse than the original hidden-size-32 robustness baseline, which produced:
    * mean validation MAE = 0.002091;
    * standard deviation MAE = 0.000094;
    * mean validation RMSE = 0.003818;
    * standard deviation RMSE = 0.000015.
30. The final robustness LSTM configuration was therefore retained as:
    * sequence length = 12;
    * hidden size = 32;
    * learning rate = 0.001;
    * patience = 10;
    * maximum epochs = 100.
31. Use validation results only for model and hyperparameter selection.
32. Do not select a final model based on whichever individual random seed gives the lowest error.
33. Treat repeated-seed results as evidence of model stability and report average performance and variation across runs.
34. Carry the selected primary and robustness configurations forward to the final comparison with the fixed GARCH benchmark.

## Final LSTM and GARCH Evaluation
1. Use the model configurations selected using validation performance for the final test comparison.
2. Keep the previously selected GARCH benchmark fixed as GARCH(1,2) with Student's t-distributed errors.
3. Use the final primary LSTM configuration:
   * sequence length = 12 weeks;
   * hidden size = 16;
   * learning rate = 0.001;
   * maximum epochs = 100;
   * patience = 10.
4. Use the final robustness LSTM configuration:
   * sequence length = 12 weeks;
   * hidden size = 32;
   * learning rate = 0.001;
   * maximum epochs = 100;
   * patience = 10.
5. Evaluate each selected LSTM configuration across five random seeds:
   * 1;
   * 7;
   * 21;
   * 42;
   * 99.
6. Use the same train, validation and test periods for every repeated run.
7. Do not change the feature set, target definition or scaling method between repeated runs.
8. Calculate MAE and RMSE in the original target units after reversing the target scaling.
9. Report the LSTM test results using the mean and standard deviation across the five seeds rather than selecting the best individual seed.
10. The final primary LSTM test performance was:
    * MAE = 0.017671 ± 0.000529;
    * RMSE = 0.023306 ± 0.000260.
11. The fixed GARCH primary test performance was:
    * MAE = 0.019744;
    * RMSE = 0.025903.
12. The LSTM therefore produced lower MAE and RMSE than GARCH for the primary four-week volatility target.
13. The final robustness LSTM test performance was:
    * MAE = 0.002021 ± 0.000144;
    * RMSE = 0.003685 ± 0.000021.
14. The fixed GARCH robustness test performance was:
    * MAE = 0.001966;
    * RMSE = 0.003844.
15. For the robustness target, GARCH produced a slightly lower MAE, while the LSTM produced a lower RMSE.
16. Treat the four-week future volatility target as the primary result because it represents the main forecasting task defined.
17. Treat the next-week squared-return target as a robustness check used to test whether the overall findings remain similar under a different definition of future volatility.
18. Do not interpret the robustness result as showing that one model is better on every metric.
19. Use the primary and robustness results together when answering the research question.
20. Interpret the final evidence as showing that the multivariate LSTM improved forecasting performance over the GARCH benchmark for the main four-week volatility target, while the robustness analysis produced mixed results depending on the evaluation metric.

