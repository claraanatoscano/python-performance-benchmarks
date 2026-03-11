import csv
import matplotlib.pyplot as plt

gil_on_x=[]
gil_on_y=[]

gil_off_x=[]
gil_off_y=[]

with open("compute.csv") as f:
    reader=csv.DictReader(f)

    for r in reader:
        if r["mode"]=="gil_on":
            gil_on_x.append(int(r["threads"]))
            gil_on_y.append(float(r["seconds"]))
        else:
            gil_off_x.append(int(r["threads"]))
            gil_off_y.append(float(r["seconds"]))

plt.plot(gil_on_x,gil_on_y,marker="o",label="GIL enabled")
plt.plot(gil_off_x,gil_off_y,marker="o",label="GIL disabled")

plt.xlabel("Threads")
plt.ylabel("Seconds")
plt.legend()
plt.title("Compute Performance")

plt.savefig("compute.svg")
