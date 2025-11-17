
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "8344375747:AAEjtVgpvhk8gzLFWIkpyRR1VsgBXDQ18e0"
CHAT_ID = "8089370993"

def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Pocket Option Signal Bot Running!"

@app.route('/signal', methods=['POST'])
def signal():
    data = request.json

    pattern = data.get("pattern")

    if pattern == "Hammer":
        send_signal("📈 BUY SIGNAL — Hammer pattern detected!")

    elif pattern == "Pin Bar":
        send_signal("📉 SELL SIGNAL — Pin Bar detected!")

    return {"status": "sent"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
