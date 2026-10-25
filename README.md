# International Debt Analysis System

A Python, MySQL, and Streamlit project for cleaning, exploring, storing, and visualizing international debt data.

## Project structure
- `data/raw/` — source CSV datasets and metadata.
- `data/processed/` — cleaned wide/long datasets and cleaning audit outputs.
- `src/clean_data.py` — data cleaning and reshaping.
- `src/eda.py` — exploratory data analysis and report/chart generation.
- `src/load_to_mysql.py` — loads processed data into MySQL.
- `src/` — supporting inspection and validation scripts.
- `sql/debt_analysis.sql` — existing SQL analysis queries.
- `sql/debt_analysis_30_queries.sql` — 30-query assignment set (review/run in your own MySQL environment before submission).
- `dashboard/app.py` — Streamlit dashboard.
- `reports/` — generated charts, analysis outputs, and documentation.

## Setup
Use Python 3.10+ if compatible with your installed dependencies. From this folder, create and activate a virtual environment, then install packages listed in `requirements.txt`.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Typical workflow
1. Put the source CSV and metadata files in `data/raw/`.
2. Run `python src/clean_data.py` from the project root. Confirm the input filename/path in the script matches the file you have.
3. Run `python src/eda.py` from the project root. Confirm configured paths and target indicator before running.
4. Create the required MySQL database and tables, configure the connection settings locally, then run `python src/load_to_mysql.py`. Do not commit real passwords.
5. Run `streamlit run dashboard/app.py` from the project root.
6. Open the SQL file in MySQL Workbench and execute queries individually; validate results against the assignment question list.

## Important notes
- The exact paths, database name, username, and password depend on your local setup. Check the configuration in the scripts before running.
- `sql/debt_analysis_30_queries.sql` is included as an assignment query set, but its full execution has not been independently certified.
- The data contains non-missing values in future years. Do not label them all as forecasts unless the source documentation confirms that interpretation.
- `.venv/` is intentionally excluded from this submission archive; recreate it with `requirements.txt`.
