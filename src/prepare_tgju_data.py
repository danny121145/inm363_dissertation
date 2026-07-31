"""convert raw tgju data into a cleaned interim csv"""

from __future__ import annotations
import json
import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data/raw/usd_irr_tgju_history_raw.json"
INTERIM_DATA_PATH = PROJECT_ROOT / "data/interim/usd_irr_tgju_daily.csv"
COLUMNS = [
    "open",
    "low",
    "high",
    "close",
    "change",
    "change_percent",
    "date",
    "jalali_date",
]

def parse_number(value:object) -> float:
    """Convert TGJU formatted numbers and html to numeric values"""
    text = str(value)
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text =text.replace(",", "").replace("%", "").strip()  # Remove thousands separators and percent signs

    if text in ("", "-"):
        return float("nan")
    return float(text)

def load_raw_rows(path: Path) -> list[list[object]]:
    """Load raw rows from the TGJU JSON response"""
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    
    try:
        rows = payload["data"]
    except KeyError as e:
        raise KeyError(
            "Expected payload['data'] in the raw JSON file:"
        ) from e
    
    if not isinstance(rows, list):
        raise TypeError("TGJU data must be a list of rows.")
    return rows

def prepare_dataframe(rows: list[list[object]]) -> pd.DataFrame:
    """Create and validate the cleaned daily TGJU dataframe"""
    dataframe = pd.DataFrame(rows, columns=COLUMNS)
    numeric_columns = ["open", "low", "high", "close", "change", "change_percent"]

    for col in numeric_columns:
        dataframe[col] = dataframe[col].map(parse_number)
    dataframe["date"] = pd.to_datetime(dataframe["date"], format="%Y/%m/%d", errors="raise")

    dataframe = dataframe.sort_values("date").reset_index(drop=True)
    if dataframe["date"].duplicated().any():
        duplicate_dates = dataframe.loc[dataframe["date"].duplicated(keep=False), "date", ]
        raise ValueError("Duplicate gregorian dates found: " f"{duplicate_dates.dt.strftime('%Y-%m-%d').tolist()}")
    
    required_columns = [
        "open",
        "low",
        "high",
        "close",
        "date",
        "jalali_date",
    ]

    missing_required = dataframe[required_columns].isna().sum()

    if missing_required.any():
        raise ValueError(
            "Missing required values in columns: "
            f"{missing_required[missing_required > 0]}"
        )
    
    dataframe["ohlc_valid"] = ~(
        (dataframe["low"] > dataframe["high"]) |
        (dataframe["open"] < dataframe["low"]) |
        (dataframe["open"] > dataframe["high"]) |
        (dataframe["close"] < dataframe["low"]) |
        (dataframe["close"] > dataframe["high"])
    )
    invalid_count = int((~dataframe["ohlc_valid"]).sum())

    if invalid_count:
        print(f"Warning: {invalid_count} rows have invalid OHLC relationships "
              "and are retained unchanged with ohlc_valid=False.")
        
    dataframe["date"] = dataframe["date"].dt.strftime("%Y-%m-%d")
    return dataframe

def main() -> None:
    """raw to interim data conversion"""
    rows = load_raw_rows(RAW_DATA_PATH)
    dataframe = prepare_dataframe(rows)
    INTERIM_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(INTERIM_DATA_PATH, index=False)
    print(f"saved: {INTERIM_DATA_PATH}")
    print(f"rows: {len(dataframe)}")
    print(f"columns: {list(dataframe.columns)}")
    print(f"date range: {dataframe['date'].min()} to {dataframe['date'].max()}")
    print(f"duplicate dates: {dataframe['date'].duplicated().sum()}")
    print(f"missing values: {int(dataframe.isna().sum().sum())}")

if __name__ == "__main__":
    main()  