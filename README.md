# Python Performance Benchmarks

A multi-threaded Python application that loads 26M+ loan records, plus a set of benchmarks measuring how file format, caching, and parallelism affect its speed.

Built for CS 544: Introduction to Big Data Systems at UW–Madison (Spring 2026).

## What it does

- **Loads data in multiple formats:** reads the same dataset from CSV and Parquet with PyArrow.
- **Caches results:** keeps recently used data in memory to avoid repeated network I/O.
- **Runs in parallel:** uses multiple threads to process requests concurrently.

## Benchmarks

Each experiment isolates one variable and measures its effect:

1. **File format:** load time for CSV vs. Parquet.
2. **Cache size:** cache hit rate as the cache grows.
3. **Parallelism:** throughput across different thread counts, and how Python's Global Interpreter Lock (GIL) limits multithreaded speedups.

## Key takeaways

- Columnar formats like Parquet load much faster than CSV for analytical workloads.
- Even a small cache can avoid a large share of repeated I/O.
- More threads help only up to a point, because Python's GIL limits CPU-bound work.

## Tech stack

Python · PyArrow · Parquet · CSV · multithreading · Jupyter

## Running it

Install the dependencies and open the notebook to run the benchmarks:

```bash
pip install -r requirements.txt
jupyter notebook
```
