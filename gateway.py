from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import Error as PostgresError
import config
from datetime import datetime
import requests

# Initialize the Flask application
app = Flask(__name__)

# ---------------------------------------------------------
# Database Helper Functions
# ---------------------------------------------------------
def get_db_connection():
    # Establish and return a connection to the Neon PostgreSQL database
    try:
        conn = psycopg2.connect(config.POSTGRES_URL)
        return conn
    except PostgresError as e:
        print(f"[DB] Connection error: {e}")
        return None

def save_sensor_data(device_id, value):
    # Insert telemetry data into the real PostgreSQL database schema
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Updated columns to match your real schema: sensor_data_id, recorded_at, synced
            sql = "INSERT INTO sensor_data (device_id, value, recorded_at, synced) VALUES (%s, %s, %s, %s)"
            val = (device_id, value, datetime.now(), True)
            cursor.execute(sql, val)
            conn.commit()
            print(f"[DB] Successfully inserted into real schema: Device {device_id} -> {value}")
            cursor.close()
        except PostgresError as e:
            print(f"[DB] Insert error: {e}")
        finally:
            conn.close()

# ---------------------------------------------------------
# Data Ingestion Endpoint
# ---------------------------------------------------------
@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.json
    print(f"[Gateway] Received payload: {data}")

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    for key in ["temperature", "humidity", "soil", "light", "pump_status", "light_status"]:
        if key in data:
            val = data[key]
            
            # Convert boolean values to integers for database compatibility
            if isinstance(val, bool):
                val = 1 if val else 0
                
            save_sensor_data(config.FEED_TO_DEVICE[key], val)

    return jsonify({"status": "success", "message": "Telemetry processed"}), 200

# ---------------------------------------------------------
# Control Endpoint (No JWT Required, Self-Triggered RPC)
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
        url = f"{config.COREIOT_URL}/api/v1/{config.COREIOT_TOKEN}/telemetry"
        payload = {
            "_trigger_rpc": True,       
            "method": rpc_method,       
            "params": target_status     
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
    print("  Smart Farm Gateway API (PostgreSQL Edition)")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000)