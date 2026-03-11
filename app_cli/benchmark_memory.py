import subprocess
import csv
import re

container="p3-client-1"

sizes=list(range(10000,100001,10000))

rows=1000000

results=[]

for size in sizes:

    cmd=[
        "docker","exec",container,
        "python3.13-nogil",
        "/app/client.py",
        "/data/2021_public_lar.parquet",
        "--rows",str(rows),
        "--threads","4",
        "--cache",str(size)
    ]

    out=subprocess.check_output(cmd).decode()

    hit=re.search(r"hit rate: (\d+)%",out)

    if hit:
        results.append([size,int(hit.group(1))])

with open("memory.csv","w",newline="") as f:
    writer=csv.writer(f)
    writer.writerow(["cache","hit_rate"])
    writer.writerows(results)
