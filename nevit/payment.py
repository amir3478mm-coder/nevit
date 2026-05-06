from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger("nevit")

class PaymentSystem:
    def __init__(self, bot, db_path: str = "nevit_bot.db"):
        self.bot = bot
        self.db_path = db_path
        self._init_db()
        self._payment_handlers = []
        self._pre_checkout_handlers = []
    
    def _get_connection(self):
        import sqlite3
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS nevit_wallets
                         (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0,
                          total_deposit INTEGER DEFAULT 0, total_spent INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS nevit_subscriptions
                         (user_id INTEGER PRIMARY KEY, plan TEXT, expires_at TEXT,
                          auto_renew INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS nevit_transactions
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                          type TEXT, amount INTEGER, description TEXT,
                          invoice_payload TEXT, status TEXT, created_at TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS nevit_products
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                          description TEXT, price INTEGER, payload TEXT)''')
        conn.commit()
        conn.close()
    
    def get_balance(self, user_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM nevit_wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    
    def add_balance(self, user_id: int, amount: int, description: str = ""):
        conn = self._get_connection()
        cursor = conn.cursor()
        current = self.get_balance(user_id)
        new_balance = current + amount
        cursor.execute("INSERT OR REPLACE INTO nevit_wallets (user_id, balance, total_deposit) VALUES (?, ?, COALESCE((SELECT total_deposit FROM nevit_wallets WHERE user_id = ?), 0) + ?)",
                      (user_id, new_balance, user_id, amount if amount > 0 else 0))
        cursor.execute("INSERT INTO nevit_transactions (user_id, type, amount, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, "deposit" if amount > 0 else "withdraw", abs(amount), description, "completed", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return new_balance
    
    def spend_balance(self, user_id: int, amount: int, description: str = "") -> bool:
        current = self.get_balance(user_id)
        if current < amount:
            return False
        conn = self._get_connection()
        cursor = conn.cursor()
        new_balance = current - amount
        cursor.execute("UPDATE nevit_wallets SET balance = ?, total_spent = COALESCE((SELECT total_spent FROM nevit_wallets WHERE user_id = ?), 0) + ? WHERE user_id = ?",
                      (new_balance, user_id, amount, user_id))
        cursor.execute("INSERT INTO nevit_transactions (user_id, type, amount, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, "spend", amount, description, "completed", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    
    def create_product(self, name: str, description: str, price: int, payload: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nevit_products (name, description, price, payload) VALUES (?, ?, ?, ?)",
                      (name, description, price, payload))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id
    
    def get_product(self, product_id: int) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, payload FROM nevit_products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "description": row[2], "price": row[3], "payload": row[4]}
        return None
    
    def get_all_products(self) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, payload FROM nevit_products")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "description": r[2], "price": r[3], "payload": r[4]} for r in rows]
    
    def create_invoice(self, user_id: int, product_id: int, provider_token: str = None) -> dict:
        product = self.get_product(product_id)
        if not product:
            return {"ok": False, "error": "Product not found"}
        
        payload = f"product_{product_id}_{user_id}_{int(datetime.now().timestamp())}"
        
        return self.bot.send_invoice(
            chat_id=user_id,
            title=product["name"],
            description=product["description"],
            payload=payload,
            provider_token=provider_token or "",
            currency="IRR",
            prices=[{"label": product["name"], "amount": product["price"]}]
        )
    
    def on_payment(self, func):
        self._payment_handlers.append(func)
        return func
    
    def on_pre_checkout(self, func):
        self._pre_checkout_handlers.append(func)
        return func
    
    def handle_pre_checkout(self, pre_checkout_query: dict):
        for handler in self._pre_checkout_handlers:
            try:
                result = handler(pre_checkout_query)
                if result is False:
                    self.bot.answer_pre_checkout_query(pre_checkout_query["id"], ok=False, error_message="پرداخت امکان پذیر نیست")
                    return
            except Exception as e:
                logger.error(f"Pre-checkout handler error: {e}")
                self.bot.answer_pre_checkout_query(pre_checkout_query["id"], ok=False, error_message="خطا در پردازش")
                return
        
        self.bot.answer_pre_checkout_query(pre_checkout_query["id"], ok=True)
    
    def handle_successful_payment(self, message):
        user_id = message.from_user.id
        payload = message.successful_payment.invoice_payload
        
        product_id = None
        parts = payload.split("_")
        if len(parts) >= 2 and parts[0] == "product":
            product_id = int(parts[1])
        
        product = self.get_product(product_id) if product_id else None
        amount = product["price"] if product else 0
        
        self.add_balance(user_id, amount, f"خرید محصول: {product['name'] if product else 'نامشخص'}")
        
        for handler in self._payment_handlers:
            try:
                handler(message, product)
            except Exception as e:
                logger.error(f"Payment handler error: {e}")
    
    def set_subscription(self, user_id: int, plan: str, days: int, auto_renew: bool = False):
        expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO nevit_subscriptions (user_id, plan, expires_at, auto_renew) VALUES (?, ?, ?, ?)",
                      (user_id, plan, expires_at, 1 if auto_renew else 0))
        conn.commit()
        conn.close()
    
    def get_subscription(self, user_id: int) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT plan, expires_at, auto_renew FROM nevit_subscriptions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"plan": row[0], "expires_at": row[1], "auto_renew": bool(row[2])}
        return None
    
    def is_subscription_active(self, user_id: int) -> bool:
        sub = self.get_subscription(user_id)
        if not sub:
            return False
        expires_at = datetime.fromisoformat(sub["expires_at"])
        return expires_at > datetime.now()
    
    def cancel_subscription(self, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM nevit_subscriptions WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def get_transactions(self, user_id: int, limit: int = 10) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, amount, description, status, created_at FROM nevit_transactions WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "type": r[1], "amount": r[2], "description": r[3], "status": r[4], "created_at": r[5]} for r in rows]
    
    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, balance FROM nevit_wallets ORDER BY balance DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"user_id": r[0], "balance": r[1]} for r in rows]