import zipfile
import threading
import argparse
import pyarrow.csv as pv
import pyarrow.parquet as pq
import pyarrow as pa
import cache
from collections import defaultdict
import requests

parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("--rows", type=int, default=-1)
parser.add_argument("--cache", type=int, default=1000)
parser.add_argument("--threads", type=int, default=4)
args = parser.parse_args()

cache.init_cache(args.cache)

columns = ["state_code", "census_tract", "income"]

if args.datafile.endswith(".parquet"):
    table = pq.read_table(args.datafile, columns=columns)

elif args.datafile.endswith(".zip"):
    options = pv.ConvertOptions(
        include_columns=columns,
        column_types={
            "state_code": pa.string(),
            "census_tract": pa.string(),
            "income": pa.float64()
        }
    )
    with zipfile.ZipFile(args.datafile) as zf:
        inner_csv = zf.namelist()[0]
        with zf.open(inner_csv) as f:
            print("Reading CSV from ZIP...")
            table = pv.read_csv(f, convert_options=options)
            print("CSV loaded")

elif args.datafile.endswith(".csv"):
    options = pv.ConvertOptions(
        include_columns=columns,
        column_types={
            "state_code": pa.string(),
            "census_tract": pa.string(),
            "income": pa.float64()
        }
    )
    table = pv.read_csv(args.datafile, convert_options=options)

else:
    raise ValueError("Unsupported file type")

# Slice rows if needed
if args.rows > 0:
    table = table.slice(0, args.rows)

num_rows = table.num_rows

lock = threading.Lock()
state_counts = defaultdict(lambda: [0, 0])  # state -> [under_count, total_count]
total_hits = 0
total_requests = 0

def worker(start, end):
    global total_hits, total_requests
    local_hits = 0
    local_requests = 0

    for i in range(start, end):
        try:
            state = table.column("state_code")[i].as_py()
            tract = table.column("census_tract")[i].as_py()
            income = table.column("income")[i].as_py()

            # Validate tract
            if not tract or not tract.strip().isdigit():
                continue
            tract_int = int(tract.strip())
            if tract_int < 0:
                continue
            tract_norm = f"{tract_int:011d}"  # normalize to 11-digit string

            # Validate income
            if income is None:
                continue
            try:
                income_val = float(income)
            except:
                continue
            if income_val <= 0 or not income_val < float("inf"):
                continue

            url = f"http://server:8001/{tract_norm}"
            content, hit = cache.http_get(url, requests.Session())
            local_requests += 1

            if hit:
                local_hits += 1

            if content is None:
                continue

            tract_median = float(content)

            with lock:
                state_counts[state][1] += 1
                if income_val < tract_median:
                    state_counts[state][0] += 1

        except Exception as e:
            # Debug print for errors
            print(f"Worker error at row {i}: {e}")
            continue

    # Update global counters
    with lock:
        total_hits += local_hits
        total_requests += local_requests

threads = []
step = (num_rows + args.threads - 1) // args.threads

for t in range(args.threads):
    start = t * step
    end = min((t + 1) * step, num_rows)

    thread = threading.Thread(target=worker, args=(start, end))
    threads.append(thread)
    thread.start()

# Wait for threads
for thread in threads:
    thread.join()

for state in sorted(state_counts):
    under, total = state_counts[state]
    pct = int(100 * under / total) if total > 0 else 0
    print(f"{state}: {pct}% of {total}")

hit_rate = int(100 * total_hits / total_requests) if total_requests > 0 else 0
print(f"hit rate: {hit_rate}%")
print("rows:", num_rows)
print("requests:", total_requests)
print("hits:", total_hits)
