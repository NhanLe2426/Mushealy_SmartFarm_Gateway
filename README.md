# Mushealy SmartFarm Gateway

A lightweight, stateless Python Flask API Gateway designed as an intermediate data pipeline between **CoreIoT (ThingsBoard)** and a **Railway MySQL Database** for an advanced AIoT Smart Farm ecosystem. 

This gateway handles real-time sensor data ingestion and facilitates secure, asynchronous two-way Remote Procedure Call (RPC) device control, preventing connection conflicts (MQTT flapping) on edge devices.

---

## Architecture Overview

The system architecture decouples the edge hardware connection from the main database storage layer using a combination of MQTT and stateless HTTP protocols:

* **Telemetry Logging Flow**:
    `ESP32 (Yolo:Bit) Sensors` --[MQTT Telemetry]--> `CoreIoT Broker` --[Rule Engine REST Webhook]--> `Gateway API (/api/telemetry)` --[MySQL Connector]--> `Railway Database`
* **Two-Way Control Flow (RPC Sync)**:
    `Frontend UI` --[HTTP POST]--> `Gateway API (/api/control)` --[Stateless HTTP POST with Trigger Flag]--> `CoreIoT Rule Engine` --[Filter & RPC Request]--> `ESP32 Actuators (Pump/Light)` --[MQTT Sync State]--> `CoreIoT Attributes`

This stateless design ensures the ESP32 maintains a persistent, uninterrupted MQTT connection while the web application can query the MySQL database or issue real-time commands smoothly.

---

## Directory Structure

```
smartfarm-gateway/
│
├── gateway.py          # Main Flask application handling incoming endpoints
├── config.py           # Configuration loader managing database and device mapping
├── requirements.txt    # Production and local dependency packages
├── Procfile            # Process file defining WSGI server runtime for Railway
├── .gitignore          # Explicitly ignores virtual envs, caches, and secrets
└── .env                # Local environment variables containing sensitive keys (git-ignored)
```

---

## Installation and Local Setup

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/NhanLe2426/Mushealy_SmartFarm_Gateway.git
cd Mushealy_SmartFarm_Gateway
```

#### 2. Initialize Virtual Environment

```bash
# Create the environment
python -m venv venv

# Activate the environment (Windows Command Prompt/PowerShell)
venv\\Scripts\\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the root directory and specify your Railway database credentials:

```env
DB_HOST=your_railway_mysql_host_address
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_database_password
DB_NAME=railway
```

#### 5. Run the Local Server

```bash
python gateway_api.py
```

The server will spin up and listen on http://127.0.0.1:5000

---

## Production Deployment (Railway)

This repository is optimized for one-click deployment on Railway.

Create a new service inside your existing Railway project by selecting GitHub Repo and choosing `Mushealy_SmartFarm_Gateway`.

Navigate to the Variables tab of the newly created Gateway service and mirror the exact pairs from your `.env` file (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

Go to Settings -> Public Networking and click Generate Domain to expose a secure public URL (e.g., https://smartfarm-gateway-production.up.railway.app).

Railway automatically reads the Procfile and launches the application using Gunicorn, a production-grade WSGI HTTP server:

```
web: gunicorn gateway_api:app
```

---

## API Reference

### Data Ingestion Endpoint

Laves incoming sensor telemetry and actuator states dispatched from CoreIoT's Rule Engine.

- **URL**: `/api/telemetry`

- **Method**: `POST`

- **Headers**: `Content-Type: application/json`

- **Payload Example**:

```json
{
  "temperature": 32.3,
  "humidity": 64.5,
  "soil": 100,
  "light": 2150,
  "pump_status": true,
  "light_status": false
}
```

- **Response**: `200 OK` on successful database insertion.

### Device Control Endpoint

Forwards manual override toggles triggered from the custom frontend UI to CoreIoT without interfering with the active MQTT channel.

- **URL**: `/api/control`

- **Method**: `POST`

- **Headers**: `Content-Type: application/json`

- **Payload Example**:

```json
{
  "device": "pump",
  "status": true
}
```


- **Response**: `200 OK` with JSON acknowledgment confirming transmission to CoreIoT's Rule Engine.
---

## CoreIoT Rule Chain Configuration

To complete the data loop, ensure your **CoreIoT Root Rule Chain** includes the following nodes branching from the `Message Type Switch` (*Post telemetry* label):

### 1. Telemetry Sync (To Railway DB):

- Add a **REST API Call** node.

- Set *Endpoint URL* to: https://<YOUR_RAILWAY_DOMAIN>/api/telemetry

- Set *Request Method* to `POST` and add header `Content-Type: application/json`.

### 2. Self-Triggered RPC Gate (For Web Control):

- Add a **Script Filter** node to catch incoming web commands forwarded by the Gateway API.

- *JS Filter Code*: `return typeof msg._trigger_rpc !== 'undefined' && msg._trigger_rpc === true;`

- Connect the *True* relation to an **RPC Call Request** node with an appropriate timeout (e.g., 5 seconds) to forcefully forward actions down to the physical ESP32 node.
