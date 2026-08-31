import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from config import WEEKLY_DATA_PATH, TRAIN_END, VALIDATION_START, VALIDATION_END, TEST_START

#config
SEQUENCE_LENGTH = 12
MULTIVARIATE_FEATURES = ["log_return", "squared_return", "rolling_volatility_4w", "brent_log_return", "inflation_yoy", "sanctions_event_count", "sanctions_tightening_count", "sanctions_relief_count"]
PRIMARY_TARGET= "target_volatility_4w"
ROBUSTNESS_TARGET= "target_squared_volatility_1w"

#target safe end dates
PRIMARY_TRAIN_END = pd.to_datetime("2019-11-29")
PRIMARY_VALIDATION_END = pd.to_datetime("2022-12-02")
ROBUSTNESS_TRAIN_END = pd.to_datetime("2019-12-20")
ROBUSTNESS_VALIDATION_END = pd.to_datetime("2022-12-23")

#load data
data = pd.read_csv(WEEKLY_DATA_PATH, parse_dates=["week_ending"])
data = data.sort_values("week_ending").reset_index(drop=True)

#create sequences for LSTM
def create_sequences(data, features, target, sequence_length, target_start, target_end):
    X = []
    y = []
    dates = []
    for target_index in range(sequence_length, len(data)):
        target_date = data.loc[target_index, "week_ending"]
        if target_date < target_start:
            continue
        if target_date > target_end:
            continue
        feature_window = data.loc[target_index-sequence_length:target_index-1, features]
        target_value = data.loc[target_index, target]
        #skip sequences with unavailable values
        if feature_window.isna().any().any():
            continue
        if pd.isna(target_value):
            continue
        X.append(feature_window.to_numpy())
        y.append(target_value)
        dates.append(target_date)
    return np.array(X), np.array(y), np.array(dates)

#primary target sequence

primary_train = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=PRIMARY_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp("2012-01-06"),
    target_end=PRIMARY_TRAIN_END,
)
primary_validation = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=PRIMARY_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp(VALIDATION_START),
    target_end=PRIMARY_VALIDATION_END,
)
primary_test = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=PRIMARY_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp(TEST_START),
    target_end=pd.Timestamp("2026-07-03"),
)

#robustness target sequence
robustness_train = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=ROBUSTNESS_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp("2012-01-06"),
    target_end=ROBUSTNESS_TRAIN_END,
)

robustness_validation = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=ROBUSTNESS_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp(VALIDATION_START),
    target_end=ROBUSTNESS_VALIDATION_END,
)

robustness_test = create_sequences(
    data=data,
    features=MULTIVARIATE_FEATURES,
    target=ROBUSTNESS_TARGET,
    sequence_length=SEQUENCE_LENGTH,
    target_start=pd.Timestamp(TEST_START),
    target_end=pd.Timestamp("2026-07-24"),
)

# Reproducibility and leakage checks
TARGET_COLUMNS = {
    "target_volatility_4w",
    "target_squared_volatility_1w",
}

if TARGET_COLUMNS.intersection(MULTIVARIATE_FEATURES):
    raise ValueError("Target columns must not appear in LSTM features.")

def check_sequence_alignment(sequence_data, sequence_length):
    X, y, dates = sequence_data

    if len(X) != len(y) or len(y) != len(dates):
        raise ValueError(
            "Sequence inputs, targets and dates are not aligned."
        )
    if X.shape[1] != sequence_length:
        raise ValueError(
            "Unexpected LSTM sequence length."
        )
    if X.shape[2] != len(MULTIVARIATE_FEATURES):
        raise ValueError(
            "Unexpected number of LSTM features."
        )

for sequence_data in [
    primary_train,
    primary_validation,
    primary_test,
    robustness_train,
    robustness_validation,
    robustness_test,
]:
    check_sequence_alignment(sequence_data,SEQUENCE_LENGTH,)
def print_sequence_summary(name, sequence_data):
    X, y, dates = sequence_data

    print(f"{name}")
    print(f"Sequences: {len(X)}")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    if len(dates) > 0:
        print(f"target dates: " f"{pd.Timestamp(dates[0]).date()} to " f"{pd.Timestamp(dates[-1]).date()}" ) 

if primary_train[2][-1] > np.datetime64("2019-11-29"):
    raise ValueError("Primary training targets cross the split boundary.")

