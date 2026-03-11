import subprocess
import csv
import time

container="p3-client-1"

files = {
    "zip":"/data/2021_public_lar_csv.zip",
    "parquet":"/data/2021_public_lar.parquet"
}

results=[]

for name,file in files.items():
    start=time.time()

    subprocess.run([
        "docker","exec",container,
        "python3.13-nogil",
        "/app/client.py",
        file,
        "--rows","0"
    ])

    end=time.time()
    results.append([name,end-start])

with open("storage.csv","w",newline="") as f:
    writer=csv.writer(f)
    writer.writerow(["format","seconds"])
    writer.writerows(results)
