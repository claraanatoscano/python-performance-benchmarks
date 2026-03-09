import sys
import time
import requests
import threading
from collections import deque

cache = {}
order = deque()
cache_size = 0
lock = threading.Lock()


def init_cache(size):
    global cache, order, cache_size
    cache = {}
    order = deque()
    cache_size = size


def http_get(url, http_session):

    # first cache check
    with lock:
        if url in cache:
            return cache[url], True

    # HTTP request without lock
    wait = 0.1
    total_wait = 0
    while True:
        try:
            resp = http_session.get(url)
            break
        except requests.exceptions.ConnectionError:
            total_wait += wait
            if total_wait > 5:
                raise
            print(f"RETRY {url} after {wait}s (total waited: {total_wait}s)")
            time.sleep(wait)

    if resp.status_code == 404:
        content = None
    else:
        resp.raise_for_status()
        content = resp.content

    # insert into cache
    with lock:

        # check again in case another thread inserted it
        if url in cache:
            return cache[url], True

        if len(order) >= cache_size:
            oldest = order.popleft()
            del cache[oldest]

        cache[url] = content
        order.append(url)

    return content, False


if __name__ == "__main__":
    init_cache(3)
    session = requests.Session()

    hits = 0
    for url in sys.argv[1:]:
        _, hit = http_get(url, session)
        if hit:
            hits += 1

    print(f"hits: {hits}")
