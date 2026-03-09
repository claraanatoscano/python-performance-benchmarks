#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.census.gov/data/2021/acs/acs5"


def get_json(url: str, session: requests.Session, timeout: int = 60):
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_states(session: requests.Session):
    data = get_json(f"{BASE}?get=NAME&for=state:*", session)
    rows = data[1:]
    states = [row[1] for row in rows if row[1].isdigit()]
    return sorted(states)


def fetch_state_tract_income(state: str):
    with requests.Session() as session:
        url = (
            f"{BASE}?get=NAME,B19013_001E&for=tract:*"
            f"&in=state:{state}&in=county:*"
        )
        data = get_json(url, session)

    cols = data[0]
    df = pd.DataFrame(data[1:], columns=cols)
    df["tract_geoid"] = df["state"].str.zfill(2) + df["county"].str.zfill(3) + df["tract"].str.zfill(6)
    df = df.rename(columns={"B19013_001E": "median_household_income"})
    return df[["tract_geoid", "median_household_income", "NAME", "state", "county", "tract"]]


def main():
    parser = argparse.ArgumentParser(description="Download US ACS 5-year tract median household income")
    parser.add_argument("--year", type=int, default=2021)
    parser.add_argument("--out", default="inputs/raw/acs5_2021_tract_income_us.csv")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    if args.year != 2021:
        raise ValueError("This script is currently pinned to 2021 ACS 5-year endpoint")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        states = fetch_states(session)

    frames = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut_to_state = {ex.submit(fetch_state_tract_income, st): st for st in states}
        for fut in as_completed(fut_to_state):
            st = fut_to_state[fut]
            try:
                frames.append(fut.result())
                print(f"Fetched state {st}")
            except Exception as e:
                print(f"Failed state {st}: {e}")

    if not frames:
        raise RuntimeError("No state data downloaded")

    all_df = pd.concat(frames, ignore_index=True)
    all_df["median_household_income"] = pd.to_numeric(all_df["median_household_income"], errors="coerce")
    all_df = all_df.sort_values("tract_geoid")

    all_df.to_csv(out_path, index=False)
    print(f"Wrote {len(all_df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
