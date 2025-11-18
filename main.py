import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "8344375747:AAGmzyhg1r8Q0BRjtzojjs2298nWwTgzBcA"
CHAT_ID = "8089370993"

def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Pocket Option Signal Bot Running!"

@app.route('/signal', methods=['GET', 'POST'])
def signal():
    # GET request (from browser)
    signal_type = request.args.get("type")

    # POST request (from bot or MT5)
    if request.method == "POST":
        data = request.json
        signal_type = data.get("type")

    if signal_type == "buy":
        send_signal("📈 BUY SIGNAL — Candle Pattern Confirmed!")
    elif signal_type == "sell":
        send_signal("📉 SELL SIGNAL — Candle Pattern Confirmed!")
    else:
        return {"status": "error", "message": "No signal type provided"}

    return {"status": "sent"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
