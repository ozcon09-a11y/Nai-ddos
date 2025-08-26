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
