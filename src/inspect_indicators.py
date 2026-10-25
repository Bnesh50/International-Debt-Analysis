
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SERIES_FILE = PROJECT_DIR / "data" / "raw" / "IDS_SeriesMetaData.csv"
OUTPUT_DIR = PROJECT_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("INTERNATIONAL DEBT - INDICATOR INSPECTION")
    print("=" * 50)

    if not SERIES_FILE.exists():
        print("ERROR: Indicator metadata file not found.")
        return

    # Load the indicator metadata
    df = pd.read_csv(
        SERIES_FILE,
        encoding="cp1252",
        low_memory=False
    )

    print("\nColumns found:")
    print(df.columns.tolist())

    print("\nTotal indicator records:", len(df))

    # Find the actual column names
    code_col = next(
        (c for c in df.columns if c.strip().lower() == "code"),
        None
    )

    name_col = next(
        (
            c for c in df.columns
            if c.strip().lower() in ["indicator name", "series name"]
        ),
        None
    )

    definition_col = next(
        (
            c for c in df.columns
            if "short definition" in c.strip().lower()
        ),
        None
    )

    if code_col is None or name_col is None:
        print("ERROR: Could not identify indicator code/name columns.")
        print("Please check the printed column names.")
        return

    # Save all indicator definitions
    selected_columns = [code_col, name_col]

    if definition_col:
        selected_columns.append(definition_col)

    metadata = df[selected_columns].copy()

    metadata.to_csv(
        OUTPUT_DIR / "indicator_metadata_review.csv",
        index=False
    )

    # Find possible debt-related indicators using their names
    keywords = [
        "debt",
        "external debt",
        "debt service",
        "interest payment",
        "principal repayment",
        "disbursement",
        "creditor"
    ]

    name_text = metadata[name_col].fillna("").astype(str)

    mask = name_text.str.contains(
        "|".join(keywords),
        case=False,
        regex=True
    )

    possible_debt = metadata[mask].copy()

    possible_debt.to_csv(
        OUTPUT_DIR / "possible_debt_indicators.csv",
        index=False
    )

    print("\nPossible debt-related indicators:", len(possible_debt))
    print("\nFirst 20 possible indicators:")

    print(possible_debt.head(20).to_string(index=False))

    print("\nFiles saved:")
    print("- reports/indicator_metadata_review.csv")
    print("- reports/possible_debt_indicators.csv")


if __name__ == "__main__":
    main()
