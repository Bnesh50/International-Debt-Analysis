
import csv
import os

file_path = "data/raw/IDS_ALLCountries_Data.csv"

print("File exists:", os.path.exists(file_path))

with open(file_path, "r", encoding="latin1", newline="") as file:
    reader = csv.DictReader(file)

    print("CSV columns:", reader.fieldnames)

    found = 0

    for row in reader:
        country = row.get("Country Code", "").strip()
        series = row.get("Series Code", "").strip()

        if country in ["WSM", "TLS", "SOM"] and series == "DT.GPA.PRVT":
            found += 1
            print("\nCountry:", row.get("Country Name"))
            print("Code:", country)

            for year in ["2000", "2010", "2015", "2020", "2024"]:
                print(year + ":", row.get(year))

    print("\nMatching records found:", found)
