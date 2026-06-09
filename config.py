import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ---------------------------------------------------------
# PostgreSQL Configuration (Neon DB on Vercel)
# ---------------------------------------------------------
# Using the pooled connection string for better performance
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:pass@host/db")

# ---------------------------------------------------------
# CoreIoT Device API Configuration
# ---------------------------------------------------------
COREIOT_URL = "https://app.coreiot.io"
COREIOT_TOKEN = "1omr8yulbsmbyugm9yof"          # Token from the ESP32 node

# ---------------------------------------------------------
# Device ID Mapping
# ---------------------------------------------------------
# Map incoming JSON keys from CoreIoT to the internal device_id in your MySQL database
FEED_TO_DEVICE = {
    "temperature": 1,
    "humidity": 2,
    "soil": 3,
    "light": 4,
    "pump_status": 5,
    "light_status": 6
}