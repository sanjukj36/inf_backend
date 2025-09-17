from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)


# ---------------------- LOAD ENV ----------------------
load_dotenv()


IP = os.getenv("IP")
JSON_FILE_PATH = os.getenv("MqttFilePath", r"C:\Mqtt\__data\mqtt_live_data.json")
# ------------------------------------------------------


# Path to your JSON file
JSON_FILE_PATH = JSON_FILE_PATH

@app.route('/api/app/mqtt/data/', methods=['GET'])
def mqtt_data_dummy():
    block = request.args.get("block", "")

    if not os.path.exists(JSON_FILE_PATH):
        return jsonify({
            "data": [],
            "success": False,
            "message": f"JSON file not found at {JSON_FILE_PATH}"
        }), 500

    try:
        # Load JSON file
        with open(JSON_FILE_PATH, "r") as file:
            json_data = json.load(file)

        # Convert JSON into the required format
        records = []
        for key, value in json_data.get("data", {}).items():
            records.append({
                # "register_no": key.upper(),  # optional, can adjust
                "title": key,
                # "data_type": type(value).__name__,  # e.g., int, float
                "value": value,
                # "unit": ""  # unit is not in file, so empty
            })

        if block == "miscellaneous":
            dummy_data = {
                "data": records,
                "success": True
            }
        else:
            dummy_data = {
                "data": [],
                "success": False,
                "message": f"No dummy data available for block '{block}'",
                "messageX": f"No dummy data available for block '{JSON_FILE_PATH}'"
            }

        return jsonify(dummy_data), 200

    except Exception as e:
        return jsonify({
            "data": [],
            "success": False,
            "message": f"Error reading JSON file: {str(e)}"
        }), 500


if __name__ == '__main__':
    # app.run(host='172.168.0.81', port=5005, debug=True)
    app.run(host=IP if IP else "172.168.0.81", port=5005, debug=True)
