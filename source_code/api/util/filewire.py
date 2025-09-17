import os
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv  




# ---------------------- LOAD ENV ----------------------
load_dotenv()

# Output directory
output_dir = os.getenv("PAYLOAD_DIR", r"./payload")
# ------------------------------------------------------

# Make sure directory exists
os.makedirs(output_dir, exist_ok=True)

while True:
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Build filename (without counter)
    filename = f"NDCTELE_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Data to write
    data = {
        "timestamp": timestamp,
        "port": 562,
    }

    # Write JSON to file
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Generated: {filepath}")

    time.sleep(60)  # wait 1 minute
