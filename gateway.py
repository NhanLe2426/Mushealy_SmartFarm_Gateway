from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error as MySQLError
import config
from datetime import datetime

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

if __name__ == '__main__':
    print("=" * 50)
    print("  Smart Farm Gateway API Started")
    print("=" * 50)
    # Run the server on all available IP addresses
    app.run(host='0.0.0.0', port=5000)