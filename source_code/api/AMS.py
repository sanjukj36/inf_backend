from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
import os
from dotenv import load_dotenv
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "mydatabase.db"

# ---------------------- LOAD ENV ----------------------
load_dotenv()

IP = os.getenv("IP")

# ---------------------- PATH CONFIG ----------------------

FILE_PATH = os.getenv(
    "MqttFilePath",
    r"C:\Mqtt\__data\mqtt_live_data.json"
)

PAYLOAD_PATH = os.getenv(
    "PayloadPath",
    r"C:\Mqtt\__data\payload"
)

# ------------------------------------------------------


# ---------------------- INIT DB ----------------------
def init_db():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ams_config (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT UNIQUE,
            ui_config_data TEXT
        )
    """)

    conn.commit()
    conn.close()

# ---------------------- ADD / UPDATE TAG ----------------------
@app.route('/app/add/tag/', methods=['POST'])
def add_or_update_tag():

    init_db()

    data = request.json

    label = data.get("label")
    ui_config_data = data.get("data")

    if not label or ui_config_data is None:

        return jsonify({
            "success": False,
            "message": "label and data are required"
        }), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    json_data = json.dumps(ui_config_data)

    # Check label exists
    cursor.execute("""
        SELECT ID FROM ams_config
        WHERE label = ?
    """, (label,))

    existing = cursor.fetchone()

    if existing:

        # Update
        cursor.execute("""
            UPDATE ams_config
            SET ui_config_data = ?
            WHERE label = ?
        """, (json_data, label))

        message = "Updated successfully"

    else:

        # Insert
        cursor.execute("""
            INSERT INTO ams_config (label, ui_config_data)
            VALUES (?, ?)
        """, (label, json_data))

        message = "Created successfully"

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": message
    }), 200


# ---------------------- GET MQTT CONFIG ----------------------
@app.route('/app/get/mqtt/', methods=['GET'])
def get_mqtt_config():

    SKIP_MQTT_LABELS = ["__sidebar_config__", "__ui_theme__"]

    init_db()

    label = request.args.get("label")

    if not label:

        return jsonify({
            "success": False,
            "message": "label is required"
        }), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT label, ui_config_data
        FROM ams_config
        WHERE label = ?
    """, (label,))

    row = cursor.fetchone()

    conn.close()

    if not row:

        return jsonify({
            "success": False,
            "message": "No data found"
        }), 404

    # -----------------------------------------
    # Load DB JSON
    # -----------------------------------------
    data = json.loads(row[1])

    # -----------------------------------------
    # Load MQTT Live Data JSON
    # -----------------------------------------
    mqtt_data = {}

    try:

        if os.path.exists(FILE_PATH):

            with open(FILE_PATH, "r") as file:

                mqtt_json = json.load(file)

            mqtt_data = mqtt_json.get("data", {})

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Error reading mqtt_live_data.json: {str(e)}"
        }), 500

    # -----------------------------------------
    # Update Values From MQTT JSON
    # -----------------------------------------

    if label not in SKIP_MQTT_LABELS:

        # If data is list
        if isinstance(data, list):

            for item in data:

                tag = item.get("tag")

                if tag in mqtt_data:
                    item["value"] = mqtt_data[tag]
                else:
                    item["value"] = 0

        # If data is object
        elif isinstance(data, dict):

            tag = data.get("tag")

            if tag in mqtt_data:
                data["value"] = mqtt_data[tag]
            else:
                data["value"] = 0

            # -----------------------------------------
        
    # Get Last Updated Time
    # -----------------------------------------
    timestamp = mqtt_data.get("time")

    if timestamp:
        try:
            human_readable_time = datetime.fromtimestamp(
                int(timestamp)
            ).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            human_readable_time = None
    else:
        human_readable_time = None

    return jsonify({
        "success": True,
        "label": row[0],
        "data": data,
        "last_updated": {
            "timestamp": timestamp,
            "last_updated_time": human_readable_time
        }
    }), 200


