from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "weekly_modelling_data.csv"
PRIMARY_TARGET_COLUMN = "target_volatility_4w"
ROBUSTNESS_TARGET_COLUMN = "target_squared_volatility_1w"
FORECAST_HORIZON = 4  # weeks
SEED = 42  # Random seed for reproducibility
TRAIN_END = "2019-12-27"
VALIDATION_START = "2020-01-03"
VALIDATION_END = "2022-12-30"
TEST_START = "2023-01-06"
TEST_END = "2026-07-31"