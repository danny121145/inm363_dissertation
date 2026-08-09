"""Explore weekly OFAC Iran sanctions features."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ofac_iran_sanctions_weekly.csv"
)


def main() -> None:
    dataframe = pd.read_csv(
        DATA_PATH,
        parse_dates=["week_ending"],
    )

    feature_columns = [
        column
        for column in dataframe.columns
        if column != "week_ending"
    ]

    print("Weekly sanctions dataset")
    print(f"Rows: {len(dataframe)}")
    print(
        "Date range: "
        f"{dataframe['week_ending'].min().date()} to "
        f"{dataframe['week_ending'].max().date()}"
    )

    print("\nMaximum weekly value for each feature:")
    print(
        dataframe[feature_columns]
        .max()
        .to_string()
    )

    print("\nWeeks where each feature is non-zero:")
    print(
        (dataframe[feature_columns] > 0)
        .sum()
        .to_string()
    )

    print("\nPercentage of weeks where each feature is non-zero:")
    print(
        (
            (dataframe[feature_columns] > 0)
            .mean()
            .mul(100)
            .round(2)
        ).to_string()
    )

    print("\nCorrelations between sanctions features:")
    print(
        dataframe[feature_columns]
        .corr()
        .round(3)
        .to_string()
    )


if __name__ == "__main__":
    main()
