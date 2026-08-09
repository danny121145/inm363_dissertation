import pandas as pd
from pathlib import Path

USD_IRR_PATH = Path("data/processed/usd_irr_tgju_weekly.csv")
BRENT_PATH = Path("data/processed/weekly_brent_oil.csv")
INFLATION_PATH = Path("data/processed/iran_inflation_weekly.csv")
SANCTIONS_PATH = Path("data/processed/ofac_iran_sanctions_weekly.csv")
OUTPUT_PATH = Path("data/processed/weekly_modelling_data.csv")

# Load processed datasets
usd_irr = pd.read_csv(USD_IRR_PATH)
brent = pd.read_csv(BRENT_PATH)
inflation = pd.read_csv(INFLATION_PATH)
sanctions = pd.read_csv(SANCTIONS_PATH)

# Convert weekly date columns
for df in [usd_irr, brent, inflation, sanctions]:
    df["week_ending"] = pd.to_datetime(df["week_ending"])

# Check that each source has one row per week
for name, df in {
    "USD/IRR": usd_irr,
    "Brent": brent,
    "Inflation": inflation,
    "Sanctions": sanctions,
}.items():

    if df["week_ending"].duplicated().any():
        raise ValueError(f"{name} contains duplicate week_ending values.")

# Use USD/IRR as the master weekly calendar
modelling_data = usd_irr.merge(brent, on="week_ending", how="left", validate="one_to_one",)
modelling_data = modelling_data.merge(inflation, on="week_ending", how="left", validate="one_to_one",)
modelling_data = modelling_data.merge(sanctions, on="week_ending", how="left", validate="one_to_one",)

#sort chronologically
modelling_data = modelling_data.sort_values("week_ending").reset_index(drop=True)

# Final validation
if len(modelling_data) != len(usd_irr):
    raise ValueError("Merged dataset does not have the same number of rows as USD/IRR dataset.")
if modelling_data["week_ending"].duplicated().any():
    raise ValueError("Merged dataset contains duplicate week_ending values.")
if not modelling_data["week_ending"].is_monotonic_increasing:
    raise ValueError("Merged dataset is not sorted in chronological order.")

# Display merge summary
print("Merge Summary:")
print(f"rows: {len(modelling_data)}")
print(f"date range: {modelling_data['week_ending'].min().date()} to {modelling_data['week_ending'].max().date()}")
print(f"duplicate weeks: {modelling_data['week_ending'].duplicated().sum()}")
print(f"missing values:\n{modelling_data.isna().sum()}")
print("\n Columns")
for column in modelling_data.columns:
    print(f"  - {column}")

# Save merged dataset
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
modelling_data.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d")
print(f"\nMerged dataset saved to {OUTPUT_PATH}")

