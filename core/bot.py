import time
import queue
import threading
import requests
import os
from dotenv import load_dotenv
from core.organizer import Organizer

load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")

base_api = f"https://api.telegram.org/bot${telegram_token}"

"""class Coms:
    def start(self):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError

    def send(self, chat_id, text):
        raise NotImplementedError"""
        
class TelegramBot:
    def __init__(self, token):
        self.api = f"https://api.telegram.org/bot{token}"
        self.queue = queue.Queue()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def get(self):
        return self.queue.get()

    def send(self, chat_id, text):
        requests.post(f"{self.api}/sendMessage", json={"chat_id": chat_id, "text": text})

    def _poll(self):
        offset = 0
        while True:
            r = requests.get(f"{self.api}/getUpdates", params={"offset": offset, "timeout": 30})
            print("polling...", r.json())  # add this
            for update in r.json().get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                if msg.get("text"):
                    print("got message:", msg["text"])  # add this
                    self.queue.put(msg)
            time.sleep(0.5)

class GengiBot(TelegramBot):
    def __init__(self, token, agentType):
        super().__init__(token)
        self.agentType = agentType

    def run(self):
        self.start()
        while True:
            msg = self.get()
            text = msg["text"]
            chat_id = msg["chat"]["id"]
            print(f"[Bot] Processing: {text}")
            try:
                reply = self.agentType.chat(text)
                print(f"[Bot] Sending reply: {reply[:100]}...")
                self.send(chat_id, reply)
            except Exception as e:
                print(f"[Bot] ERROR: {e}")
                import traceback
                traceback.print_exc()
                self.send(chat_id, f"Error: {e}")
    