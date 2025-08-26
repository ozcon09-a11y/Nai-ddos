import argparse
import threading
import time
import queue
import random
import signal
import sys
import statistics
from datetime import datetime
from typing import List, Dict

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from colorama import Fore, Style, init as colorama_init
except ImportError:
    print("Missing deps. Install: pip install requests colorama")
    sys.exit(1)

# --------- UI / Banner ---------
colorama_init(autoreset=True)

BANNER = r"""
================================================================
=  =======  ====  ====    =====       ==       =========      ==
=   ======  ===    ====  ======  ====  =  ====  =======  ====  =
=    =====  ==  ==  ===  ======  ====  =  ====  =======  ====  =
=  ==  ===  =  ====  ==  ======  ====  =  ====  ==   ===  ======
=  ===  ==  =  ====  ==  ======  ====  =  ====  =     ====  ====
=  ====  =  =        ==  ======  ====  =  ====  =  =  ======  ==
=  =====    =  ====  ==  ======  ====  =  ====  =  =  =  ====  =
=  ======   =  ====  ==  ======  ====  =  ====  =  =  =  ====  =
=  =======  =  ====  =    =====       ==       ===   ===      ==
================================================================
"""

CYBER_LINES = [
    "Booting NAI engine...",
    "Spinning up threads...",
    "Priming HTTP sessions...",
    "Arming observability...",
    "Ready to launch 🚀"
]

SPINNER_FRAMES = ["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]

shutdown_flag = threading.Event()

def print_banner():
    print(Fore.MAGENTA + Style.BRIGHT + BANNER)
    # cyberpunk boot animation
    for i, line in enumerate(CYBER_LINES):
        for _ in range(8):
            frame = SPINNER_FRAMES[_ % len(SPINNER_FRAMES)]
            sys.stdout.write(f"\r{Fore.CYAN}{frame} {line}")
            sys.stdout.flush()
            time.sleep(0.05)
        print(f"\r{Fore.GREEN}✔ {line}{' ' * 20}")
    print("")

# --------- Worker Logic ---------
class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.latencies: List[float] = []
        self.success = 0
        self.fail = 0
        self.codes: Dict[int, int] = {}

    def record(self, ok: bool, latency: float, code: int = None):
        with self.lock:
            if ok:
                self.success += 1
                self.latencies.append(latency)
            else:
                self.fail += 1
            if code is not None:
                self.codes[code] = self.codes.get(code, 0) + 1

def build_session(timeout, keepalive=True, verify_tls=True):
    s = requests.Session()
    # robust adapter with connection pool
    retries = Retry(total=0, backoff_factor=0)
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=100,
        pool_maxsize=1000
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": "NAI-LoadTester/1.0",
        "Connection": "keep-alive" if keepalive else "close"
    })
    s.verify = verify_tls
    s.timeout = timeout
    return s

def worker(idx, args, job_q: queue.Queue, metrics: Metrics, start_ts, end_>
    session = build_session(timeout=args.timeout, keepalive=not args.no_ke>
    rng = random.Random(idx ^ int(time.time()))
    # simple log pulse each second
    last_log = time.time()

    while not shutdown_flag.is_set():
        now = time.time()
        if now < start_ts:
            time.sleep(min(0.01, start_ts - now))
            continue
        if now >= end_ts:
            break

        # rate limiting per thread
        if args.rps > 0:
            # spread requests evenly within second
            delay = 1.0 / args.rps
        else:
            delay = 0.0

        try:
            method, url, payload, headers = job_q.get_nowait()
        except queue.Empty:
            # recycle a default job if queue empty
            method = args.method
            url = args.url
            payload = None
            headers = {}

        t0 = time.perf_counter()
        ok = False
        code = None
        try:
            if method == "GET":
                resp = session.get(url, headers=headers)
            elif method == "POST":
                resp = session.post(url, data=payload if args.form else No>
                                    json=None if args.form else payload, h>
            elif method == "PUT":
                resp = session.put(url, data=payload if args.form else Non>
                                   json=None if args.form else payload, he>
            else:
                resp = session.request(method, url, headers=headers)
            code = resp.status_code
            ok = 200 <= resp.status_code < 500  # 5xx considered fail for >
        except requests.RequestException:
            ok = False
        latency = (time.perf_counter() - t0) * 1000.0
        metrics.record(ok, latency, code)

        # eye-candy pulse
        if time.time() - last_log >= 1.0 and idx == 0:
            total = metrics.success + metrics.fail
            sys.stdout.write(
                f"\r{Fore.YELLOW}🚀 Threads {args.threads} | Sent {total} >
                f"{sum(v for k,v in metrics.codes.items() if 200<=k<300)}/"
                f"{sum(v for k,v in metrics.codes.items() if 300<=k<400)}/"
                f"{sum(v for k,v in metrics.codes.items() if 400<=k<500)}/"
                f"{sum(v for k,v in metrics.codes.items() if 500<=k<600)}"
            )
            sys.stdout.flush()
            last_log = time.time()

        if delay > 0:
            # add tiny jitter so all threads don't align perfectly
            time.sleep(delay * (0.8 + 0.4 * rng.random()))

# --------- Percentiles / Report ---------
def percentile(values: List[float], p: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    k = (len(v) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(v) - 1)
    if f == c:
        return v[int(k)]
    return v[f] + (v[c] - v[f]) * (k - f)
