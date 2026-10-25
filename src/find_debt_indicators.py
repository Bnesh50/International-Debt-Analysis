
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
METADATA_FILE = PROJECT_DIR / "data" / "raw" / "IDS_SeriesMetaData.csv"
OUTPUT_DIR = PROJECT_DIR / "reports"

def main():
    df = pd.read_csv(
        METADATA_FILE,
        encoding="cp1252",
        low_memory=False
    )

    print("Available columns:")
    print(df.columns.tolist())

    # Find the metadata columns
    code_col = next(
        c for c in df.columns if c.strip().lower() == "code"
    )
    name_col = next(
        c for c in df.columns
        if c.strip().lower() == "indicator name"
    )

    definition_col = next(
        (
            c for c in df.columns
            if "short definition" in c.strip().lower()
        ),
        None
    )

    # Search for indicators related to external debt stocks
    search_text = df[name_col].fillna("").astype(str)

    mask = search_text.str.contains(
        "external debt stocks",
        case=False,
        regex=False
    )

    results = df.loc[mask].copy()

    columns = [code_col, name_col]
    if definition_col:
        columns.append(definition_col)

    results = results[columns]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results.to_csv(
        OUTPUT_DIR / "external_debt_stock_indicators.csv",
        index=False
    )

    print("\nExternal debt stock indicators found:", len(results))
    print(results.to_string(index=False))
    print("\nSaved to reports/external_debt_stock_indicators.csv")

if __name__ == "__main__":
    main()
