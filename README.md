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

## Target Variable

The target variable is weekly USD/IRR exchange-rate volatility.

The project focuses on forecasting volatility rather than predicting the exact
future exchange-rate level.

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

The raw response contains daily OHLC prices, change values, Gregorian dates, and
Jalali dates.

## Work Completed

- Created the project repository and folder structure
- Recorded the data source and retrieval
- Downloaded and preserved the raw TGJU JSON response


## Project Structure

```text
data/
  raw/          Original source data
  interim/      Cleaned daily data
  processed/    Weekly modelling data

docs/
  sources_register.md
  methodology.md
  ai_evidence.md
  ai_use_register.md
  feature_register.md

src/
  download_tgju_data.py

results/        Model outputs, tables, and figures
tests/          Automated tests

