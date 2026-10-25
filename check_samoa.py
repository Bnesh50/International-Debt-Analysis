import pandas as pd

file_path = "data/raw/IDS_ALLCountries_Data.csv"

df = pd.read_csv(file_path, encoding="latin1", low_memory=False)

countries = ["WSM", "TLS", "SOM"]

for country in countries:
    row = df[
        (df["Country Code"] == country) &
        (df["Series Code"] == "DT.GPA.PRVT")
    ]

    print("\nCountry:", country)

    if row.empty:
        print("No record found")
    else:
        for year in ["2000", "2010", "2015", "2020", "2024"]:
            print(year + ":", row[year].iloc[0])