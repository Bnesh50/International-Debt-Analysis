
import math
import pandas as pd
import mysql.connector
from pathlib import Path

# ==========================================
# INTERNATIONAL DEBT ANALYSIS
# MYSQL DATA LOADER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

COUNTRY_FILE = BASE_DIR / "data" / "raw" / "IDS_CountryMetaData.csv"
INDICATOR_FILE = BASE_DIR / "data" / "raw" / "IDS_SeriesMetaData.csv"
DEBT_FILE = BASE_DIR / "data" / "processed" / "cleaned_debt_long.csv"

REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

INVALID_FILE = REPORT_DIR / "observations_missing_metadata.csv"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "international_debt_analysis"
}

BATCH_SIZE = 2000


def safe_value(value):
    """Convert missing values to Python None for MySQL."""

    if value is None or pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    return value


def clean_code(value):
    """Clean a country or indicator code."""

    value = safe_value(value)

    if value is None:
        return None

    return str(value).strip()


def safe_records(dataframe):
    """Convert a DataFrame to Python tuples for MySQL."""

    return [
        tuple(safe_value(value) for value in row)
        for row in dataframe.itertuples(index=False, name=None)
    ]


def load_batches(cursor, connection, sql, records, label):
    """Insert data in batches."""

    total = len(records)

    for start in range(0, total, BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        cursor.executemany(sql, batch)
        connection.commit()

        completed = min(start + len(batch), total)
        print(f"{label}: {completed:,} / {total:,}")


def main():
    connection = None
    cursor = None

    print("=" * 60)
    print("INTERNATIONAL DEBT ANALYSIS - MYSQL DATA LOADER")
    print("=" * 60)

    try:
        # ------------------------------------------
        # CHECK FILES
        # ------------------------------------------

        for file_path in [COUNTRY_FILE, INDICATOR_FILE, DEBT_FILE]:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

        # ------------------------------------------
        # READ DATASETS
        # ------------------------------------------

        print("\nReading CSV files...")

        countries = pd.read_csv(
            COUNTRY_FILE,
            encoding="cp1252",
            low_memory=False
        )

        indicators = pd.read_csv(
            INDICATOR_FILE,
            encoding="cp1252",
            low_memory=False
        )

        debt = pd.read_csv(
            DEBT_FILE,
            low_memory=False
        )

        print(f"Country metadata: {len(countries):,}")
        print(f"Indicator metadata: {len(indicators):,}")
        print(f"Debt observations: {len(debt):,}")

        # ------------------------------------------
        # PREPARE COUNTRIES
        # ------------------------------------------

        country_data = countries.rename(columns={
            "Code": "country_code",
            "Long Name": "country_name",
            "Region": "region",
            "Income Group": "income_group"
        })

        country_columns = [
            "country_code",
            "country_name",
            "region",
            "income_group"
        ]

        if not all(c in country_data.columns for c in country_columns):
            raise ValueError(
                f"Unexpected country columns: {countries.columns.tolist()}"
            )

        country_data = country_data[country_columns].copy()

        country_data["country_code"] = (
            country_data["country_code"].map(clean_code)
        )
        country_data["country_name"] = (
            country_data["country_name"].map(safe_value)
        )
        country_data["region"] = country_data["region"].map(safe_value)
        country_data["income_group"] = (
            country_data["income_group"].map(safe_value)
        )

        country_data = country_data.dropna(
            subset=["country_code", "country_name"]
        )

        country_data = country_data.drop_duplicates(
            subset=["country_code"],
            keep="first"
        )

        valid_country_codes = set(country_data["country_code"])

        # ------------------------------------------
        # PREPARE INDICATORS
        # ------------------------------------------

        indicator_data = indicators.rename(columns={
            "Code": "indicator_code",
            "Indicator Name": "indicator_name",
            "Short definition": "short_definition"
        })

        indicator_columns = [
            "indicator_code",
            "indicator_name",
            "short_definition"
        ]

        if not all(c in indicator_data.columns for c in indicator_columns):
            raise ValueError(
                f"Unexpected indicator columns: "
                f"{indicators.columns.tolist()}"
            )

        indicator_data = indicator_data[indicator_columns].copy()

        indicator_data["indicator_code"] = (
            indicator_data["indicator_code"].map(clean_code)
        )
        indicator_data["indicator_name"] = (
            indicator_data["indicator_name"].map(safe_value)
        )
        indicator_data["short_definition"] = (
            indicator_data["short_definition"].map(safe_value)
        )

        indicator_data = indicator_data.dropna(
            subset=["indicator_code", "indicator_name"]
        )

        indicator_data = indicator_data.drop_duplicates(
            subset=["indicator_code"],
            keep="first"
        )

        valid_indicator_codes = set(indicator_data["indicator_code"])

        # ------------------------------------------
        # PREPARE DEBT OBSERVATIONS
        # ------------------------------------------

        debt_data = debt.rename(columns={
            "Country Code": "country_code",
            "Series Code": "indicator_code",
            "Year": "year",
            "Debt Value": "debt_value"
        })

        debt_columns = [
            "country_code",
            "indicator_code",
            "year",
            "debt_value"
        ]

        if not all(c in debt_data.columns for c in debt_columns):
            raise ValueError(
                f"Unexpected debt columns: {debt.columns.tolist()}"
            )

        debt_data = debt_data[debt_columns].copy()

        debt_data["country_code"] = (
            debt_data["country_code"].map(clean_code)
        )
        debt_data["indicator_code"] = (
            debt_data["indicator_code"].map(clean_code)
        )

        debt_data["year"] = pd.to_numeric(
            debt_data["year"],
            errors="coerce"
        )

        debt_data["debt_value"] = pd.to_numeric(
            debt_data["debt_value"],
            errors="coerce"
        )

        debt_data = debt_data.dropna(
            subset=["country_code", "indicator_code", "year"]
        )

        debt_data = debt_data[
            debt_data["year"].between(-32768, 32767)
        ].copy()

        debt_data["year"] = debt_data["year"].astype(int)

        # Remove exact duplicate observation keys
        debt_data = debt_data.drop_duplicates(
            subset=["country_code", "indicator_code", "year"],
            keep="first"
        )

        # ------------------------------------------
        # VALIDATE FOREIGN KEY REFERENCES
        # ------------------------------------------

        print("\nChecking country and indicator codes...")

        unknown_country = ~debt_data["country_code"].isin(
            valid_country_codes
        )

        unknown_indicator = ~debt_data["indicator_code"].isin(
            valid_indicator_codes
        )

        invalid_mask = unknown_country | unknown_indicator

        invalid_data = debt_data.loc[invalid_mask].copy()

        if not invalid_data.empty:
            invalid_data["validation_issue"] = ""

            invalid_data.loc[
                unknown_country[invalid_mask],
                "validation_issue"
            ] = "Unknown country code"

            both_unknown = (
                unknown_country & unknown_indicator
            )[invalid_mask]

            invalid_data.loc[
                both_unknown,
                "validation_issue"
            ] = "Unknown country and indicator codes"

            indicator_only = (
                ~unknown_country & unknown_indicator
            )[invalid_mask]

            invalid_data.loc[
                indicator_only,
                "validation_issue"
            ] = "Unknown indicator code"

            invalid_data.to_csv(INVALID_FILE, index=False)

            print(f"Unmatched observations: {len(invalid_data):,}")
            print(f"Review report: {INVALID_FILE}")
        else:
            print("All observation codes match the metadata.")

        valid_debt_data = debt_data.loc[~invalid_mask].copy()

        print(f"Valid observations: {len(valid_debt_data):,}")

        country_records = safe_records(country_data)
        indicator_records = safe_records(indicator_data)
        debt_records = safe_records(valid_debt_data)

        print("\nPrepared records:")
        print(f"Countries: {len(country_records):,}")
        print(f"Indicators: {len(indicator_records):,}")
        print(f"Valid observations: {len(debt_records):,}")

        # ------------------------------------------
        # CONNECT TO MYSQL
        # ------------------------------------------

        print("\nConnecting to MySQL...")

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("MySQL connection successful!")

        # ------------------------------------------
        # LOAD COUNTRIES
        # ------------------------------------------

        country_sql = """
            INSERT INTO countries
                (country_code, country_name, region, income_group)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                country_name = VALUES(country_name),
                region = VALUES(region),
                income_group = VALUES(income_group)
        """

        print("\nLoading countries...")

        load_batches(
            cursor, connection,
            country_sql, country_records, "Countries"
        )

        # ------------------------------------------
        # LOAD INDICATORS
        # ------------------------------------------

        indicator_sql = """
            INSERT INTO debt_indicators
                (indicator_code, indicator_name, short_definition)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                indicator_name = VALUES(indicator_name),
                short_definition = VALUES(short_definition)
        """

        print("\nLoading indicators...")

        load_batches(
            cursor, connection,
            indicator_sql, indicator_records, "Indicators"
        )

        # ------------------------------------------
        # LOAD OBSERVATIONS
        # ------------------------------------------

        observation_sql = """
            INSERT INTO debt_observations
                (country_code, indicator_code, year, debt_value)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                debt_value = VALUES(debt_value)
        """

        print("\nLoading valid debt observations...")

        load_batches(
            cursor, connection,
            observation_sql, debt_records, "Observations"
        )

        # ------------------------------------------
        # VERIFY DATABASE
        # ------------------------------------------

        print("\nFinal database row counts:")

        for table in [
            "countries",
            "debt_indicators",
            "debt_observations"
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            print(f"{table}: {cursor.fetchone()[0]:,}")

        print("\nDATA LOADING COMPLETED SUCCESSFULLY!")

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        print("\nDATA LOADING FAILED.")
        print(f"{type(error).__name__}: {error}")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

        print("\nMySQL connection closed.")


if __name__ == "__main__":
    main()
