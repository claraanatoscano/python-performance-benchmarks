import subprocess
import csv
import time

container="p3-client-1"

threads=[1,2,4,8]

modes=[("gil_on","1"),("gil_off","0")]

rows=1000000
cache=50000

results=[]

for mode,gil in modes:

    for t in threads:

        start=time.time()

        subprocess.run([
            "docker","exec",container,
            "python3.13-nogil",
            "-X","gil="+gil,
            "/app/client.py",
            "/data/2021_public_lar.parquet",
            "--rows",str(rows),
            "--threads",str(t),
            "--cache",str(cache)
        ])

        end=time.time()

        results.append([mode,t,end-start])

with open("compute.csv","w",newline="") as f:
    writer=csv.writer(f)
    writer.writerow(["mode","threads","seconds"])
    writer.writerows(results)
