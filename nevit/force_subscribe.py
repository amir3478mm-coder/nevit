from nevit import NevitBot, InlineKeyboardMarkup, InlineKeyboardButton

class ForceSubscribe:
    def __init__(self, bot):
        self.bot = bot
        self.required_channels = {}
        self._load()
    
    def _load(self):
        import json, os
        if os.path.exists('force_subs.json'):
            with open('force_subs.json', 'r', encoding='utf-8') as f:
                self.required_channels = json.load(f)
    
    def _save(self):
        import json, os
        with open('force_subs.json', 'w', encoding='utf-8') as f:
            json.dump(self.required_channels, f, ensure_ascii=False, indent=2)
    
    def set_channel(self, bot_username, channel_username):
        self.required_channels[bot_username] = channel_username
        self._save()
    
    def get_channel(self, bot_username):
        return self.required_channels.get(bot_username, None)
    
    def is_member(self, user_id, channel_username):
        try:
            member = self.bot.get_chat_member(f"@{channel_username}", user_id)
            if member.get('ok'):
                status = member.get('result', {}).get('status', '')
                return status in ['member', 'administrator', 'creator']
            return False
        except:
            return False
    
    def setup_handlers(self):
        @self.bot.command(["setchannel", "تنظیم_کانال"])
        def cmd_set_channel(message):
            if message.from_user.id != 90416727:
                self.bot.reply(message, "⛔ *فقط ادمین می‌تواند این دستور را اجرا کند*")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /setchannel [یوزرنیم کانال]\nمثال: /setchannel mychannel")
                return
            
            channel = parts[1].replace('@', '')
            self.set_channel(self.bot.bot_info['username'], channel)
            self.bot.reply(message, f"✅ *عضویت اجباری در کانال @{channel} تنظیم شد*")
        
        @self.bot.message()
        def check_membership(message):
            if message.from_user.id == 90416727:
                return
            
            channel = self.get_channel(self.bot.bot_info['username'])
            if channel and not self.is_member(message.from_user.id, channel):
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://ble.ir/{channel}"))
                kb.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_member"))
                
                self.bot.reply(message, f"⚠️ *برای استفاده از ربات، ابتدا در کانال زیر عضو شوید:*\n\n🔹 @{channel}", reply_markup=kb.to_dict())
                return
        
        @self.bot.callback("check_member")
        def check_member_callback(callback, data):
            channel = self.get_channel(self.bot.bot_info['username'])
            if not channel:
                self.bot.answer_callback(callback.id, "✅ دسترسی آزاد است", show_alert=True)
                return
            
            if self.is_member(callback.from_user.id, channel):
                self.bot.edit_message_text(callback.chat.id, callback.message_id, "✅ *عضویت شما تأیید شد*\nاکنون می‌توانید از ربات استفاده کنید.")
                self.bot.answer_callback(callback.id, "✅ تأیید شد", show_alert=False)
            else:
                self.bot.answer_callback(callback.id, "❌ هنوز عضو نشده‌اید", show_alert=True)