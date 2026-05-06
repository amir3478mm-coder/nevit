from nevit import NevitBot, InlineKeyboardMarkup, InlineKeyboardButton, Filters
import json
import os

class GroupManager:
    def __init__(self, bot):
        self.bot = bot
        self.welcome_settings = {}
        self.auto_delete_settings = {}
        self._load()
        self._setup_handlers()
    
    def _load(self):
        if os.path.exists('groups.json'):
            with open('groups.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.welcome_settings = data.get('welcome', {})
                self.auto_delete_settings = data.get('auto_delete', {})
    
    def _save(self):
        with open('groups.json', 'w', encoding='utf-8') as f:
            json.dump({
                'welcome': self.welcome_settings,
                'auto_delete': self.auto_delete_settings
            }, f, ensure_ascii=False, indent=2)
    
    def set_welcome(self, chat_id, message):
        self.welcome_settings[str(chat_id)] = message
        self._save()
    
    def get_welcome(self, chat_id):
        return self.welcome_settings.get(str(chat_id), None)
    
    def set_auto_delete(self, chat_id, seconds):
        self.auto_delete_settings[str(chat_id)] = seconds
        self._save()
    
    def get_auto_delete(self, chat_id):
        return self.auto_delete_settings.get(str(chat_id), 0)
    
    def _is_admin(self, message):
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            chat_member = self.bot.get_chat_member(chat_id, user_id)
            if chat_member and chat_member.get('ok'):
                status = chat_member.get('result', {}).get('status', '')
                return status in ['administrator', 'creator']
            return False
        except:
            return False
    
    def _setup_handlers(self):
        
        @self.bot.message(Filters.new_chat_members)
        def welcome_new_member(message):
            welcome_text = self.get_welcome(message.chat.id)
            if welcome_text:
                new_members = message.new_chat_members
                bot_info = self.bot.bot_info
                bot_id = bot_info.get('id') if isinstance(bot_info, dict) else None
                
                for member in new_members:
                    if bot_id and member.id == bot_id:
                        continue
                    if hasattr(member, 'first_name'):
                        text = welcome_text.replace('{name}', member.first_name)
                        self.bot.send_message(message.chat.id, text)
        
        @self.bot.message(Filters.left_chat_member)
        def goodbye_member(message):
            if message.left_chat_member:
                name = message.left_chat_member.first_name
                self.bot.send_message(message.chat.id, f"👋 {name} از گروه خارج شد")
        
        @self.bot.command(["setwelcome", "تنظیم_خوشامد"])
        def cmd_set_welcome(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند این دستور را اجرا کنند*")
                return
            
            self.bot.set_state(message.from_user.id, "group_waiting_welcome")
            self.bot.reply(message, "📝 *متن خوش‌آمدگویی را وارد کنید*\n(از {name} برای نام کاربر استفاده کنید)\n\nمثال: خوش آمدی {name} عزیز!")
        
        @self.bot.message()
        def handle_welcome(message):
            if self.bot.get_state(message.from_user.id) == "group_waiting_welcome":
                self.set_welcome(message.chat.id, message.text)
                self.bot.clear_state(message.from_user.id)
                self.bot.reply(message, "✅ *متن خوش‌آمدگویی تنظیم شد*")
        
        @self.bot.command(["deletewelcome", "حذف_خوشامد"])
        def cmd_delete_welcome(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند این دستور را اجرا کنند*")
                return
            
            self.welcome_settings.pop(str(message.chat.id), None)
            self._save()
            self.bot.reply(message, "✅ *متن خوش‌آمدگویی حذف شد*")
        
        @self.bot.command(["pin", "سنجاق"])
        def cmd_pin(message):
            if not message.reply_to_message:
                self.bot.reply(message, "❌ *به پیامی که می‌خواهید سنجاق کنید پاسخ دهید*")
                return
            
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند پیام سنجاق کنند*")
                return
            
            result = self.bot.pin_message(message.chat.id, message.reply_to_message.message_id)
            if result and result.get('ok'):
                self.bot.reply(message, "📌 *پیام سنجاق شد*")
            else:
                self.bot.reply(message, "❌ *خطا در سنجاق پیام*")
        
        @self.bot.command(["unpin", "برداشتن_سنجاق"])
        def cmd_unpin(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند سنجاق را بردارند*")
                return
            
            result = self.bot.unpin_message(message.chat.id)
            if result and result.get('ok'):
                self.bot.reply(message, "✅ *سنجاق برداشته شد*")
            else:
                self.bot.reply(message, "❌ *خطا در برداشتن سنجاق*")
        
        @self.bot.command(["setautodelete", "حذف_خودکار"])
        def cmd_set_auto_delete(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند این دستور را اجرا کنند*")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /setautodelete [ثانیه]\nمثال: /setautodelete 10")
                return
            
            try:
                seconds = int(parts[1])
                if seconds <= 0:
                    self.bot.reply(message, "❌ *عدد باید بزرگتر از صفر باشد*")
                    return
                self.set_auto_delete(message.chat.id, seconds)
                self.bot.reply(message, f"✅ *پیام‌ها پس از {seconds} ثانیه حذف می‌شوند*")
            except ValueError:
                self.bot.reply(message, "❌ *عدد معتبر وارد کنید*")
        
        @self.bot.command(["ban", "بن"])
        def cmd_ban(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند کاربر را بن کنند*")
                return
            
            if not message.reply_to_message:
                self.bot.reply(message, "❌ *به پیام کاربری که می‌خواهید بن کنید پاسخ دهید*")
                return
            
            user_id = message.reply_to_message.from_user.id
            result = self.bot.kick_member(message.chat.id, user_id)
            if result and result.get('ok'):
                self.bot.reply(message, f"✅ *کاربر {message.reply_to_message.from_user.first_name} بن شد*")
            else:
                self.bot.reply(message, "❌ *خطا در بن کردن کاربر*")
        
        @self.bot.command(["unban", "آنبن"])
        def cmd_unban(message):
            if not self._is_admin(message):
                self.bot.reply(message, "⛔ *فقط ادمین‌ها می‌توانند آنبن کنند*")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /unban [آیدی عددی کاربر]\nمثال: /unban 123456789")
                return
            
            try:
                user_id = int(parts[1])
                result = self.bot.unban_member(message.chat.id, user_id)
                if result and result.get('ok'):
                    self.bot.reply(message, f"✅ *کاربر {user_id} آنبن شد*")
                else:
                    self.bot.reply(message, "❌ *خطا در آنبن کردن کاربر*")
            except ValueError:
                self.bot.reply(message, "❌ *آیدی عددی معتبر وارد کنید*")
        
        @self.bot.command(["admins", "ادمین‌ها"])
        def cmd_admins(message):
            result = self.bot.get_chat_administrators(message.chat.id)
            if result and result.get('ok'):
                admins = result.get('result', [])
                if not admins:
                    self.bot.reply(message, "📭 *هیچ ادمینی یافت نشد*")
                    return
                
                text = "👑 *لیست ادمین‌های گروه:*\n\n"
                for admin in admins:
                    user = admin.get('user', {})
                    name = user.get('first_name', 'نامشخص')
                    username = user.get('username', '')
                    if username:
                        text += f"• {name} (@{username})\n"
                    else:
                        text += f"• {name}\n"
                self.bot.reply(message, text)
            else:
                self.bot.reply(message, "❌ *خطا در دریافت لیست ادمین‌ها*")