# ---------------------- GET TAGS FROM JSON ----------------------
@app.route('/app/get/tag/', methods=['GET'])
def get_tags():

    try:

        # Check file exists
        if not os.path.exists(FILE_PATH):

            return jsonify({
                "success": False,
                "message": "mqtt_live_data.json file not found"
            }), 404

        # Read JSON file
        with open(FILE_PATH, "r") as file:

            json_data = json.load(file)

        # Get "data" object
        data = json_data.get("data", {})

        # Extract only tags (keys)
        tags = list(data.keys())

        return jsonify({
            "success": True,
            "data": tags
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------------- GET CHART DATA ----------------------
@app.route('/app/get/chart/', methods=['GET'])
def get_chart_data():

    tag = request.args.get("tag")
    start_datetime = request.args.get("start_datetime")
    end_datetime = request.args.get("end_datetime")

    if not tag or not start_datetime or not end_datetime:

        return jsonify({
            "success": False,
            "message": "tag, start_datetime and end_datetime are required"
        }), 400

    try:

        # Convert request datetime
        start_dt = datetime.strptime(
            start_datetime,
            "%Y-%m-%d %H:%M:%S"
        )

        end_dt = datetime.strptime(
            end_datetime,
            "%Y-%m-%d %H:%M:%S"
        )

        response_data = []

        # Check payload folder exists
        if not os.path.exists(PAYLOAD_PATH):

            return jsonify({
                "success": False,
                "message": "Payload folder not found"
            }), 404

        # Get all files
        files = sorted(os.listdir(PAYLOAD_PATH))

        for file_name in files:

            # Check filename format
            if not file_name.startswith("NDCTELE_"):
                continue

            if not file_name.endswith(".json"):
                continue

            try:

                # Example:
                # NDCTELE_202605190327.json

                timestamp_str = file_name.replace(
                    "NDCTELE_",
                    ""
                ).replace(
                    ".json",
                    ""
                )

                file_dt = datetime.strptime(
                    timestamp_str,
                    "%Y%m%d%H%M"
                )

                # Check datetime range
                if file_dt < start_dt or file_dt > end_dt:
                    continue

                file_path = os.path.join(
                    PAYLOAD_PATH,
                    file_name
                )

                # Read file
                with open(file_path, "r") as file:

                    json_data = json.load(file)

                data = json_data.get("data", {})

                # Get tag value
                value = data.get(tag)

                if value is not None:

                    response_data.append({
                        "time": file_dt.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "value": value
                    })

            except Exception as e:

                print(f"Error processing file {file_name}: {e}")

        return jsonify({
            "success": True,
            "tag": tag,
            "data": response_data
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------------- GET ALL TAGS ----------------------
@app.route('/app/get/all/tags/', methods=['GET'])
def get_all_tags():

    try:

        all_tags = set()

        # Check payload folder exists
        if not os.path.exists(PAYLOAD_PATH):

            return jsonify({
                "success": False,
                "message": "Payload folder not found"
            }), 404

        files = os.listdir(PAYLOAD_PATH)

        for file_name in files:

            if not file_name.startswith("NDCTELE_"):
                continue

            if not file_name.endswith(".json"):
                continue

            file_path = os.path.join(
                PAYLOAD_PATH,
                file_name
            )

            try:

                with open(file_path, "r") as file:

                    json_data = json.load(file)

                data = json_data.get("data", {})

                # Add keys/tags
                all_tags.update(data.keys())

            except Exception as e:

                print(f"Error reading {file_name}: {e}")

        return jsonify({
            "success": True,
            "count": len(all_tags),
            "data": sorted(list(all_tags))
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------------- LOGIN ----------------------
# @app.route('/app/login/', methods=['POST'])
# def login():

#     data = request.json

#     username = data.get("username")
#     password = data.get("password")

#     users = {
#         "Admin": {
#             "password": "Admin123",
#             "userType": "admin"
#         },
#         "Rawabi": {
#             "password": "Rawabi123",
#             "userType": "client"
#         }
#     }

#     user = users.get(username)

#     if not user or user["password"] != password:
#         return jsonify({
#             "success": False,
#             "message": "Invalid username or password"
#         }), 401

#     return jsonify({
#         "success": True,
#         "message": "Login successful",
#         "data": {
#             "username": username,
#             "userType": user["userType"]
#         }
#     }), 200

# ---------------------- LOGIN ----------------------
@app.route('/app/login5/', methods=['POST'])
def login5():

    data = request.json or {}

    username = data.get("username")
    password = data.get("password")

    users = {
        "Admin": {
            "password": "Admin123",
            "userType": "admin"
        },
        "Rawabi": {
            "password": "Rawabi123",
            "userType": "client"
        }
    }

    user = users.get(username)

    # Invalid credentials
    if not user or user["password"] != password:
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    response_data = {
        "username": username,
        "userType": user["userType"]
    }

    # Client Login
    if user["userType"] == "client":

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ui_config_data
            FROM ams_config
            WHERE label = ?
        """, ("__sidebar_config__",))

        row = cursor.fetchone()

        conn.close()

        # Sidebar config not created yet
        if not row:
            return jsonify({
                "success": False,
                "message": "Admin side configuration is pending. Please contact administrator."
            }), 401

        response_data["sidebarConfig"] = json.loads(row[0])

    # Success
    return jsonify({
        "success": True,
        "message": "Login successful",
        "data": response_data
    }), 200

# ---------------------- LOGIN ----------------------
@app.route('/app/login/', methods=['POST'])
def login():

    data = request.json or {}

    username = data.get("username")
    password = data.get("password")

    users = {
        "Admin": {
            "password": "Admin123",
            "userType": "admin"
        },
        "Rawabi": {
            "password": "Rawabi123",
            "userType": "client"
        }
    }

    user = users.get(username)

    # Invalid credentials
    if not user or user["password"] != password:
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 401

    response_data = {
        "username": username,
        "userType": user["userType"]
    }

    # Client Login Validation
    if user["userType"] == "client":

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ui_config_data
            FROM ams_config
            WHERE label = ?
        """, ("__sidebar_config__",))

        row = cursor.fetchone()

        conn.close()

        # Sidebar config not created
        if not row:
            return jsonify({
                "success": False,
                "message": "Admin side configuration is pending. Please contact administrator."
            }), 401

        try:
            sidebar_config = json.loads(row[0])
        except Exception:
            sidebar_config = []

        description = ""

        if (
            isinstance(sidebar_config, list)
            and len(sidebar_config) > 0
            and isinstance(sidebar_config[0], dict)
        ):
            description = str(
                sidebar_config[0].get("description", "")
            ).strip()

        # Sidebar config is empty / pending
        if not description or description == "[]":
            return jsonify({
                "success": False,
                "message": "Admin side configuration is pending. Please contact administrator."
            }), 401

        response_data["sidebarConfig"] = sidebar_config

    return jsonify({
        "success": True,
        "message": "Login successful",
        "data": response_data
    }), 200

# ---------------------- MAIN ----------------------
if __name__ == '__main__':

    app.run(
        host=IP if IP else "172.168.0.81",
        port=5008,
        debug=True
    )