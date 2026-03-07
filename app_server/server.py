import flask
import pandas as pd
import os

app = flask.Flask(__name__)

DATA_PATH = os.environ.get("ACS_DATA", "/data/acs5_2021_tract_income_us.csv")

print(f"Server: Loading ACS tract income dataset from {DATA_PATH}...")
census_df = pd.read_csv(DATA_PATH, low_memory=False)

if "tract_geoid" not in census_df.columns:
    raise ValueError("ACS file must include 'tract_geoid' column")
if "median_household_income" not in census_df.columns:
    raise ValueError("ACS file must include 'median_household_income' column")

census_df["median_income_k"] = (
    pd.to_numeric(census_df["median_household_income"], errors="coerce") / 1000.0
)
census_df["tract_geoid"] = census_df["tract_geoid"].astype(str).str.zfill(11)
census_df = census_df.dropna(subset=["tract_geoid", "median_income_k"])

tract_income_map = dict(
    zip(census_df["tract_geoid"].tolist(), census_df["median_income_k"].tolist())
)
print(f"Serving {len(tract_income_map)} tract median-income records.")


@app.route("/<tract_geoid>")
def lookup(tract_geoid):
    if tract_geoid in tract_income_map:
        return str(tract_income_map[tract_geoid]), 200
    return "", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
