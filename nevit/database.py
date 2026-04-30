import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "nevit_bot.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                data TEXT,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"user_id": row[0], "username": row[1], "first_name": row[2], "data": json.loads(row[3]) if row[3] else {}, "created_at": row[4]}
        return None
    
    def save_user(self, user_id: int, data: dict, username: str = None, first_name: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        existing = self.get_user(user_id)
        if existing:
            cursor.execute("UPDATE users SET data = ? WHERE user_id = ?", (json.dumps(data), user_id))
        else:
            cursor.execute("INSERT INTO users (user_id, username, first_name, data, created_at) VALUES (?, ?, ?, ?, ?)",
                          (user_id, username, first_name, json.dumps(data), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str, default: str = None) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()