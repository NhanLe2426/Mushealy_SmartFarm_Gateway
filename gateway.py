from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error as MySQLError
import config
from datetime import datetime
import requests

# Initialize the Flask application
app = Flask(__name__)

def get_db_connection():
    # Establish and return a connection to the MySQL database
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return conn
    except MySQLError as e:
        print(f"[DB] Connection error: {e}")
        return None

def save_sensor_data(device_id, value):
    # Insert telemetry data into the database
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Modify the table name 'sensor_data' to match your actual schema
            sql = "INSERT INTO sensor_data (device_id, value, created_at) VALUES (%s, %s, %s)"
            val = (device_id, value, datetime.now())
            cursor.execute(sql, val)
            conn.commit()
            print(f"[DB] Successfully inserted: Device {device_id} -> {value}")
            cursor.close()
        except MySQLError as e:
            print(f"[DB] Insert error: {e}")
        finally:
            conn.close()

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    # Parse the incoming JSON payload from CoreIoT Webhook
    data = request.json
    print(f"[Gateway] Received payload: {data}")

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Process and map the payload keys to the database structure
    for key in ["temperature", "humidity", "soil", "light", "pump_status", "light_status"]:
        if key in data:
            val = data[key]

            # Convert boolean values (True/False) to integers (1/0) for MySQL TINYINT compatibility
            if isinstance(val, bool):
                val = 1 if val else 0
            
            save_sensor_data(config.FEED_TO_DEVICE[key], val)

    # Return a success response to CoreIoT
    return jsonify({"status": "success", "message": "Telemetry processed"}), 200

# ---------------------------------------------------------
# Control Endpoint for Custom Web/App
# ---------------------------------------------------------
@app.route('/api/control', methods=['POST'])
def control_device_from_web():
    req_data = request.json
    if not req_data or "device" not in req_data or "status" not in req_data:
        return jsonify({"error": "Invalid request format"}), 400

    target_device = req_data["device"]
    target_status = req_data["status"] 

    rpc_method = "setPumpStatus" if target_device == "pump" else "setLightStatus"

    try:
        # Send a Telemetry packet containing an RPC activation command to Rule Engine.
        url = f"{config.COREIOT_URL}/api/v1/{config.COREIOT_TOKEN}/telemetry"
        payload = {
            "_trigger_rpc": True,       # Flags for Rule Engine to recognize
            "method": rpc_method,       # RPC function name
            "params": target_status     # True/False state
        }
        
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            print(f"[Gateway] Sent RPC trigger to Rule Engine: {rpc_method} -> {target_status}")
            return jsonify({"status": "success", "message": "Command forwarded via Rule Engine"}), 200
        else:
            print(f"[Gateway] Failed to trigger RPC: {res.text}")
            return jsonify({"error": "Failed to trigger RPC"}), 500

    except Exception as e:
        print(f"[Gateway] Error communicating with CoreIoT: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("  Smart Farm Gateway API Started")
    print("=" * 50)
    # Run the server on all available IP addresses
    app.run(host='0.0.0.0', port=5000)