import os
import json
import subprocess
import threading
from datetime import datetime, timezone

# ================= CONFIG =================
BASE_PATH = r"C:\Mqtt\__data"
PAYLOAD_FOLDER = os.path.join(BASE_PATH, "payload")
LIVE_FILE_NAME = "mqtt_live_data.json"
PREFIX = "NDCTELE_"
MAX_PAYLOAD_FILES = 1400

MOSQUITTO_SUB = r"C:\Program Files\mosquitto\mosquitto_sub.exe"
MQTT_HOST = "172.168.0.80"
MQTT_PORT = "1883"
MQTT_TOPIC = "ndc/min_all"
# =========================================

os.makedirs(BASE_PATH, exist_ok=True)
os.makedirs(PAYLOAD_FOLDER, exist_ok=True)

lock = threading.Lock()


# ================= UTILITIES =================
def current_minute_ts():
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")


def write_live_file(output: str):
    path = os.path.join(BASE_PATH, LIVE_FILE_NAME)
    with open(path, "w", encoding="utf-8") as f:
        f.write(output + "\n")


def append_payload_file(minute_ts: str, output: str):
    file_name = f"{PREFIX}{minute_ts}.json"
    path = os.path.join(PAYLOAD_FOLDER, file_name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(output + "\n")


def cleanup_old_payload_files():
    files = [
        os.path.join(PAYLOAD_FOLDER, f)
        for f in os.listdir(PAYLOAD_FOLDER)
        if f.endswith(".json")
    ]

    excess = len(files) - MAX_PAYLOAD_FILES
    if excess <= 0:
        return

    files.sort(key=os.path.getctime)

    for f in files[:excess]:
        try:
            os.remove(f)
            print(f"🗑️ Deleted: {os.path.basename(f)}")
        except Exception as e:
            print(f"⚠️ Delete failed: {e}")


# ================= MQTT LISTENER =================
def mqtt_listener():
    print("🚀 MQTT Listener started...")

    cmd = [
        MOSQUITTO_SUB,
        "-h", MQTT_HOST,
        "-p", MQTT_PORT,
        "-t", MQTT_TOPIC,
        "-v"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    for line in process.stdout:
        try:
            topic, message = line.strip().split(" ", 1)
            payload = json.loads(message)

            payload["last_updated"] = datetime.now(timezone.utc).isoformat()
            wrapped = {"data": payload}
            output = json.dumps(wrapped)

            minute_ts = current_minute_ts()

            with lock:
                write_live_file(output)
                append_payload_file(minute_ts, output)
                cleanup_old_payload_files()

            print("📥 MQTT data saved")

        except json.JSONDecodeError:
            print("⚠️ Invalid JSON received")
        except Exception as e:
            print("⚠️ Error:", e)


# ================= MAIN =================
if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=mqtt_listener, daemon=True)
    mqtt_thread.start()

    print("✅ System running. Waiting for MQTT data...")
    mqtt_thread.join()
