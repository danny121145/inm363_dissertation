"""Explore processed weekly Iran inflation data."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = (PROJECT_ROOT/ "data"/ "processed"/ "iran_inflation_weekly.csv")

def main() -> None:
    inflation = pd.read_csv(INPUT_PATH,parse_dates=["week_ending","available_from"],)
    usable = inflation["inflation_yoy"].dropna()
    print(f"rows: {len(inflation)}")
    print(f"date range: {inflation['week_ending'].min()} to {inflation['week_ending'].max()}")
    print(f"usable inflation observations: {len(usable)}")
    print(f"missing inflation values: {inflation['inflation_yoy'].isna().sum()}")
    print("\ninflation descriptive statistics:")
    print(usable.describe().to_string())
    print(f"skewness: {usable.skew():.6f}")
    print(f"kurtosis: {usable.kurtosis():.6f}")
    min_index = usable.idxmin()
    max_index = usable.idxmax()
    print(f"date of minimum inflation: {inflation.loc[min_index, 'week_ending'].date()}")
    print(f"Minimum inflation reference month: {inflation.loc[min_index, 'reference_month']}")
    print(f"date of maximum inflation: {inflation.loc[max_index, 'week_ending'].date()}")
    print(f"Maximum inflation reference month: {inflation.loc[max_index, 'reference_month']}")

if __name__ == "__main__":
    main()