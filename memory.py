from collections import defaultdict

memory_store = defaultdict(list)

def get_history(chat_id):
    return memory_store[chat_id]

def add_message(chat_id, role, content):

    memory_store[chat_id].append({
        "role": role,
        "content": content
    })

    memory_store[chat_id] = memory_store[chat_id][-8:]