# inm363_dissertation

## Research Question

Can machine-learning time-series models provide improved performance compared
with traditional statistical models when analysing exchange-rate volatility in
Iran?

## Project Aim

This project compares a traditional GARCH model with an LSTM neural network for
forecasting weekly USD/IRR exchange-rate volatility.

The study also examines whether a small number of economic, institutional, and
geopolitical variables improve volatility forecasts beyond information contained
in historical exchange-rate movements alone.

## Planned Models

- GARCH model as the traditional econometric benchmark
- Univariate LSTM using historical exchange-rate information
- Multivariate LSTM using exchange-rate information together with selected
  explanatory variables

## Planned Explanatory Variables

The final modelling dataset is expected to include a limited number of variables
such as:

- USD/IRR exchange-rate returns
- oil-price changes
- inflation or related macroeconomic indicators
- sanctions-related events
- major policy changes
- periods of economic disruption

The exact variables will depend on data availability, frequency, and quality.

## Forecasting Targets

The project focuses on forecasting volatility rather than predicting the exact
future exchange-rate level.

The primary forecasting target is:

- target_volatility_4w: the standard deviation of weekly USD/IRR log returns
  over the following four weeks

The robustness target is:

- target_squared_volatility_1w: the squared USD/IRR log return for the
  following week

The processed dataset also contains historical volatility measures:

- squared_return
- rolling_volatility_4w

These describe volatility already observed and may be used as historical model
inputs. The forecasting-target columns will not be used as input features.

## Evaluation Plan

The models will be compared using out-of-sample forecasts over the same test
period.

Planned evaluation methods include:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- additional volatility-forecast loss measures where appropriate
- statistical testing of differences in forecast performance

The time series will be split chronologically rather than randomly.

## Current Data Source

The current USD/IRR source is the TGJU historical free-market exchange-rate API.

The raw response contains daily opening, low, high and closing prices, absolute
and percentage change values, Gregorian dates, and Jalali dates.

The fixed raw-data snapshot was retrieved on 31 July 2026 and contains 3,916
daily records covering 26 November 2011 to 30 July 2026.

## Current Processed Dataset

The daily data were cleaned and converted into a weekly dataset using
Friday-ending weekly periods.

The weekly dataset contains:

- 763 weekly observations
- coverage from 2 December 2011 to 31 July 2026
- no missing weekly closing prices
- no duplicate week-ending dates
- one expected missing initial log return
- historical and future volatility variables

## Work Completed

- Created the project repository and folder structure
- Recorded the data source and retrieval
- Downloaded and preserved the raw TGJU JSON response
- Cleaned and validated the daily exchange-rate data
- Retained and flagged eight source records with invalid OHLC relationships
- Converted the daily data into Friday-ending weekly observations
- Calculated weekly logarithmic returns
- Conducted descriptive return analysis
- Applied Ljung–Box tests to returns and squared returns
- Applied the ARCH LM test
- Identified strong evidence of volatility clustering and ARCH effects
- Added historical volatility measures
- Added the primary four-week volatility forecasting target
- Added the one-week squared-volatility robustness target
- Manually validated the alignment of both forecasting targets

## Project Structure

```text
data/
  raw/
    usd_irr_tgju_history_raw.json

  interim/
    usd_irr_tgju_daily.csv

  processed/
    usd_irr_tgju_weekly.csv

docs/
  sources_register.md
  methodology.md
  ai_evidence.md
  ai_use_register.md
  feature_register.md

src/
  download_tgju_data.py
  prepare_tgju_data.py
  prepare_weekly_data.py
  explore_weekly_data.py

results/
  Model outputs, evaluation tables, and figures

tests/
  Automated tests



