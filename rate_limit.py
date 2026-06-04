import time

last_requests = {}

def allow_request(user_id, seconds=2):

    now = time.time()

    if user_id in last_requests:

        if now - last_requests[user_id] < seconds:
            return False

    last_requests[user_id] = now

    return True