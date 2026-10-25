import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from mysql.connector import Error

st.set_page_config(
    page_title="International Debt Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# MySQL connection settings
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "international_debt_analysis",
}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: #151a24;
        border: 1px solid #293241;
        padding: 15px 18px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_sql(query, params=None):
    """Run a parameterized query using a fresh MySQL connection."""
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        # Queries that return rows have cursor.description populated.
        if cursor.description is None:
            return pd.DataFrame()

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame(rows, columns=columns)

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@st.cache_data(ttl=300)
def load_filter_options():
    countries = read_sql(
        """
        SELECT DISTINCT country_code, country_name
        FROM countries
        WHERE country_name IS NOT NULL
        ORDER BY country_name
        """
    )
    indicators = read_sql(
        """
        SELECT d.indicator_code, d.indicator_name
        FROM debt_indicators d
        WHERE EXISTS (
            SELECT 1
            FROM debt_observations o
            WHERE o.indicator_code = d.indicator_code
              AND o.debt_value IS NOT NULL
        )
        ORDER BY d.indicator_name, d.indicator_code
        """
    )
    years = read_sql(
        """
        SELECT MIN(year) AS min_year, MAX(year) AS max_year
        FROM debt_observations
        WHERE debt_value IS NOT NULL
        """
    )
    return countries, indicators, years


def placeholders(values):
    return ", ".join(["%s"] * len(values))


def format_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    if decimals:
        return f"{float(value):,.{decimals}f}"
    return f"{int(value):,}"


st.title("🌍 International Debt Analysis")
st.caption(
    "Explore international debt observations by country, indicator, and year. "
    "Use the filters to update the trend, country comparison, indicator coverage, and records."
)

try:
    countries_df, indicators_df, year_df = load_filter_options()
    overall_df = read_sql(
        """
        SELECT
            COUNT(*) AS total_observations,
            COUNT(DISTINCT country_code) AS total_countries,
            COUNT(DISTINCT indicator_code) AS observed_indicators,
            MIN(year) AS first_year,
            MAX(year) AS latest_year
        FROM debt_observations
        WHERE debt_value IS NOT NULL
        """
    )
except Error as exc:
    st.error(
        "Could not connect to MySQL or read the dashboard tables. Check that MySQL is running "
        "and that the credentials in dashboard/app.py are correct."
    )
    st.code(str(exc))
    st.stop()
except Exception as exc:
    st.error("Could not load dashboard data. Check the database tables and column names.")
    st.code(str(exc))
    st.stop()

if countries_df.empty or indicators_df.empty or year_df.empty:
    st.warning("The database does not contain enough country, indicator, or year data.")
    st.stop()

min_year = int(year_df.iloc[0]["min_year"])
max_year = int(year_df.iloc[0]["max_year"])
overall = overall_df.iloc[0]

# Sidebar filters
st.sidebar.header("Dashboard Filters")
country_options = countries_df["country_name"].dropna().tolist()
selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=country_options,
    default=[],
    help="Leave empty to include all countries.",
)

