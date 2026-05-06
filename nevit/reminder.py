from nevit import NevitBot
import json
import os
import threading
import time
from datetime import datetime, timedelta

class Reminder:
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        self._load()
        self._start_checker()
    
    def _load(self):
        if os.path.exists('reminders.json'):
            with open('reminders.json', 'r', encoding='utf-8') as f:
                self.reminders = json.load(f)
    
    def _save(self):
        with open('reminders.json', 'w', encoding='utf-8') as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=2)
    
    def _parse_time(self, time_str):
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1])
                now = datetime.now()
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return None
        except:
            return None
    
    def _start_checker(self):
        def check():
            while True:
                now = datetime.now().isoformat()
                for uid, items in list(self.reminders.items()):
                    for item in items[:]:
                        if item['time'] <= now:
                            try:
                                self.bot.send_message(int(uid), f"🔔 *یادآوری:*\n\n{item['text']}")
                                items.remove(item)
                                self._save()
                            except:
                                pass
                time.sleep(60)
        threading.Thread(target=check, daemon=True).start()
    
    def set(self, user_id, text, remind_time):
        uid = str(user_id)
        if uid not in self.reminders:
            self.reminders[uid] = []
        self.reminders[uid].append({
            'text': text,
            'time': remind_time.isoformat()
        })
        self._save()
        return True
    
    def set_time(self, user_id, text, time_str):
        remind_time = self._parse_time(time_str)
        if not remind_time:
            return False
        return self.set(user_id, text, remind_time)
    
    def list(self, user_id):
        uid = str(user_id)
        if uid not in self.reminders or not self.reminders[uid]:
            return []
        return self.reminders[uid]
    
    def remove(self, user_id, index):
        uid = str(user_id)
        if uid in self.reminders and 0 <= index < len(self.reminders[uid]):
            removed = self.reminders[uid].pop(index)
            self._save()
            return True
        return False
    
    def clear(self, user_id):
        uid = str(user_id)
        if uid in self.reminders:
            self.reminders[uid] = []
            self._save()
            return True
        return False
    
    def setup_handlers(self):
        @self.bot.command(["remind", "یادآوری"])
        def cmd_remind(message):
            self.bot.set_state(message.from_user.id, "reminder_waiting_text")
            self.bot.reply(message, "📝 *متن یادآوری را وارد کنید:*")
        
        @self.bot.message()
        def handle_reminder_text(message):
            if self.bot.get_state(message.from_user.id) == "reminder_waiting_text":
                self.bot.set_state(message.from_user.id, "reminder_waiting_time", {"text": message.text})
                self.bot.reply(message, "⏰ *زمان را وارد کنید (مثال: 14:30)*")
        
        @self.bot.message()
        def handle_reminder_time(message):
            if self.bot.get_state(message.from_user.id) == "reminder_waiting_time":
                state_data = self.bot.get_state_data(message.from_user.id)
                remind_time = self._parse_time(message.text)
                if remind_time:
                    self.set(message.from_user.id, state_data['text'], remind_time)
                    self.bot.clear_state(message.from_user.id)
                    self.bot.reply(message, f"✅ *یادآوری تنظیم شد*\n\n📝 {state_data['text']}\n⏰ {message.text}")
                else:
                    self.bot.reply(message, "❌ *فرمت زمان صحیح نیست*\nلطفاً به صورت 14:30 وارد کنید")
        
        @self.bot.command(["myreminds", "یادآوری‌های من"])
        def cmd_list_reminds(message):
            items = self.list(message.from_user.id)
            if not items:
                self.bot.reply(message, "📭 *یادآوری فعالی ندارید*")
                return
            text = "📋 *یادآوری‌های شما:*\n\n"
            for i, item in enumerate(items):
                text += f"{i+1}. {item['text']}\n   🕐 {item['time']}\n\n"
            self.bot.reply(message, text)
        
        @self.bot.command(["delremind", "حذف_یادآوری"])
        def cmd_remove_remind(message):
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /delremind [شماره]")
                return
            try:
                index = int(parts[1]) - 1
                if self.remove(message.from_user.id, index):
                    self.bot.reply(message, "✅ *یادآوری حذف شد*")
                else:
                    self.bot.reply(message, "❌ *یادآوری یافت نشد*")
            except:
                self.bot.reply(message, "❌ *شماره نامعتبر است*")
        
        @self.bot.command(["clearreminds", "پاکسازی_یادآوری"])
        def cmd_clear_reminds(message):
            self.clear(message.from_user.id)
            self.bot.reply(message, "✅ *همه یادآوری‌ها حذف شدند*")