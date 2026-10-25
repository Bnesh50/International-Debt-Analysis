
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# INTERNATIONAL DEBT ANALYSIS
# Country-level external debt analysis

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "processed" / "cleaned_debt_long.csv"
COUNTRY_FILE = PROJECT_DIR / "data" / "raw" / "IDS_CountryMetaData.csv"
REPORT_DIR = PROJECT_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"

INDICATOR_CODE = "DT.DOD.DECT.CD"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 60)
    print("INTERNATIONAL DEBT ANALYSIS")
    print("=" * 60)

    # Load cleaned observations
    debt = pd.read_csv(DATA_FILE, low_memory=False)

    # Load country metadata
    countries = pd.read_csv(
        COUNTRY_FILE,
        encoding="cp1252",
        low_memory=False
    )

    # Select total external debt stocks
    debt = debt[
        debt["Series Code"].astype(str).str.strip()
        == INDICATOR_CODE
    ].copy()

    if debt.empty:
        print("ERROR: Debt indicator was not found.")
        return

    # Check metadata structure
    required_metadata = ["Code", "Long Name", "Region"]

    missing = [
        column for column in required_metadata
        if column not in countries.columns
    ]

    if missing:
        print("ERROR: Metadata columns missing:", missing)
        print("Available columns:", countries.columns.tolist())
        return

    # Keep actual country records with a populated region.
    # Aggregate groups in this metadata generally have blank regions.
    countries["Code"] = countries["Code"].astype(str).str.strip()
    countries["Region"] = countries["Region"].fillna("").astype(str).str.strip()

    valid_countries = countries[
        countries["Region"].ne("")
        & countries["Code"].ne("")
    ].copy()

    valid_codes = set(valid_countries["Code"])

    debt["Country Code"] = (
        debt["Country Code"].astype(str).str.strip()
    )

    debt = debt[
        debt["Country Code"].isin(valid_codes)
    ].copy()

    # Convert values
    debt["Year"] = pd.to_numeric(debt["Year"], errors="coerce")
    debt["Debt Value"] = pd.to_numeric(
        debt["Debt Value"], errors="coerce"
    )

    debt = debt.dropna(
        subset=["Year", "Debt Value"]
    ).copy()

    if debt.empty:
        print("ERROR: No valid country-level observations remain.")
        return

    # Add country classifications
    country_columns = [
        "Code",
        "Long Name",
        "Region",
        "Income Group"
    ]

    country_columns = [
        column for column in country_columns
        if column in valid_countries.columns
    ]

    country_lookup = valid_countries[country_columns].drop_duplicates(
        subset=["Code"]
    )

    debt = debt.merge(
        country_lookup,
        left_on="Country Code",
        right_on="Code",
        how="left"
    )

    debt = debt.drop(columns=["Code"], errors="ignore")

    # Save verified country-level observations
    debt.to_csv(
        REPORT_DIR / "external_debt_country_observations.csv",
        index=False
    )

    # Latest available value per country
    latest = (
        debt.sort_values("Year")
        .groupby("Country Code", as_index=False)
        .tail(1)
        .sort_values("Debt Value", ascending=False)
    )

    ranking_columns = [
        "Country Name",
        "Country Code",
        "Region",
        "Income Group",
        "Year",
        "Debt Value"
    ]

    ranking_columns = [
        column for column in ranking_columns
        if column in latest.columns
    ]

    latest = latest[ranking_columns]

    latest.to_csv(
        REPORT_DIR / "latest_external_debt_by_country.csv",
        index=False
    )

    # Top 10 country ranking
    top10 = latest.head(10).sort_values("Debt Value")

    plt.figure(figsize=(12, 7))
    plt.barh(top10["Country Name"], top10["Debt Value"])
    plt.title("Top 10 Countries by Latest Available External Debt")
    plt.xlabel("External debt stocks (current US$)")
    plt.ylabel("Country")
    plt.tight_layout()
    plt.savefig(
        CHART_DIR / "top_10_external_debt.png",
        dpi=150
    )
    plt.close()

    # Yearly country coverage
    yearly = (
        debt.groupby("Year")
        .agg(
            Countries=("Country Code", "nunique"),
            Observations=("Debt Value", "count")
        )
        .reset_index()
        .sort_values("Year")
    )

    yearly.to_csv(
        REPORT_DIR / "external_debt_yearly_coverage.csv",
        index=False
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        yearly["Year"],
        yearly["Countries"],
        marker="o"
    )
    plt.title("Country Coverage for External Debt Stocks")
    plt.xlabel("Year")
    plt.ylabel("Countries with recorded observations")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        CHART_DIR / "external_debt_country_coverage.png",
        dpi=150
    )
    plt.close()

    # Create report
    report = [
        "INTERNATIONAL DEBT ANALYSIS REPORT",
        "=" * 50,
        f"Indicator code: {INDICATOR_CODE}",
        "Indicator: External debt stocks, total (DOD, current US$)",
        f"Country count: {debt['Country Code'].nunique()}",
        f"Observation count: {len(debt)}",
        f"First year: {int(debt['Year'].min())}",
        f"Latest year: {int(debt['Year'].max())}",
        "",
        "TOP 10 COUNTRIES BY LATEST AVAILABLE OBSERVATION",
        latest.head(10).to_string(index=False)
    ]

    (REPORT_DIR / "external_debt_analysis_report.txt").write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("\nAnalysis completed successfully!")
    print("Indicator:", INDICATOR_CODE)
    print("Country count:", debt["Country Code"].nunique())
    print("Observations:", len(debt))
    print("Year range:", int(debt["Year"].min()), "to", int(debt["Year"].max()))
    print("\nTop 10 countries:")
    print(latest.head(10).to_string(index=False))
    print("\nReport saved to:", REPORT_DIR)


if __name__ == "__main__":
    main()
