"""Create a weekly data file from the daily data files."""

from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAILY_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "usd_irr_tgju_daily.csv"
WEEKLY_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "usd_irr_tgju_weekly.csv"

def main() -> None:
    """Resample the daily close price to weeks ending Friday"""
    dataframe = pd.read_csv(DAILY_DATA_PATH, parse_dates=["date"])
    daily = (dataframe[["date", "close"]].sort_values("date").set_index("date"))
    daily["observation_date"] = daily.index
    weekly = daily.resample("W-FRI").last()
    weekly = weekly.dropna(subset=["close"])
    weekly["log_return"] = np.log(weekly["close"] / weekly["close"].shift(1))
    weekly.index.name = "week_ending"
    weekly = weekly.reset_index()
    weekly = weekly[
        ["week_ending", "observation_date", "close", "log_return"]
    ]

    WEEKLY_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(WEEKLY_DATA_PATH, index=False)
    print(f"saved: {WEEKLY_DATA_PATH}")
    print(f"rows: {len(weekly)}")
    print(f"date range: {weekly['week_ending'].min()} to {weekly['week_ending'].max()}")
    print(f"missing close values: {weekly['close'].isna().sum()}")
    print(f"missing log_return values: {weekly['log_return'].isna().sum()}")
    print(f"duplicate weeks: {weekly['week_ending'].duplicated().sum()}")

if __name__ == "__main__":
    main()