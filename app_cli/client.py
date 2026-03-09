import sys
import threading
import argparse
import pyarrow.csv as pv
import pyarrow.parquet as pq
import cache
from collections import defaultdict

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("datafile")
parser.add_argument("--rows", type=int, default=-1)
parser.add_argument("--cache", type=int, default=1000)
parser.add_argument("--threads", type=int, default=4)
args = parser.parse_args()

# Initialize cache
cache.init_cache(args.cache)

# Read the data file
columns = ["state_code", "census_tract", "income"]
if args.datafile.endswith(".parquet"):
    table = pq.read_table(args.datafile, columns=columns)
elif args.datafile.endswith(".zip") or args.datafile.endswith(".csv"):
    options = pv.ConvertOptions(include_columns=columns)
    table = pv.read_csv(args.datafile, convert_options=options)
else:
    raise ValueError("Unsupported file type")

# Slice rows if needed
if args.rows > 0:
    table = table.slice(0, args.rows)

num_rows = table.num_rows

# Thread-safe counters
lock = threading.Lock()
state_counts = defaultdict(lambda: [0,0])  # state -> [under_count, total_count]
total_hits = 0

# Worker function
def worker(start, end):
    global total_hits
    local_hits = 0
    for i in range(start, end):
        try:
            state = table.column("state_code")[i].as_py()
            tract = table.column("census_tract")[i].as_py()
            income = table.column("income")[i].as_py()

            if not tract or not state or not income or income <= 0:
                continue

            url = f"http://server:8001/{tract}"
            content, hit = cache.http_get(url, requests.Session())
            if hit:
                local_hits += 1
            if content is None:
                continue

            tract_median = float(content)
            with lock:
                state_counts[state][1] += 1
                if income < tract_median:
                    state_counts[state][0] += 1
        except:
            continue
    with lock:
        total_hits += local_hits

# Split work among threads
threads = []
step = (num_rows + args.threads - 1) // args.threads
for t in range(args.threads):
    start = t * step
    end = min((t+1)*step, num_rows)
    thread = threading.Thread(target=worker, args=(start,end))
    threads.append(thread)
    thread.start()

# Wait for threads
for thread in threads:
    thread.join()

# Print results
for state in sorted(state_counts):
    under, total = state_counts[state]
    pct = int(100*under/total)
    print(f"{state}: {pct}% of {total}")

print(f"hit rate: {int(100*total_hits/num_rows)}")
