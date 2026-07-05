import os
import sys
from dotenv import load_dotenv, find_dotenv

# Automatically find and load the .env file
env_path = find_dotenv()
if not env_path:
    print("❌ FATAL ERROR: .env file not found!")
    sys.exit(1)

load_dotenv(override=True)

# Export all configurations globally
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
CREDENTIALS_FILE = "credentials.json"

# Security assertion upon startup
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("❌ FATAL ERROR: TELEGRAM_TOKEN or GEMINI_API_KEY is missing in .env file!")
    sys.exit(1)