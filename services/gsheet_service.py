import gspread
import time
import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from core.config import SPREADSHEET_NAME, CREDENTIALS_FILE

# --- Unified OAuth 2.0 Login Logic ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Establish global connection
creds = get_credentials()
gsheets_client = gspread.authorize(creds)
sheet_doc = gsheets_client.open(SPREADSHEET_NAME)

# --- Caching Mechanism ---
_settings_cache = {}
CACHE_TTL = 600

def get_system_settings():
    global _settings_cache
    current_time = time.time()
    if "data" in _settings_cache and (current_time - _settings_cache["timestamp"] < CACHE_TTL):
        return _settings_cache["data"]

    users_data = sheet_doc.worksheet("Settings_Users").get_all_records()
    active_users = [str(u['Telegram_ID']) for u in users_data if u.get('Status') == 'Active']
    
    coa_data = sheet_doc.worksheet("Settings_COA").get_all_records()
    categories = [c['Category_Name'] for c in coa_data]
    
    pay_data = sheet_doc.worksheet("Settings_Payment").get_all_records()
    payments = [p['Payment_Channel'] for p in pay_data]
    
    result = (active_users, categories, payments)
    _settings_cache["data"] = result
    _settings_cache["timestamp"] = current_time
    return result

# --- Transaction ID Generator ---
def generate_txn_id(user_id):
    today = datetime.now().strftime("%Y%m%d")
    worksheet = sheet_doc.worksheet("Transactions")
    records = worksheet.get_all_records()
    count = sum(1 for r in records if str(user_id) in str(r.get('User_ID', '')) and today in str(r.get('Txn_ID', '')))
    return f"{user_id}{today}{count+1:06d}"

# --- Write Logic ---
def append_transaction(data: dict, receipt_link: str, user_id: str, txn_id: str):
    worksheet = sheet_doc.worksheet("Transactions")
    row = [
        txn_id, user_id, data.get("Date", ""), data.get("Vendor", ""), 
        data.get("Company_Reg_No", ""), data.get("Invoice_No", ""),
        data.get("Amount", ""), data.get("Tax_Amount", ""),
        data.get("Category", ""), data.get("Payment_Method", ""), 
        "Unreconciled", receipt_link
    ]
    worksheet.append_row(row)