import time
from collections import defaultdict
import threading

_lock = threading.Lock()

_last_request = defaultdict(float)

RATE_LIMIT_SECONDS = 2


def allow_request(user_id: int) -> bool:
    now = time.time()

    with _lock:
        last = _last_request[user_id]

        if now - last < RATE_LIMIT_SECONDS:
            return False

        _last_request[user_id] = now
        return True