import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv  

# ---------------------- LOAD ENV ----------------------
load_dotenv()

# Source MQTT JSON file
JSON_FILE_PATH = os.getenv(
    "MqttFilePath",
    r"C:\Mqtt\__data\mqtt_live_data.json"
)

# Output directory
output_dir = os.getenv("PAYLOAD_DIR", r"./payload")
# ------------------------------------------------------

# Make sure output directory exists
os.makedirs(output_dir, exist_ok=True)

while True:
    try:
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Build filename
        filename = f"NDCTELE_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Read data from mqtt_live_data.json
        with open(JSON_FILE_PATH, "r") as source_file:
            mqtt_data = json.load(source_file)

        # (Optional) add timestamp into payload
        mqtt_data["generated_at"] = timestamp

        # Write copied data into new file
        with open(filepath, "w") as target_file:
            json.dump(mqtt_data, target_file, indent=4)

        print(f"Generated: {filepath}")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(60)  # wait 1 minute