if primary_validation[2][-1] > np.datetime64("2022-12-02"):
    raise ValueError("Primary validation targets cross the split boundary.")

if robustness_train[2][-1] > np.datetime64("2019-12-20"):
    raise ValueError("Robustness training targets cross the split boundary.")

if robustness_validation[2][-1] > np.datetime64("2022-12-23"):
    raise ValueError("Robustness validation targets cross the split boundary.")

if len(MULTIVARIATE_FEATURES) != len(set(MULTIVARIATE_FEATURES)):
    raise ValueError("Duplicate columns found in LSTM feature list.")

missing_features = [
    feature
    for feature in MULTIVARIATE_FEATURES
    if feature not in data.columns
]

if missing_features:
    raise ValueError(f"Missing LSTM feature columns: {missing_features}")

print("\nLSTM Sequence Summary")
print(f"Sequence length: {SEQUENCE_LENGTH} weeks")
print(f"Number of features: {len(MULTIVARIATE_FEATURES)}")
print_sequence_summary("Primary - Train", primary_train)
print_sequence_summary("Primary - Validation", primary_validation)
print_sequence_summary("Primary - Test", primary_test)
print_sequence_summary("Robustness - Train", robustness_train)
print_sequence_summary("Robustness - Validation", robustness_validation)
print_sequence_summary("Robustness - Test", robustness_test)

def scale_sequence_data(train_data, validation_data, test_data):
    X_train, y_train, train_dates = train_data
    X_validation, y_validation, validation_dates = validation_data
    X_test, y_test, test_dates = test_data
    n_features = X_train.shape[2]

    # Feature scaling
    feature_scaler = StandardScaler()

    # Fit only on training features
    X_train_2d = X_train.reshape(-1, n_features)
    feature_scaler.fit(X_train_2d)

    # Transform train, validation and test
    X_train_scaled = feature_scaler.transform(X_train.reshape(-1, n_features)).reshape(X_train.shape)
    X_validation_scaled = feature_scaler.transform(X_validation.reshape(-1, n_features)).reshape(X_validation.shape)
    X_test_scaled = feature_scaler.transform(X_test.reshape(-1, n_features)).reshape(X_test.shape)

    # Target scaling
    target_scaler = StandardScaler()
    y_train_scaled = target_scaler.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_validation_scaled = target_scaler.transform(y_validation.reshape(-1, 1)).flatten()
    y_test_scaled = target_scaler.transform(y_test.reshape(-1, 1)).flatten()

    return {
        "X_train": X_train_scaled,
        "y_train": y_train_scaled,
        "train_dates": train_dates,

        "X_validation": X_validation_scaled,
        "y_validation": y_validation_scaled,
        "validation_dates": validation_dates,

        "X_test": X_test_scaled,
        "y_test": y_test_scaled,
        "test_dates": test_dates,

        "feature_scaler": feature_scaler,
        "target_scaler": target_scaler,
    }

primary_scaled = scale_sequence_data(
    primary_train,
    primary_validation,
    primary_test,
)

robustness_scaled = scale_sequence_data(
    robustness_train,
    robustness_validation,
    robustness_test,
)

def check_scaled_data(scaled_data):
    if np.isnan(scaled_data["X_train"]).any():
        raise ValueError("NaN found in scaled training features.")

    if np.isnan(scaled_data["X_validation"]).any():
        raise ValueError("NaN found in scaled validation features.")

    if np.isnan(scaled_data["X_test"]).any():
        raise ValueError("NaN found in scaled test features.")

    if np.isnan(scaled_data["y_train"]).any():
        raise ValueError("NaN found in scaled training target.")

check_scaled_data(primary_scaled)
check_scaled_data(robustness_scaled)

print("Scaling Summary")

print("Primary")
print("X train shape:", primary_scaled["X_train"].shape)
print("y train shape:", primary_scaled["y_train"].shape)
print("Training feature mean:",primary_scaled["X_train"].mean(),)
print("Training feature std:",primary_scaled["X_train"].std(),)

print("Robustness")
print("X train shape:", robustness_scaled["X_train"].shape)
print("y train shape:", robustness_scaled["y_train"].shape)
print("Training feature mean:",robustness_scaled["X_train"].mean(),)
print("Training feature std:",robustness_scaled["X_train"].std(),)