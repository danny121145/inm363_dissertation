import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/processed/weekly_modelling_data.csv")

#feature definitions
GARCH_FEATURES = [
    "log_return",
]

UNIVARIATE_FEATURES = [
    "log_return",
    "squared_return",
    "rolling_volatility_4w",
]

MULTIVARIATE_FEATURES = [
    "log_return",
    "squared_return",
    "rolling_volatility_4w",
    "brent_log_return",
    "inflation_yoy",
    "sanctions_event_count",
    "sanctions_tightening_count",
    "sanctions_relief_count",
]

PRIMARY_TARGET = "target_volatility_4w"
ROBUSTNESS_TARGET = "target_squared_volatility_1w"

#load merged weekly datsaset
data = pd.read_csv(DATA_PATH, parse_dates=["week_ending"])
data = (data.sort_values("week_ending").reset_index(drop=True))

#garch dataset
garch_data = data[["week_ending"] + GARCH_FEATURES].dropna().reset_index(drop=True)
#lstm dataset preparation
def create_lstm_dataset(features, target):
    required_columns = ["week_ending"] + features + [target]
    dataset = data[required_columns].dropna().reset_index(drop=True)
    return dataset

#univaraite datasets
univariate_primary = create_lstm_dataset(UNIVARIATE_FEATURES, PRIMARY_TARGET)
univariate_robustness = create_lstm_dataset(UNIVARIATE_FEATURES, ROBUSTNESS_TARGET)

#multivariate datasets
multivariate_primary = create_lstm_dataset(MULTIVARIATE_FEATURES, PRIMARY_TARGET)
multivariate_robustness = create_lstm_dataset(MULTIVARIATE_FEATURES, ROBUSTNESS_TARGET)

#summary
datasets_summary = {
    "GARCH": garch_data,
    "Univariate LSTM (Primary Target)": univariate_primary,
    "Univariate LSTM (Robustness Target)": univariate_robustness,
    "Multivariate LSTM (Primary Target)": multivariate_primary,
    "Multivariate LSTM (Robustness Target)": multivariate_robustness,
}

print("Datasets Summary:")
for name, df in datasets_summary.items():
    print(f"\n{name}:")
    print(f"  - rows: {len(df)}")
    print(f"  - date range: {df['week_ending'].min().date()} to {df['week_ending'].max().date()}")
    print(f"duplicate weeks: {df['week_ending'].duplicated().sum()}")
    print(f"missing values:\n{df.isna().sum().sum()}")


