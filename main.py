# main.py
import os, time, threading
from datetime import datetime, timezone
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN","").strip()
CHAT_ID   = os.getenv("CHAT_ID","").strip()
SYMBOL    = os.getenv("SYMBOL","BTCUSDT").strip()
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL","30"))

def send_signal(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing BOT_TOKEN or CHAT_ID; cannot send telegram.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("Telegram sent:", text)
    except Exception as e:
        print("Telegram send failed:", e)

@app.route("/")
def home():
    return "Pocket Option Signal Bot Running!"

@app.route("/signal", methods=["GET","POST"])
def signal_endpoint():
    # GET: /signal?type=buy   POST: {"type":"buy"}
    signal_type = None
    if request.method == "GET":
        signal_type = request.args.get("type")
    else:
        data = request.get_json(silent=True) or {}
        signal_type = data.get("type")
    if signal_type == "buy":
        send_signal("📈 BUY SIGNAL — Candle Pattern Confirmed!")
    elif signal_type == "sell":
        send_signal("📉 SELL SIGNAL — Candle Pattern Confirmed!")
    else:
        return jsonify({"error":"no type"}), 400
    return jsonify({"status":"sent"})

# pattern detectors
def is_hammer(o,h,l,c):
    body = abs(c-o)
    lower = min(o,c)-l
    upper = h - max(o,c)
    if body == 0: body = 1e-9
    return (lower >= 2*body) and (upper <= body)

def is_inverted_hammer(o,h,l,c):
    body = abs(c-o)
    lower = min(o,c)-l
    upper = h - max(o,c)
    if body == 0: body = 1e-9
    return (upper >= 2*body) and (lower <= body)

def is_pinbar(o,h,l,c):
    body = abs(c-o)
    lower = min(o,c)-l
    upper = h - max(o,c)
    if body == 0: body = 1e-9
    return (lower >= 2.5*body) or (upper >= 2.5*body)

# fetch last closed 5m candle from Binance
def fetch_latest_5m(symbol):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol":symbol,"interval":"5m","limit":2}
        r = requests.get(url, params=params, timeout=10); r.raise_for_status()
        data = r.json()
        closed = data[-2]  # last fully closed candle
        return {
            "open_time": int(closed[0]),
            "open": float(closed[1]),
            "high": float(closed[2]),
            "low": float(closed[3]),
            "close": float(closed[4]),
        }
    except Exception as e:
        print("fetch error:", e)
        return None

class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.last_marker = None

    def run(self):
        print("Worker started: symbol", SYMBOL, "poll", POLL_INTERVAL)
        while True:
            try:
                candle = fetch_latest_5m(SYMBOL)
                if candle:
                    marker = candle["open_time"]
                    if marker != self.last_marker:
                        self.last_marker = marker
                        o = candle["open"]; h = candle["high"]; l = candle["low"]; c = candle["close"]
                        hammer = is_hammer(o,h,l,c)
                        inv = is_inverted_hammer(o,h,l,c)
                        pin = is_pinbar(o,h,l,c)
                        lower = min(o,c)-l; upper = h-max(o,c)
                        signal = None
                        if hammer or (pin and lower>upper):
                            signal = "buy"
                        elif inv or (pin and upper>lower):
                            signal = "sell"
                        if signal:
                            ts = datetime.fromtimestamp(marker/1000, tz=timezone.utc).astimezone()
                            tstr = ts.strftime("%Y-%m-%d %H:%M:%S %Z")
                            send_signal(f"📣 {signal.upper()} SIGNAL — Pattern on {SYMBOL} M5\n{tstr}")
                        else:
                            print("No pattern on", SYMBOL, "candle at", marker)
                else:
                    print("No candle fetched.")
            except Exception as e:
                print("Worker error:", e)
            time.sleep(POLL_INTERVAL)

worker = None

@app.before_first_request
def start_worker():
    global worker
    if worker is None:
        worker = Worker()
        worker.start()

if __name__ == "__main__":
    start_worker()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")))
