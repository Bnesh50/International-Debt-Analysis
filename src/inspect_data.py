
import pandas as pd
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "raw" / "IDS_ALLCountries_Data.csv"
OUTPUT_FILE = PROJECT_DIR / "data_inspection.txt"


def main():
    print("INTERNATIONAL DEBT ANALYSIS")
    print("=" * 50)

    # Check whether the dataset exists
    if not DATA_FILE.exists():
        print("ERROR: Dataset file not found.")
        print("Expected location:", DATA_FILE)
        return

    # Load the dataset
    print("\nLoading dataset...")
    df = pd.read_csv(
        DATA_FILE,
        encoding="cp1252",
        low_memory=False
    )

    # Capture the inspection results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as report:
        report.write("INTERNATIONAL DEBT ANALYSIS - DATA INSPECTION\n")
        report.write("=" * 60 + "\n")

        report.write(f"\nNumber of rows: {df.shape[0]}\n")
        report.write(f"Number of columns: {df.shape[1]}\n")

        report.write("\n--- COLUMN NAMES ---\n")
        report.write("\n".join(df.columns.astype(str)) + "\n")

        report.write("\n--- FIRST 5 ROWS ---\n")
        report.write(df.head().to_string(index=False) + "\n")

        report.write("\n--- DATA TYPES ---\n")
        report.write(df.dtypes.to_string() + "\n")

        report.write("\n--- DATASET INFORMATION ---\n")
        df.info(buf=report)

        report.write("\n\n--- MISSING VALUES ---\n")
        missing = df.isnull().sum()
        report.write(missing.to_string() + "\n")

        report.write("\n--- EXACT DUPLICATE ROWS ---\n")
        report.write(str(df.duplicated().sum()) + "\n")

        if "Country Code" in df.columns:
            report.write("\n--- UNIQUE COUNTRIES ---\n")
            report.write(str(df["Country Code"].nunique()) + "\n")

        if "Series Code" in df.columns:
            report.write("\n--- UNIQUE INDICATORS ---\n")
            report.write(str(df["Series Code"].nunique()) + "\n")

        if (
            "Country Code" in df.columns
            and "Series Code" in df.columns
        ):
            duplicate_pairs = df.duplicated(
                subset=["Country Code", "Series Code"],
                keep=False
            ).sum()

            report.write("\n--- COUNTRY-INDICATOR DUPLICATE ROWS ---\n")
            report.write(str(duplicate_pairs) + "\n")

    print("\nInspection completed successfully!")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Exact duplicate rows:", df.duplicated().sum())
    print("Report saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
