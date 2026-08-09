"""Prepare weekly Iran inflation data from the IMF monthly CPI dataset."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = (PROJECT_ROOT/ "data"/ "raw"/ "imf_iran_cpi_monthly.csv")
USD_WEEKLY_PATH = (PROJECT_ROOT/ "data"/ "processed"/ "usd_irr_tgju_weekly.csv")
OUTPUT_PATH = (PROJECT_ROOT/ "data"/ "processed"/ "iran_inflation_weekly.csv")

def main() -> None:
    """Prepare monthly Iran CPI and align lagged inflation to weekly dates."""

    dataframe = pd.read_csv(RAW_PATH)
    # Keep only the exact Iran monthly CPI series required.
    inflation = dataframe[(dataframe["COUNTRY.ID"] == "IRN") & (dataframe["INDEX_TYPE.ID"] == "CPI") & (dataframe["COICOP_1999.ID"] == "_T") & (dataframe["TYPE_OF_TRANSFORMATION.ID"] == "IX") & (dataframe["FREQUENCY.ID"] == "M")].copy()
    # Keep only the fields needed for processing.
    inflation = inflation[["TIME_PERIOD","OBS_VALUE",]].rename(columns={"TIME_PERIOD": "reference_month","OBS_VALUE": "cpi_index",})
    # Convert IMF format such as 2011-M12 into a monthly period.
    inflation["reference_month"] = pd.PeriodIndex(inflation["reference_month"].str.replace("-M", "-", regex=False),freq="M",)
    inflation = (inflation.sort_values("reference_month").reset_index(drop=True))
    # Basic validation.
    if inflation["reference_month"].duplicated().any():
        raise ValueError("Duplicate CPI months found.")

    if inflation["cpi_index"].isna().any():
        raise ValueError("Missing CPI values found.")

    if (inflation["cpi_index"] <= 0).any():
        raise ValueError("Invalid CPI values found.")

    # Calculate year-on-year inflation.
    inflation["inflation_yoy"] = (inflation["cpi_index"].pct_change(periods=12) * 100)
    # Apply a one-month lag.
    # Example: December 2019 inflation becomes available for January 2020.
    inflation["available_from"] = (inflation["reference_month"] + 1).dt.to_timestamp()
    # Remove months that do not yet have 12 months of history.
    inflation = inflation.dropna(subset=["inflation_yoy"]).reset_index(drop=True)
    # Load the existing USD/IRR weekly calendar.
    weekly = pd.read_csv(USD_WEEKLY_PATH,usecols=["week_ending"],parse_dates=["week_ending"],)
    weekly = (weekly.drop_duplicates().sort_values("week_ending").reset_index(drop=True))
    # Convert monthly availability dates to datetime.
    inflation["available_from"] = pd.to_datetime(inflation["available_from"])
    # For each Friday, use the latest inflation value that had become available by that date.
    weekly_inflation = pd.merge_asof(weekly, inflation[["available_from","reference_month","cpi_index","inflation_yoy",]].sort_values("available_from"),left_on="week_ending",right_on="available_from",direction="backward",)
    # Convert the monthly period to a readable string.
    weekly_inflation["reference_month"] = (weekly_inflation["reference_month"].astype(str))
    weekly_inflation["week_ending"] = (weekly_inflation["week_ending"].dt.strftime("%Y-%m-%d"))
    weekly_inflation["available_from"] = (weekly_inflation["available_from"].dt.strftime("%Y-%m-%d"))

    OUTPUT_PATH.parent.mkdir(parents=True,exist_ok=True,)
    weekly_inflation.to_csv(OUTPUT_PATH,index=False,)

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Rows: {len(weekly_inflation)}")

    print("Date range: "f"{weekly_inflation['week_ending'].min()} to "f"{weekly_inflation['week_ending'].max()}")
    print("Missing inflation values: "f"{weekly_inflation['inflation_yoy'].isna().sum()}")
    print("Duplicate weeks: "f"{weekly_inflation['week_ending'].duplicated().sum()}")
    print("\nFirst 10 rows:")
    print(weekly_inflation.head(10).to_string(index=False))
    print("\nLast 10 rows:")
    print(weekly_inflation.tail(10).to_string(index=False))

if __name__ == "__main__":
    main()