year_range = st.sidebar.slider(
    "Select year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)
start_year, end_year = year_range

indicator_labels = []
label_to_code = {}
label_to_name = {}
for _, row in indicators_df.iterrows():
    code = str(row["indicator_code"])
    name = str(row["indicator_name"])
    label = f"{name} [{code}]"
    indicator_labels.append(label)
    label_to_code[label] = code
    label_to_name[label] = name

selected_indicator_label = st.sidebar.selectbox(
    "Select one debt indicator",
    options=indicator_labels,
    index=0,
    help="One indicator is selected at a time because indicators can use different units.",
)
selected_indicator_code = label_to_code[selected_indicator_label]
selected_indicator_name = label_to_name[selected_indicator_label]

selected_country_codes = []
if selected_countries:
    selected_country_codes = (
        countries_df.loc[
            countries_df["country_name"].isin(selected_countries), "country_code"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

country_filter = ""
if selected_country_codes:
    country_filter = f" AND o.country_code IN ({placeholders(selected_country_codes)})"

# Overall database KPIs (independent of sidebar filters)
st.subheader("Database Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Countries in database", format_number(overall["total_countries"]))
k2.metric("Observed indicators", format_number(overall["observed_indicators"]))
k3.metric("Total observations", format_number(overall["total_observations"]))
k4.metric(
    "Year coverage",
    f"{int(overall['first_year'])}–{int(overall['latest_year'])}",
)

st.markdown("---")
st.subheader("Filtered Data Summary")
st.caption(
    f"Indicator: {selected_indicator_name} | Years: {start_year}–{end_year} | "
    + (f"Countries selected: {len(selected_country_codes)}" if selected_country_codes else "All countries")
)

filtered_params = [selected_indicator_code, start_year, end_year]
filtered_params.extend(selected_country_codes)
filtered_summary = read_sql(
    f"""
    SELECT
        COUNT(*) AS observation_count,
        COUNT(DISTINCT o.country_code) AS country_count,
        MIN(o.year) AS first_year,
        MAX(o.year) AS last_year,
        AVG(o.debt_value) AS average_value
    FROM debt_observations o
    WHERE o.indicator_code = %s
      AND o.year BETWEEN %s AND %s
      AND o.debt_value IS NOT NULL
      {country_filter}
    """,
    filtered_params,
).iloc[0]

s1, s2, s3, s4 = st.columns(4)
s1.metric("Filtered observations", format_number(filtered_summary["observation_count"]))
s2.metric("Countries with data", format_number(filtered_summary["country_count"]))
s3.metric("Average value", format_number(filtered_summary["average_value"], 2))
if pd.notna(filtered_summary["first_year"]):
    filtered_year_text = f"{int(filtered_summary['first_year'])}–{int(filtered_summary['last_year'])}"
else:
    filtered_year_text = "—"
s4.metric("Available years", filtered_year_text)

st.subheader("Selected Indicator")
st.write(f"**{selected_indicator_name}**")
st.caption(
    "Values are shown in the source dataset's units. Different indicators may measure "
    "different concepts, so values should not be compared across indicators without checking definitions."
)

# Trend chart
st.subheader("Debt Trend Over Time")
trend_params = [selected_indicator_code, start_year, end_year]
trend_params.extend(selected_country_codes)
trend_df = read_sql(
    f"""
    SELECT
        o.year,
        AVG(o.debt_value) AS average_value,
        COUNT(*) AS observation_count
    FROM debt_observations o
    WHERE o.indicator_code = %s
      AND o.year BETWEEN %s AND %s
      AND o.debt_value IS NOT NULL
      {country_filter}
    GROUP BY o.year
    ORDER BY o.year
    """,
    trend_params,
)

if trend_df.empty:
    st.info("No observations match the selected filters.")
else:
    trend_fig = px.line(
        trend_df,
        x="year",
        y="average_value",
        markers=True,
        title=f"Average value by year — {selected_indicator_name}",
        labels={
            "year": "Year",
            "average_value": "Average value (source units)",
            "observation_count": "Observations",
        },
        hover_data={"observation_count": True, "average_value": ":,.2f"},
    )
    trend_fig.update_layout(
        template="plotly_dark",
        height=430,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(trend_fig, use_container_width=True)

# Top 10 countries by latest available value for selected indicator
st.subheader("Country Comparison")
st.caption(
    "Top 10 countries ranked by each country's latest non-null value for the selected indicator "
    "within the selected year range."
)
comparison_country_filter = ""
comparison_country_params = []
if selected_country_codes:
    comparison_country_filter = f" AND o.country_code IN ({placeholders(selected_country_codes)})"
    comparison_country_params.extend(selected_country_codes)

comparison_params = [selected_indicator_code, start_year, end_year, selected_indicator_code]
comparison_params.extend(comparison_country_params)
comparison_df = read_sql(
    f"""
    SELECT
        c.country_code,
        c.country_name,
        o.year AS latest_year,
        o.debt_value
    FROM debt_observations o
    INNER JOIN countries c ON c.country_code = o.country_code
    INNER JOIN (
        SELECT country_code, MAX(year) AS latest_year
        FROM debt_observations
        WHERE indicator_code = %s
          AND year BETWEEN %s AND %s
          AND debt_value IS NOT NULL
        GROUP BY country_code
    ) latest
      ON latest.country_code = o.country_code
     AND latest.latest_year = o.year
    WHERE o.indicator_code = %s
      AND o.debt_value IS NOT NULL
      {comparison_country_filter}
    ORDER BY o.debt_value DESC
    LIMIT 10
    """,
    comparison_params,
)

if comparison_df.empty:
    st.info("No country values are available for this indicator and year range.")
else:
    comparison_fig = px.bar(
        comparison_df.sort_values("debt_value", ascending=True),
        x="debt_value",
        y="country_name",
        orientation="h",
        hover_data={"latest_year": True, "debt_value": ":,.2f"},
        title="Top 10 countries by latest available value",
        labels={
            "debt_value": "Value (source units)",
            "country_name": "Country",
            "latest_year": "Latest observation year",
        },
    )
    comparison_fig.update_layout(
        template="plotly_dark",
        height=max(380, 42 * len(comparison_df)),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(comparison_fig, use_container_width=True)

    comparison_display = comparison_df[["country_name", "latest_year", "debt_value"]].rename(
        columns={"country_name": "Country", "latest_year": "Latest year", "debt_value": "Value"}
    )
    st.dataframe(
        comparison_display.style.format({"Value": "{:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

# Indicator analysis chart
st.subheader("Indicator Analysis")
st.caption(
    "The 15 most frequently observed indicators for the selected countries and years. "
    "Hover over a bar to compare total observations, countries covered, and years covered. "
    "If bars have equal lengths, those indicators have the same number of observations in the selected filters."
)
coverage_params = [start_year, end_year]
coverage_params.extend(selected_country_codes)
coverage_df = read_sql(
    f"""
    SELECT
        d.indicator_code,
        d.indicator_name,
        COUNT(*) AS observation_count,
        COUNT(DISTINCT o.country_code) AS countries_covered,
        COUNT(DISTINCT o.year) AS years_covered
    FROM debt_observations o
    INNER JOIN debt_indicators d ON d.indicator_code = o.indicator_code
    WHERE o.year BETWEEN %s AND %s
      AND o.debt_value IS NOT NULL
      {country_filter}
    GROUP BY d.indicator_code, d.indicator_name
    ORDER BY observation_count DESC, d.indicator_name
    LIMIT 15
    """,
    coverage_params,
)

if coverage_df.empty:
    st.info("No indicator coverage data is available for the selected filters.")
else:
    coverage_plot_df = coverage_df.sort_values(
        ["observation_count", "indicator_name"], ascending=[True, True]
    )
    coverage_fig = px.bar(
        coverage_plot_df,
        x="observation_count",
        y="indicator_name",
        orientation="h",
        text="observation_count",
        hover_data={
            "indicator_code": True,
            "observation_count": ":,",
            "countries_covered": True,
            "years_covered": True,
        },
        title="15 most frequently observed indicators",
        labels={
            "observation_count": "Number of observations",
            "indicator_name": "Debt indicator",
            "indicator_code": "Indicator code",
            "countries_covered": "Countries covered",
            "years_covered": "Years covered",
        },
    )
    coverage_fig.update_traces(textposition="outside", cliponaxis=False)
    coverage_fig.update_layout(
        template="plotly_dark",
        height=max(520, 34 * len(coverage_plot_df)),
        margin=dict(l=20, r=70, t=60, b=20),
        xaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(coverage_fig, use_container_width=True)

    st.dataframe(
        coverage_df[[
            "indicator_name", "observation_count", "countries_covered", "years_covered"
        ]].rename(columns={
            "indicator_name": "Indicator",
            "observation_count": "Observations",
            "countries_covered": "Countries covered",
            "years_covered": "Years covered",
        }),
        use_container_width=True,
        hide_index=True,
    )

# Records and export
st.subheader("Debt Observation Records")
st.caption("Showing up to 1,000 records matching the selected indicator, countries, and year range.")
records_params = [selected_indicator_code, start_year, end_year]
records_params.extend(selected_country_codes)
records_df = read_sql(
    f"""
    SELECT c.country_name, d.indicator_name, o.year, o.debt_value
    FROM debt_observations o
    INNER JOIN countries c ON c.country_code = o.country_code
    INNER JOIN debt_indicators d ON d.indicator_code = o.indicator_code
    WHERE o.indicator_code = %s
      AND o.year BETWEEN %s AND %s
      AND o.debt_value IS NOT NULL
      {country_filter}
    ORDER BY o.year DESC, c.country_name
    LIMIT 1000
    """,
    records_params,
)

records_display = records_df.rename(
    columns={
        "country_name": "Country",
        "indicator_name": "Indicator",
        "year": "Year",
        "debt_value": "Value",
    }
)
st.dataframe(
    records_display.style.format({"Value": "{:,.2f}"}),
    use_container_width=True,
    hide_index=True,
)

if not records_df.empty:
    st.download_button(
        "Download filtered data as CSV",
        data=records_df.to_csv(index=False).encode("utf-8"),
        file_name="international_debt_filtered_data.csv",
        mime="text/csv",
    )
else:
    st.info("No records are available to download for the current filters.")

st.info(
    "Data note: the dataset includes years beyond the current year. These may be projections or estimates; "
    "verify the source metadata before describing them as actual historical outcomes. Debt indicators can "
    "also use different definitions and units."
)
st.caption("International Debt Analysis • Streamlit + MySQL")
