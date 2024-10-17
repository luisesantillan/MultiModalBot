from collections import deque
import json
import os

class MemoryManager:
    def __init__(self, clear=False):
        if clear: 
            self.clear()
            return
        if not os.path.exists("history.jsonl"): open("history.jsonl", "w", encoding="utf-8").close()
        self.memory = deque(
            [json.loads(line.strip()) for line in open("history.jsonl", "r", encoding="utf-8").readlines()[-10:]],            
            maxlen=10
        )
        print(f"Loaded memory: {self.memory}")

    def add_message(self, message):
        self.memory.append(message)
        with open("history.jsonl", "a", encoding="utf-8") as f:
            json.dump(message, f, ensure_ascii=False)
            f.write("\n")

    def clear(self):
        self.memory = deque(maxlen=10)
        open("history.jsonl", "w", encoding="utf-8").close()
        print("Memory cleared.")