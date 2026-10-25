
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# INTERNATIONAL DEBT ANALYSIS - DATA CLEANING
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "data" / "raw" / "IDS_ALLCountries_Data.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 55)
    print("INTERNATIONAL DEBT ANALYSIS - DATA CLEANING")
    print("=" * 55)

    # 1. Check and load the original dataset
    if not RAW_FILE.exists():
        print("ERROR: Original CSV file was not found.")
        print("Expected location:", RAW_FILE)
        return

    df = pd.read_csv(
        RAW_FILE,
        encoding="cp1252",
        low_memory=False
    )

    original_rows = len(df)
    report = []

    report.append("INTERNATIONAL DEBT ANALYSIS - CLEANING REPORT")
    report.append("=" * 55)
    report.append(f"Original rows: {original_rows}")
    report.append(f"Original columns: {len(df.columns)}")

    print("Original rows:", original_rows)
    print("Original columns:", len(df.columns))

    # 2. Remove leading and trailing spaces from text fields
    text_columns = df.select_dtypes(include=["object"]).columns

    for column in text_columns:
        df[column] = df[column].map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    # Treat blank text as missing, without changing numeric zeroes
    df[text_columns] = df[text_columns].replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    # 3. Identify exact duplicate rows
    exact_duplicates = int(df.duplicated().sum())

    report.append(f"Exact duplicate rows found: {exact_duplicates}")

    # Save duplicate rows for audit before removing them
    duplicate_rows = df[df.duplicated(keep=False)].copy()

    duplicate_rows.to_csv(
        OUTPUT_DIR / "exact_duplicates_for_review.csv",
        index=False
    )

    # Remove only exact duplicates
    df = df.drop_duplicates().copy()

    report.append(
        f"Rows after removing exact duplicates: {len(df)}"
    )

    # 4. Check required identifier columns
    required_columns = [
        "Country Name",
        "Country Code",
        "Series Name",
        "Series Code"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR: Expected columns are missing:", missing_columns)
        print("Please check the original dataset column names.")
        return

    # Save rows with missing identifiers for manual review
    missing_identifier_mask = df[required_columns].isna().any(axis=1)

    missing_identifier_rows = df[missing_identifier_mask].copy()

    missing_identifier_rows.to_csv(
        OUTPUT_DIR / "rows_missing_identifiers.csv",
        index=False
    )

    report.append(
        "Rows with missing country/indicator identifiers: "
        f"{len(missing_identifier_rows)}"
    )

    # Exclude unidentified rows from analytical data,
    # but preserve them in the review file above
    df = df[~missing_identifier_mask].copy()

    # 5. Find yearly columns
    year_columns = [
        column for column in df.columns
        if str(column).isdigit()
        and len(str(column)) == 4
    ]

    year_columns = sorted(year_columns, key=int)

    if not year_columns:
        print("ERROR: No four-digit year columns were found.")
        return

    report.append(
        f"Year columns identified: {len(year_columns)}"
    )
    report.append(
        f"Year range: {year_columns[0]} to {year_columns[-1]}"
    )

    # 6. Convert year values to numeric
    for column in year_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # 7. Convert wide format to long format
    identifier_columns = [
        column for column in df.columns
        if column not in year_columns
    ]

    long_df = df.melt(
        id_vars=identifier_columns,
        value_vars=year_columns,
        var_name="Year",
        value_name="Debt Value"
    )

    long_df["Year"] = pd.to_numeric(
        long_df["Year"],
        errors="raise"
    ).astype("int64")

    # 8. Keep only rows with observed debt values.
    # Zero is a valid value and will be retained.
    missing_debt_values = int(long_df["Debt Value"].isna().sum())

    long_df = long_df.dropna(subset=["Debt Value"]).copy()

    report.append(
        f"Missing yearly debt observations excluded: "
        f"{missing_debt_values}"
    )
    report.append(
        f"Valid debt observations retained: {len(long_df)}"
    )

    # 9. Identify repeated country-indicator pairs.
    # Do not silently delete them; save them for investigation.
    repeated_pair_mask = long_df.duplicated(
        subset=["Country Code", "Series Code", "Year"],
        keep=False
    )

    repeated_pairs = long_df[repeated_pair_mask].copy()

    repeated_pairs.to_csv(
        OUTPUT_DIR / "repeated_country_indicator_years.csv",
        index=False
    )

    report.append(
        "Rows involved in repeated country-indicator-year "
        f"combinations: {len(repeated_pairs)}"
    )

    # 10. Save cleaned datasets
    long_df.to_csv(
        OUTPUT_DIR / "cleaned_debt_long.csv",
        index=False
    )

    # Also save the cleaned wide-format version
    df.to_csv(
        OUTPUT_DIR / "cleaned_debt_wide.csv",
        index=False
    )

    # 11. Save the report
    report.append(f"Final long-format rows: {len(long_df)}")
    report.append(
        f"Final long-format columns: {len(long_df.columns)}"
    )
    report.append("")
    report.append("Files created in data/processed/")
    report.append("- cleaned_debt_long.csv")
    report.append("- cleaned_debt_wide.csv")
    report.append("- exact_duplicates_for_review.csv")
    report.append("- rows_missing_identifiers.csv")
    report.append("- repeated_country_indicator_years.csv")

    report_text = "\n".join(report)

    report_file = OUTPUT_DIR / "cleaning_report.txt"
    report_file.write_text(report_text, encoding="utf-8")

    print("\n" + "=" * 55)
    print("CLEANING COMPLETED")
    print("=" * 55)
    print(report_text)
    print("\nAll output files saved in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
