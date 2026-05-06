from nevit import NevitBot
import json
import os
import math

class Levels:
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self._load()
    
    def _load(self):
        if os.path.exists('levels.json'):
            with open('levels.json', 'r', encoding='utf-8') as f:
                self.users = json.load(f)
    
    def _save(self):
        with open('levels.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def get_level(self, exp):
        return int(math.sqrt(exp / 100)) + 1
    
    def get_next_level_exp(self, current_exp):
        current_level = self.get_level(current_exp)
        return (current_level ** 2) * 100
    
    def add_exp(self, user_id, amount):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {'exp': 0, 'total_messages': 0, 'level_up_notify': True}
        
        old_level = self.get_level(self.users[uid]['exp'])
        self.users[uid]['exp'] += amount
        self.users[uid]['total_messages'] += 1
        new_level = self.get_level(self.users[uid]['exp'])
        
        self._save()
        
        if new_level > old_level and self.users[uid].get('level_up_notify', True):
            return new_level
        return None
    
    def get_user_info(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            return {
                'exp': 0,
                'level': 1,
                'total_messages': 0,
                'next_level_exp': 100
            }
        exp = self.users[uid]['exp']
        level = self.get_level(exp)
        next_exp = self.get_next_level_exp(exp)
        return {
            'exp': exp,
            'level': level,
            'total_messages': self.users[uid].get('total_messages', 0),
            'next_level_exp': next_exp,
            'exp_needed': next_exp - exp,
            'level_up_notify': self.users[uid].get('level_up_notify', True)
        }
    
    def get_leaderboard(self, limit=10):
        sorted_users = sorted(self.users.items(), key=lambda x: x[1].get('exp', 0), reverse=True)
        return [(uid, data) for uid, data in sorted_users[:limit]]
    
    def add_points(self, user_id, points):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {'exp': 0, 'total_messages': 0}
        self.users[uid]['points'] = self.users[uid].get('points', 0) + points
        self._save()
        return self.users[uid]['points']
    
    def get_points(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            return 0
        return self.users[uid].get('points', 0)
    
    def setup_handlers(self):
        @self.bot.message()
        def on_message(message):
            if message.text and not message.text.startswith('/'):
                new_level = self.add_exp(message.from_user.id, 10)
                if new_level:
                    self.bot.reply(message, f"🎉 *تبریک! به لول {new_level} رسیدید!* 🎉")
        
        @self.bot.command(["level", "لول"])
        def cmd_level(message):
            info = self.get_user_info(message.from_user.id)
            progress = int((info['exp'] / info['next_level_exp']) * 20)
            bar = "█" * progress + "░" * (20 - progress)
            text = f"📊 *آمار شما:*\n\n"
            text += f"🎯 *لول:* {info['level']}\n"
            text += f"⭐ *امتیاز:* {info['exp']}\n"
            text += f"📈 *تا لول بعدی:* {info['exp_needed']}\n"
            text += f"📊 *پیشرفت:*\n{bar} {int((info['exp'] / info['next_level_exp'])*100)}%\n"
            text += f"💬 *پیام‌ها:* {info['total_messages']}\n"
            text += f"💰 *نقاط جایزه:* {self.get_points(message.from_user.id)}"
            self.bot.reply(message, text)
        
        @self.bot.command(["leaderboard", "برترین‌ها"])
        def cmd_leaderboard(message):
            top_users = self.get_leaderboard(10)
            if not top_users:
                self.bot.reply(message, "📭 *هنوز کاربری ثبت نشده است*")
                return
            
            text = "🏆 *برترین کاربران:*\n\n"
            for i, (uid, data) in enumerate(top_users, 1):
                try:
                    name = self.bot.get_chat_member(message.chat.id, int(uid)).get('result', {}).get('user', {}).get('first_name', 'کاربر')
                except:
                    name = 'کاربر'
                level = self.get_level(data.get('exp', 0))
                text += f"{i}. {name} - لول {level} - {data.get('exp', 0)} امتیاز\n"
            
            self.bot.reply(message, text)
        
        @self.bot.command(["points", "امتیاز"])
        def cmd_points(message):
            points = self.get_points(message.from_user.id)
            self.bot.reply(message, f"💰 *نقاط جایزه شما:* {points}\n\nبرای کسب امتیاز بیشتر، فعال باشید!")