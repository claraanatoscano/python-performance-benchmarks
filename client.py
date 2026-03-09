import sys
import threading
import argparse
import pyarrow.csv as pv
import pyarrow.parquet as pq
import zipfile
import requests
import traceback
import cache
from collections import defaultdict
from pyarrow import string, float64
import pyarrow as pa
import argparse

# Ensure prints appear immediately in Docker
def safe_print(msg):
    print(msg, flush=True)

# Print uncaught exceptions immediately
sys.excepthook = lambda exc_type, exc_value, exc_tb: safe_print(
    "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("--rows", type=int, default=50000)
parser.add_argument("--cache", type=int, default=2000)
parser.add_argument("--threads", type=int, default=8)
parser.add_argument("--debug", action="store_true", help="Print debug info")
args = parser.parse_args()

# Initialize cache
cache.init_cache(args.cache)

# Columns to read
columns = ["state_code", "census_tract", "income"]
options = pv.ConvertOptions(
    include_columns=columns,
    column_types={"state_code": string(), "census_tract": string(), "income": float64()}
)

# Read the data file
try:
    if args.datafile.endswith(".parquet"):
        table = pq.read_table(args.datafile, columns=columns)
        safe_print(f"Read {table.num_rows} rows from Parquet")
    elif args.datafile.endswith(".zip"):
        with zipfile.ZipFile(args.datafile) as zf:
            inner_csv = zf.namelist()[0]  # CSV inside ZIP
            with zf.open(inner_csv) as f:
                table = pv.read_csv(f, convert_options=options)
        safe_print(f"Read {table.num_rows} rows from {inner_csv} in ZIP")
    elif args.datafile.endswith(".csv"):
        table = pv.read_csv(args.datafile, convert_options=options)
        safe_print(f"Read {table.num_rows} rows from CSV")
    else:
        raise ValueError("Unsupported file type")
except Exception as e:
    safe_print(f"Error reading file: {e}")
    sys.exit(1)

# Slice rows if needed
if args.rows > 0:
    table = table.slice(0, args.rows)

num_rows = table.num_rows
safe_print(f"Processing {num_rows} rows...")

# Thread-safe counters
lock = threading.Lock()
state_counts = defaultdict(lambda: [0, 0])  # state -> [under_count, total_count]
total_hits = 0

# Worker function
def worker(start, end):
    global total_hits
    local_hits = 0
    session = requests.Session()
    for i in range(start, end):
        try:
            state = table.column("state_code")[i].as_py()
            tract = table.column("census_tract")[i].as_py()
            income = table.column("income")[i].as_py()

            # Skip bad rows
            if not state or not tract or not income or income <= 0:
                continue

            url = f"http://server:8001/{tract}"
            content, hit = cache.http_get(url, session)
            if hit:
                local_hits += 1
            if content is None:
                continue

            tract_median = float(content)
            with lock:
                state_counts[state][1] += 1
                if income < tract_median:
                    state_counts[state][0] += 1
        except Exception as e:
            if args.debug:
                safe_print(f"Row {i} error: {e}")
            continue
    with lock:
        total_hits += local_hits

# Split work among threads
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

# Print results
for state in sorted(state_counts):
    under, total = state_counts[state]
    pct = int(100 * under / total) if total > 0 else 0
    safe_print(f"{state}: {pct}% of {total}")

hit_pct = int(100 * total_hits / num_rows) if num_rows > 0 else 0
safe_print(f"hit rate: {hit_pct}")
