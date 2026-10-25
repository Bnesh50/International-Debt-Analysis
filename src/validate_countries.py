
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

DEBT_FILE = (
    PROJECT_DIR / "data" / "processed" / "cleaned_debt_long.csv"
)
COUNTRY_FILE = (
    PROJECT_DIR / "data" / "raw" / "IDS_CountryMetaData.csv"
)
OUTPUT_DIR = PROJECT_DIR / "reports"

INDICATOR_CODE = "DT.DOD.DECT.CD"


def main():
    print("=" * 60)
    print("VALIDATING COUNTRY-LEVEL DEBT DATA")
    print("=" * 60)

    debt = pd.read_csv(DEBT_FILE, low_memory=False)
    countries = pd.read_csv(
        COUNTRY_FILE,
        encoding="cp1252",
        low_memory=False
    )

    print("\nMetadata columns:")
    print(countries.columns.tolist())

    # Find the country-code column in metadata
    code_column = next(
        (
            column for column in countries.columns
            if column.strip().lower() in ["country code", "code"]
        ),
        None
    )

    if code_column is None:
        print("ERROR: Country-code column not found.")
        return

    # Find the metadata field identifying countries vs aggregates
    indicator_columns = [
        column for column in countries.columns
        if any(
            word in column.lower()
            for word in ["region", "income", "aggregate"]
        )
    ]

    print("\nPossible classification columns:", indicator_columns)

    if not indicator_columns:
        print(
            "\nNo classification columns found. "
            "We must inspect the metadata structure before filtering."
        )
        return

    # Show sample metadata records
    print("\nSample country metadata:")
    print(
        countries[
            [code_column] + indicator_columns
        ].head(15).to_string(index=False)
    )

    # Filter to the chosen debt indicator
    debt = debt[debt["Series Code"] == INDICATOR_CODE].copy()

    if debt.empty:
        print("\nERROR: Debt indicator not found.")
        return

    # Save the metadata and filtered debt observations for inspection
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    countries.to_csv(
        OUTPUT_DIR / "country_metadata_review.csv",
        index=False
    )

    debt.to_csv(
        OUTPUT_DIR / "external_debt_before_country_filter.csv",
        index=False
    )

    print("\nDebt rows before country validation:", len(debt))
    print("Debt country codes:", debt["Country Code"].nunique())

    print("\nSaved:")
    print("reports/country_metadata_review.csv")
    print("reports/external_debt_before_country_filter.csv")


if __name__ == "__main__":
    main()
