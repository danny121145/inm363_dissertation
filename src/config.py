from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "usd_irr_tgju_weekly.csv"
PRIMARY_TARGET_COLUMN = "target_volatility_4w"
ROBUST_TARGET_COLUMN = "target_squared_volatility_1w"
FORECAST_HORIZON = 4  # weeks
SEED = 42  # Random seed for reproducibility
TRAIN_START = "2011-12-02"
TRAIN_END = "2021-12-31"
VALIDATION_START = "2022-01-01"
VALIDATION_END = "2023-12-31"
TEST_START = "2024-01-01"
TEST_END = "2026-07-31"