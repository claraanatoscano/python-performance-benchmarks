import csv
import matplotlib.pyplot as plt

x=[]
y=[]

with open("memory.csv") as f:
    reader=csv.DictReader(f)
    for row in reader:
        x.append(int(row["cache"]))
        y.append(int(row["hit_rate"]))

plt.plot(x,y,marker="o")
plt.xlabel("Cache Size")
plt.ylabel("Hit Rate (%)")
plt.title("Memory Performance")
plt.savefig("memory.svg")
