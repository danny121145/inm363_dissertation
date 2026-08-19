import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/processed/weekly_modelling_data.csv")
TRAIN_END = pd.Timestamp("2019-12-27")
VALIDATION_END = pd.Timestamp("2022-12-30")

#feature definitions
GARCH_FEATURES = [
    "log_return",
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

#multivariate datasets
multivariate_primary = create_lstm_dataset(MULTIVARIATE_FEATURES, PRIMARY_TARGET)
multivariate_robustness = create_lstm_dataset(MULTIVARIATE_FEATURES, ROBUSTNESS_TARGET)

def chronological_split(dataset, target_type=None):
    train = dataset[
        dataset["week_ending"] <= TRAIN_END
    ].copy()

    validation = dataset[
        (dataset["week_ending"] > TRAIN_END)
        & (dataset["week_ending"] <= VALIDATION_END)
    ].copy()

    test = dataset[
        dataset["week_ending"] > VALIDATION_END
    ].copy()

    # Prevent future target information crossing split boundaries
    if target_type == "primary":
        train = train.iloc[:-4].copy()
        validation = validation.iloc[:-4].copy()

    elif target_type == "robustness":
        train = train.iloc[:-1].copy()
        validation = validation.iloc[:-1].copy()

    return (
        train.reset_index(drop=True),
        validation.reset_index(drop=True),
        test.reset_index(drop=True),
    )

# GARCH split
garch_train, garch_validation, garch_test = chronological_split(
    garch_data
)


# Multivariate LSTM - primary target
multi_primary_train, multi_primary_validation, multi_primary_test = (
    chronological_split(
        multivariate_primary,
        target_type="primary",
    )
)


# Multivariate LSTM - robustness target
multi_robust_train, multi_robust_validation, multi_robust_test = (
    chronological_split(
        multivariate_robustness,
        target_type="robustness",
    )
)

split_datasets = {
    "GARCH": (
        garch_train,
        garch_validation,
        garch_test,
    ),
    "Multivariate LSTM - Primary": (
        multi_primary_train,
        multi_primary_validation,
        multi_primary_test,
    ),
    "Multivariate LSTM - Robustness": (
        multi_robust_train,
        multi_robust_validation,
        multi_robust_test,
    ),
}


print("\nFinal Chronological Splits")
print("=" * 70)

for name, splits in split_datasets.items():
    print(f"\n{name}")
    print("-" * 70)

    for split_name, split in zip(
        ["Train", "Validation", "Test"],
        splits,
    ):
        print(
            f"{split_name}: {len(split)} rows | "
            f"{split['week_ending'].min().date()} to "
            f"{split['week_ending'].max().date()}"
        )

#summary
datasets_summary = {
    "GARCH": garch_data,
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


