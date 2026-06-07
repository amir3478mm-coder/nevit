import json
import os
import asyncio
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import threading
import time as time_module

@dataclass
class BackupSchedule:
    hour: int
    minute: int
    chat_id: int
    last_run: Optional[str] = None

class SmartBackup:
    def __init__(self, bot, db_instance, backup_dir: str = "smart_backups"):
        self.bot = bot
        self.db = db_instance
        self.backup_dir = backup_dir
        self.schedules: List[BackupSchedule] = []
        self._scheduler_thread = None
        self._running = False
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        self._load_schedules()
    
    def _get_db_path(self) -> str:
        if hasattr(self.db, 'db_path'):
            return self.db.db_path
        return "nevit_bot.db"
    
    def _get_connection(self):
        db_path = self._get_db_path()
        return sqlite3.connect(db_path)
    
    def _load_schedules(self):
        schedule_file = os.path.join(self.backup_dir, "schedules.json")
        if os.path.exists(schedule_file):
            with open(schedule_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    self.schedules.append(BackupSchedule(
                        hour=item["hour"],
                        minute=item["minute"],
                        chat_id=item["chat_id"],
                        last_run=item.get("last_run")
                    ))
    
    def _save_schedules(self):
        schedule_file = os.path.join(self.backup_dir, "schedules.json")
        data = []
        for s in self.schedules:
            data.append({
                "hour": s.hour,
                "minute": s.minute,
                "chat_id": s.chat_id,
                "last_run": s.last_run
            })
        with open(schedule_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def backup_users_to_json(self, user_ids: List[int] = None) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if user_ids:
            placeholders = ",".join("?" for _ in user_ids)
            cursor.execute(f"SELECT user_id, username, first_name, data, created_at FROM users WHERE user_id IN ({placeholders})", user_ids)
        else:
            cursor.execute("SELECT user_id, username, first_name, data, created_at FROM users")
        
        rows = cursor.fetchall()
        conn.close()
        
        users_data = []
        for row in rows:
            users_data.append({
                "user_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "data": json.loads(row[3]) if row[3] else {},
                "created_at": row[4]
            })
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        backup_info = {
            "backup_time": datetime.now().isoformat(),
            "total_users": len(users_data),
            "users": users_data
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_backup_list(self) -> List[Dict]:
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("backup_") and filename.endswith(".json"):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "name": filename,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def add_schedule(self, hour: int, minute: int, chat_id: int):
        for s in self.schedules:
            if s.chat_id == chat_id:
                self.schedules.remove(s)
        
        self.schedules.append(BackupSchedule(hour=hour, minute=minute, chat_id=chat_id))
        self._save_schedules()
        self._start_scheduler()
        return True
    
    def remove_schedule(self, chat_id: int):
        self.schedules = [s for s in self.schedules if s.chat_id != chat_id]
        self._save_schedules()
    
    def get_schedule(self, chat_id: int) -> Optional[BackupSchedule]:
        for s in self.schedules:
            if s.chat_id == chat_id:
                return s
        return None
    
    def _start_scheduler(self):
        if self._scheduler_thread and self._running:
            return
        
        self._running = True
        
        def scheduler_loop():
            while self._running:
                now = datetime.now()
                for schedule in self.schedules:
                    if schedule.hour == now.hour and schedule.minute == now.minute:
                        if schedule.last_run != now.strftime("%Y-%m-%d %H:%M"):
                            self._execute_backup(schedule)
                            schedule.last_run = now.strftime("%Y-%m-%d %H:%M")
                            self._save_schedules()
                time_module.sleep(60)
        
        self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._scheduler_thread.start()
    
    def _get_or_create_event_loop(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    
    def _execute_backup(self, schedule: BackupSchedule):
        try:
            filepath = self.backup_users_to_json()
            
            with open(filepath, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            
            summary = f"""
📦 *گزارش بکاپ خودکار*

🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👥 تعداد کاربران: {backup_data['total_users']}
📁 نام فایل: `{os.path.basename(filepath)}`
💾 حجم: {os.path.getsize(filepath)} bytes

✅ بکاپ با موفقیت انجام شد
"""
            self.bot.send_message(schedule.chat_id, summary)
            
            loop = self._get_or_create_event_loop()
            
            future = asyncio.run_coroutine_threadsafe(
                self.bot.send_document(schedule.chat_id, filepath, caption="📁 فایل بکاپ کاربران"),
                loop
            )
            future.result(timeout=60)
            
        except Exception as e:
            self.bot.send_message(schedule.chat_id, f"❌ خطا در بکاپ خودکار: {str(e)}")
    
    def stop_scheduler(self):
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)