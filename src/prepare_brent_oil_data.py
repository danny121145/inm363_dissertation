"""Prepare weekly Brent oil price data from the EIA dataset."""
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "Weekly_Europe_Brent_Spot_Price_FOB.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "weekly_brent_oil.csv"
STUDY_START_DATE = pd.to_datetime("2011-12-02")
STUDY_END_DATE = pd.to_datetime("2026-07-31")

def main() -> None:
    """clean the weekly EIA brent dataset and calculate the weekly log return of the Brent price."""
    #load the raw EIA brent dataset
    brent = pd.read_csv(RAW_PATH, skiprows=3)
    #rename the columns
    brent = brent.rename(columns={"Week of": "week_ending", "Weekly Europe Brent Spot Price FOB  Dollars per Barrel": "brent_price"})
    #parse dates and sort from oldest to newest
    brent["week_ending"] = pd.to_datetime(brent["week_ending"], format="%m/%d/%Y")
    brent = (brent.sort_values("week_ending").reset_index(drop=True))
    #basic valdiation
    if brent["week_ending"].isna().any():
        raise ValueError("Missing week_ending values found.")

    if brent["brent_price"].isna().any():
        raise ValueError("Missing Brent prices found.")

    if brent["week_ending"].duplicated().any():
        raise ValueError("Duplicate week_ending values found.")

    if (brent["brent_price"] <= 0).any():
        raise ValueError("Invalid Brent prices found.")
    # Calculate weekly Brent log return before restricting the date range.
    # This allows the first study-period week to use the previous week's price.
    brent["brent_log_return"] = np.log(brent["brent_price"] / brent["brent_price"].shift(1))
    # Restrict to the study period
    brent = brent[(brent["week_ending"] >= STUDY_START_DATE ) & (brent["week_ending"] <= STUDY_END_DATE)].copy()
    brent = brent.reset_index(drop=True)
    #format dates consistently with other datasets
    brent["week_ending"] = brent["week_ending"].dt.strftime("%Y-%m-%d")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    brent.to_csv(OUTPUT_PATH, index=False)
    print(f"saved: {OUTPUT_PATH}")
    print(f"rows: {len(brent)}")
    print(f"date range: {brent['week_ending'].min()} to {brent['week_ending'].max()}")
    print(f"missing values: {brent.isna().sum()}")
    print(f"missing values in brent_log_return: {brent['brent_log_return'].isna().sum()}")
    print(f"duplicate weeks: {brent['week_ending'].duplicated().sum()}")
    print("\nfirst 5 rows:")
    print(brent.head().to_string(index=False))
    print("\nlast 5 rows:")
    print(brent.tail().to_string(index=False))

if __name__ == "__main__":
     main()
    
   