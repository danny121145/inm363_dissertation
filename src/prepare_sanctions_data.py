"""create an interim datastet from ofac data"""
from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "ofac_iran_candidate_events_raw.json"
INTERIM_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "ofac_iran_sanctions_event.csv"
CLASSIFICATION_PATH = PROJECT_ROOT / "data" / "manual" / "ofac_iran_event_classifications.csv"

VALID_ACTION_TYPES = {
    "tightening",
    "relief",
    "license",
    "regulatory_change",
    "other",
}

VALID_SECTORS = {
    "oil_energy",
    "banking_finance",
    "shipping",
    "trade_industry",
    "government_irgc",
    "human_rights",
    "nuclear_missile",
    "general_other",
}

def load_raw_data(path: Path) -> pd.DataFrame:
    """Load the untouched OFAC candidate-event JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if "records" not in payload:
        raise KeyError("Expected 'records' in the raw OFAC JSON.")

    records = payload["records"]

    if not isinstance(records, list):
        raise TypeError("Raw OFAC 'records' must be a list.")

    dataframe = pd.DataFrame(records)

    required_columns = [
        "event_date",
        "title",
        "description",
        "source_reference",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing raw columns: {missing_columns}"
        )

    dataframe["source_reference"] = (
        dataframe["source_reference"].astype(str).str.strip()
    )

    if dataframe["source_reference"].duplicated().any():
        duplicates = dataframe.loc[
            dataframe["source_reference"].duplicated(keep=False),
            "source_reference",
        ].tolist()

        raise ValueError(
            f"Duplicate source references in raw data: {duplicates}"
        )

    return dataframe


def load_classifications(path: Path) -> pd.DataFrame:
    """Load and validate the manual sanctions classifications."""
    if not path.exists():
        raise FileNotFoundError(
            f"Classification file not found: {path}"
        )

    dataframe = pd.read_csv(path)

    required_columns = [
        "source_reference",
        "relevant",
        "action_type",
        "sector",
        "classification_notes",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing classification columns: {missing_columns}"
        )

    dataframe["source_reference"] = (
        dataframe["source_reference"].astype(str).str.strip()
    )

    if dataframe["source_reference"].duplicated().any():
        duplicates = dataframe.loc[
            dataframe["source_reference"].duplicated(keep=False),
            "source_reference",
        ].tolist()

        raise ValueError(
            "Duplicate source references in classifications: "
            f"{duplicates}"
        )

    if not dataframe["relevant"].isin([0, 1]).all():
        raise ValueError(
            "'relevant' must contain only 0 or 1."
        )

    relevant = dataframe["relevant"] == 1

    invalid_actions = dataframe.loc[
        relevant
        & ~dataframe["action_type"].isin(VALID_ACTION_TYPES),
        "action_type",
    ].unique()

    if len(invalid_actions) > 0:
        raise ValueError(
            f"Invalid action types: {invalid_actions.tolist()}"
        )

    for source_reference, sectors in dataframe.loc[
        relevant,
        ["source_reference", "sector"],
    ].itertuples(index=False):

        if pd.isna(sectors) or not str(sectors).strip():
            raise ValueError(
                f"Missing sector for: {source_reference}"
            )

        sector_list = [
            sector.strip()
            for sector in str(sectors).split(";")
        ]

        invalid_sectors = [
            sector
            for sector in sector_list
            if sector not in VALID_SECTORS
        ]

        if invalid_sectors:
            raise ValueError(
                f"Invalid sector(s) for {source_reference}: "
                f"{invalid_sectors}"
            )

    return dataframe


def validate_matches(
    raw: pd.DataFrame,
    classifications: pd.DataFrame,
) -> None:
    """Verify that every raw candidate has one classification."""
    raw_references = set(raw["source_reference"])
    classification_references = set(
        classifications["source_reference"]
    )

    missing_classifications = (
        raw_references - classification_references
    )

    if missing_classifications:
        raise ValueError(
            "Raw events missing classifications: "
            f"{sorted(missing_classifications)}"
        )

    unknown_classifications = (
        classification_references - raw_references
    )

    if unknown_classifications:
        raise ValueError(
            "Classifications with no matching raw event: "
            f"{sorted(unknown_classifications)}"
        )


def prepare_dataframe(
    raw: pd.DataFrame,
    classifications: pd.DataFrame,
) -> pd.DataFrame:
    """Merge raw events with classifications and retain relevant events."""
    dataframe = raw.merge(
        classifications,
        on="source_reference",
        how="inner",
        validate="one_to_one",
    )

    dataframe = dataframe.loc[
        dataframe["relevant"] == 1
    ].copy()

    dataframe["event_date"] = pd.to_datetime(
        dataframe["event_date"],
        format="%m/%d/%Y",
        errors="raise",
    )

    dataframe = (
        dataframe
        .sort_values(["event_date", "source_reference"])
        .reset_index(drop=True)
    )

    dataframe["event_date"] = (
        dataframe["event_date"].dt.strftime("%Y-%m-%d")
    )

    columns = [
        "event_date",
        "title",
        "description",
        "press_release_url",
        "source_reference",
        "action_type",
        "sector",
        "classification_notes",
    ]

    columns = [
        column
        for column in columns
        if column in dataframe.columns
    ]

    return dataframe[columns]


def main() -> None:
    """Create the interim sanctions-event CSV."""
    raw = load_raw_data(RAW_DATA_PATH)
    classifications = load_classifications(
        CLASSIFICATION_PATH
    )

    validate_matches(raw, classifications)

    dataframe = prepare_dataframe(
        raw,
        classifications,
    )

    INTERIM_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        INTERIM_DATA_PATH,
        index=False,
    )

    print(f"Saved: {INTERIM_DATA_PATH}")
    print(f"Raw candidates: {len(raw)}")
    print(f"Classifications: {len(classifications)}")
    print(f"Relevant events retained: {len(dataframe)}")
    print(
        "Date range: "
        f"{dataframe['event_date'].min()} to "
        f"{dataframe['event_date'].max()}"
    )
    print(
        "Duplicate source references: "
        f"{dataframe['source_reference'].duplicated().sum()}"
    )
    print("\nAction types:")
    print(
        dataframe["action_type"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()