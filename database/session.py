import sqlite3
import json
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")

def init_db():
    """Initialize local database and enable WAL mode for high concurrency."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable Write-Ahead Logging to significantly improve concurrent R/W performance
    cursor.execute('PRAGMA journal_mode=WAL;') 
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_transactions (
            txn_id TEXT PRIMARY KEY,
            user_id TEXT,
            ai_data TEXT,
            receipt_link TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_pending(user_id: str, ai_data: dict, receipt_link: str) -> str:
    """Save AI extracted data temporarily and return a unique transaction ID."""
    
    txn_id = "TXN_" + str(uuid.uuid4())[:8].upper() 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pending_transactions (txn_id, user_id, ai_data, receipt_link, status) VALUES (?, ?, ?, ?, ?)",
        (txn_id, user_id, json.dumps(ai_data), receipt_link, "PENDING")
    )
    conn.commit()
    conn.close()
    return txn_id

def get_and_complete_pending(txn_id):
    """Fetch pending data and delete the record upon completion."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Crucial for accessing columns by name
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pending_transactions WHERE txn_id = ?", (txn_id,))
    row = cursor.fetchone()
    
    if row:
        data = {
            "txn_id": row["txn_id"],
            "user_id": row["user_id"],      
            "ai_data": json.loads(row["ai_data"]),
            "local_path": row["receipt_link"] 
        }
        # Delete record after processing to prevent duplicates
        cursor.execute("DELETE FROM pending_transactions WHERE txn_id = ?", (txn_id,))
        conn.commit()
        conn.close()
        return data
    conn.close()
    return None

def get_pending(txn_id: str) -> dict:
    """Read pending data without changing its status (used for editing UI)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ai_data, receipt_link FROM pending_transactions WHERE txn_id = ? AND status = 'PENDING'", (txn_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "ai_data": json.loads(row[0]),
            "receipt_link": row[1]
        }
    return None

def update_pending_data(txn_id: str, new_ai_data: dict):
    """Update pending AI data (used to save user manual modifications)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pending_transactions SET ai_data = ? WHERE txn_id = ?",
        (json.dumps(new_ai_data), txn_id)
    )
    conn.commit()
    conn.close()