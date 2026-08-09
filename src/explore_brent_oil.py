"""Explore the weekly Brent oil price data."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "weekly_brent_oil.csv"

def main() -> None:
    """Load and explore the weekly Brent oil price data."""
    brent = pd.read_csv(DATA_PATH, parse_dates=["week_ending"])
    returns = brent["brent_log_return"].dropna()

    print(f"loaded: {DATA_PATH}")
    print(f"rows: {len(brent)}")
    print(f"date range: {brent['week_ending'].min()} to {brent['week_ending'].max()}")
    print(brent["brent_price"].describe().to_string())
    print(returns.describe().to_string())
    print(f"skewness:{returns.skew():.6f}")
    print(f"kurtosis:{returns.kurtosis():.6f}")
    min_index = returns.idxmin()
    max_index = returns.idxmax()
    print("minimum return date:" f"{brent.loc[min_index, 'week_ending'].date()}")
    print("maximum return date:" f"{brent.loc[max_index, 'week_ending'].date()}")

if __name__ == "__main__":
    main()