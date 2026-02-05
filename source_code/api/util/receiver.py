from flask import Flask, request, jsonify
import os
import json
from datetime import datetime, timezone
import threading

app = Flask(__name__)

# ================= CONFIG =================
BASE_PATH = r"C:\Mqtt\__data"
PAYLOAD_FOLDER = os.path.join(BASE_PATH, "payload")
LIVE_FILE_NAME = "mqtt_live_data.json"
PREFIX = "NDCTELE_"

os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(PAYLOAD_FOLDER, exist_ok=True)

lock = threading.Lock()  # thread-safe file writes
# ==========================================


def current_minute_ts():
    """YYYYMMDDHHMM"""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")


def write_live_file(output: str):
    live_path = os.path.join(BASE_PATH, LIVE_FILE_NAME)
    with open(live_path, "w", encoding="utf-8") as f:
        f.write(output + "\n")


def append_payload_file(minute_ts: str, output: str):
    file_name = f"{PREFIX}{minute_ts}.json"
    path = os.path.join(PAYLOAD_FOLDER, file_name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(output + "\n")


@app.route("/mqtt", methods=["POST"])
def receive_mqtt():
    try:
        payload = request.get_json(force=True)

        payload["last_updated"] = datetime.now(timezone.utc).isoformat()
        wrapped = {"data": payload}
        output = json.dumps(wrapped)

        minute_ts = current_minute_ts()

        with lock:
            # ✅ update live file
            write_live_file(output)

            # ✅ append into minute-based payload file
            append_payload_file(minute_ts, output)

        print("📥 Received:", output)
        return jsonify({"status": "saved"}), 200

    except Exception as e:
        print("⚠️ Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
