import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ---------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------
# It is highly recommended to use environment variables in production (Railway)
DB_HOST = os.getenv("DB_HOST", "") 
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "railway")

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