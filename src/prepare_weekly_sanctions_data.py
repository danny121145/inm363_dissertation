"""Create weekly sanctions features from interim OFAC Iran events."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SANCTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "ofac_iran_sanctions_event.csv"
)

WEEKLY_USD_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "usd_irr_tgju_weekly.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ofac_iran_sanctions_weekly.csv"
)

ACTION_TYPES = [
    "tightening",
    "relief",
    "license",
    "regulatory_change",
    "other",
]
SECTORS = [
    "oil_energy",
    "banking_finance",
    "shipping",
    "trade_industry",
    "government_irgc",
    "human_rights",
    "nuclear_missile",
    "general_other",
]

def main() -> None:
    """Aggregate relevant OFAC sanctions events into weekly features."""

    sanctions = pd.read_csv(
        SANCTIONS_PATH,
        parse_dates=["event_date"],
    )

    weekly_usd = pd.read_csv(
        WEEKLY_USD_PATH,
        parse_dates=["week_ending"],
    )

    # Assign every sanctions event to a week ending Friday.
    sanctions["week_ending"] = (
        sanctions["event_date"]
        .dt.to_period("W-FRI")
        .dt.end_time
        .dt.normalize()
    )

    # Total number of relevant sanctions events in each week.
    total_counts = (
        sanctions.groupby("week_ending")
        .size()
        .rename("sanctions_event_count")
    )

    # Count each type of sanctions action by week.
    action_counts = (
        sanctions
        .groupby(["week_ending", "action_type"])
        .size()
        .unstack(fill_value=0)
    )


    # Make sure every expected action type exists as a column.
    for action_type in ACTION_TYPES:
        if action_type not in action_counts.columns:
            action_counts[action_type] = 0

    action_counts = action_counts[ACTION_TYPES]

    action_counts = action_counts.rename(
        columns={
            "tightening": "sanctions_tightening_count",
            "relief": "sanctions_relief_count",
            "license": "sanctions_license_count",
            "regulatory_change":
                "sanctions_regulatory_change_count",
            "other": "sanctions_other_count",
        }
    )

    # Split multi-sector values into separate rows.
    sector_events = sanctions[
        ["week_ending", "sector"]
    ].copy()

    sector_events["sector"] = (
        sector_events["sector"]
        .str.split(";")
    )

    sector_events = sector_events.explode("sector")

    sector_events["sector"] = (
        sector_events["sector"].str.strip()
    )

    # Count events for each sector by week.
    sector_counts = (
        sector_events
        .groupby(["week_ending", "sector"])
        .size()
        .unstack(fill_value=0)
    )

    for sector in SECTORS:
        if sector not in sector_counts.columns:
            sector_counts[sector] = 0

    sector_counts = sector_counts[SECTORS]

    sector_counts = sector_counts.rename(
        columns={
            sector: f"sanctions_{sector}_count"
            for sector in SECTORS
        }
    )

    weekly_sanctions = pd.concat(
        [
            total_counts,
            action_counts,
            sector_counts,
        ],
        axis=1,
    ).reset_index()

    # Use the USD/IRR weekly calendar so every exchange-rate week exists.
    weekly_calendar = weekly_usd[
        ["week_ending"]
    ].drop_duplicates()

    weekly = weekly_calendar.merge(
        weekly_sanctions,
        on="week_ending",
        how="left",
    )

    feature_columns = [
        column
        for column in weekly.columns
        if column != "week_ending"
    ]

    # Weeks with no sanctions events should contain zero, not NaN.
    weekly[feature_columns] = (
        weekly[feature_columns]
        .fillna(0)
        .astype(int)
    )

    weekly = weekly.sort_values(
        "week_ending"
    ).reset_index(drop=True)

    weekly["week_ending"] = (
        weekly["week_ending"]
        .dt.strftime("%Y-%m-%d")
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    weekly.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Rows: {len(weekly)}")
    print(
        "Date range: "
        f"{weekly['week_ending'].min()} to "
        f"{weekly['week_ending'].max()}"
    )
    print(
        "Weeks with sanctions events: "
        f"{(weekly['sanctions_event_count'] > 0).sum()}"
    )
    print(
        "Weeks without sanctions events: "
        f"{(weekly['sanctions_event_count'] == 0).sum()}"
    )
    print(
        "Total sanctions events represented: "
        f"{weekly['sanctions_event_count'].sum()}"
    )

    print("\nWeekly feature totals:")
    print(
        weekly[feature_columns]
        .sum()
        .to_string()
    )

if __name__ == "__main__":
    main()
