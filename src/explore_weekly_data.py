"""Produce basic descriptive statistics for weekly USD/IRR data."""

from pathlib import Path
import pandas as pd
from statsmodels.stats.diagnostic import het_arch
from statsmodels.stats.diagnostic import acorr_ljungbox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "usd_irr_tgju_weekly.csv"

def main() -> None:
    dataframe = pd.read_csv(WEEKLY_DATA_PATH, parse_dates=["week_ending", "observation_date"])
    
    returns = dataframe["log_return"].dropna()
    print("Descriptive statistics of weekly dataset")
    print(f"rows: {len(dataframe)}")
    print(f"usable returns: {len(returns)}")
    print(f"date range: {dataframe['week_ending'].min().date()} to {dataframe['week_ending'].max().date()}")

    print("\nLog-return descriptive statistics:")
    print(returns.describe().to_string())

    print("\nAdditional statistics:")
    print(f"Skewness: {returns.skew():.6f}")
    print(f"Excess kurtosis: {returns.kurt():.6f}")
    print(f"Minimum return date: {dataframe.loc[dataframe['log_return'].idxmin(), 'week_ending'].date()}")
    print(f"Maximum return date: {dataframe.loc[dataframe['log_return'].idxmax(), 'week_ending'].date()}")

    squared_returns = returns ** 2
    print("\nLjung-Box test for autocorrelation of returns:")
    print(acorr_ljungbox(returns, lags=[5, 10, 20], return_df=True).to_string())
    print("\nLjung-Box test for autocorrelation of squared returns:")
    print(acorr_ljungbox(squared_returns, lags=[5, 10, 20], return_df=True).to_string())
    arch_stat, arch_pvalue, _, _ = het_arch(returns, nlags=10)

    print(f"\nARCH LM test:")
    print(f"ARCH LM statistic: {arch_stat:.6f}")
    print(f"ARCH LM p-value: {arch_pvalue:.6f}")

    target_columns = [
    "rolling_volatility_4w",
    "target_volatility_4w",
    "target_squared_volatility_1w",
]

    print("\nVolatility-variable descriptive statistics:")

    for column in target_columns:
        print(f"\n{column}:")
        print(dataframe[column].dropna().describe().to_string())

if __name__ == "__main__":
    main()