import sys
import time
import requests

def init_cache(size):
    pass # TODO: initialize any global data structures as needed

def http_get(url, http_session):
    """Fetch url with retries (up to 5 seconds total wait). Returns (content_bytes, hit)."""
    wait = 0.1
    total_waited = 0
    while True:
        try:
            resp = http_session.get(url)
            break
        except requests.exceptions.ConnectionError:
            total_waited += wait
            if total_waited > 5:
                raise
            print(f"RETRY {url} after {wait}s (total waited: {total_waited}s)")
            time.sleep(wait)
    resp.raise_for_status()
    return resp.content, False

if __name__ == "__main__":
    init_cache(3)
    session = requests.Session()
    hits = 0
    for url in sys.argv[1:]:
        _, hit = http_get(url, session)
        if hit:
            hits += 1
    print(f"hits: {hits}")
