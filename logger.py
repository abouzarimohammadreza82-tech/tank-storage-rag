import json
from datetime import datetime

def save_log(user_id, query, answer):

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "query": query,
        "answer": answer
    }

    with open(
        "chat_logs.jsonl",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                record,
                ensure_ascii=False
            ) + "\n"
        )