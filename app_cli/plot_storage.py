import csv
import matplotlib.pyplot as plt

formats=[]
times=[]

with open("storage.csv") as f:
    reader=csv.DictReader(f)
    for row in reader:
        formats.append(row["format"])
        times.append(float(row["seconds"]))

plt.bar(formats,times)
plt.ylabel("Seconds")
plt.title("Storage Performance")
plt.savefig("storage.svg")
