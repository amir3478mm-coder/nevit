from nevit import NevitBot
import json
import os

class Referral:
    def __init__(self, bot):
        self.bot = bot
        self.referrals = {}
        self.rewards = {
            'per_invite': 10,
            'milestones': {5: 50, 10: 100, 25: 300, 50: 1000}
        }
        self._load()
    
    def _load(self):
        if os.path.exists('referrals.json'):
            with open('referrals.json', 'r', encoding='utf-8') as f:
                self.referrals = json.load(f)
    
    def _save(self):
        with open('referrals.json', 'w', encoding='utf-8') as f:
            json.dump(self.referrals, f, ensure_ascii=False, indent=2)
    
    def get_ref_code(self, user_id):
        uid = str(user_id)
        if uid not in self.referrals:
            self.referrals[uid] = {
                'code': str(user_id),
                'invites': 0,
                'points': 0,
                'invited_users': []
            }
            self._save()
        return self.referrals[uid]['code']
    
    def add_referral(self, user_id, referrer_id):
        if user_id == referrer_id:
            return False
        
        uid = str(user_id)
        rid = str(referrer_id)
        
        if uid in self.referrals and self.referrals[uid].get('referred_by'):
            return False
        
        if rid not in self.referrals:
            self.get_ref_code(referrer_id)
        
        if uid not in self.referrals:
            self.get_ref_code(user_id)
        
        self.referrals[uid]['referred_by'] = rid
        self.referrals[rid]['invites'] += 1
        self.referrals[rid]['points'] += self.rewards['per_invite']
        
        for milestone, bonus in self.rewards['milestones'].items():
            if self.referrals[rid]['invites'] == milestone:
                self.referrals[rid]['points'] += bonus
        
        self.referrals[rid]['invited_users'].append(uid)
        self._save()
        return True
    
    def get_stats(self, user_id):
        uid = str(user_id)
        if uid not in self.referrals:
            self.get_ref_code(user_id)
        data = self.referrals[uid]
        return {
            'code': data['code'],
            'invites': data['invites'],
            'points': data['points']
        }
    
    def setup_handlers(self):
        @self.bot.command(["ref", "referral", "دعوت"])
        def cmd_ref(message):
            stats = self.get_stats(message.from_user.id)
            bot_username = self.bot.bot_info['username']
            
            text = f"🎁 *سیستم دعوت NEVIT*\n\n"
            text += f"🔗 *لینک دعوت شما:*\n`https://ble.ir/{bot_username}?start={stats['code']}`\n\n"
            text += f"👥 *تعداد دعوت:* {stats['invites']}\n"
            text += f"⭐ *امتیاز شما:* {stats['points']}\n\n"
            text += f"🎯 *جوایز:*\n"
            text += f"• هر دعوت: {self.rewards['per_invite']} امتیاز\n"
            for milestone, bonus in self.rewards['milestones'].items():
                text += f"• {milestone} دعوت: +{bonus} امتیاز\n"
            
            self.bot.reply(message, text)
        
        @self.bot.command(["refstats", "آمار_دعوت"])
        def cmd_refstats(message):
            if message.from_user.id != 90416727:
                self.bot.reply(message, "⛔ *فقط ادمین*")
                return
            
            total_users = len(self.referrals)
            total_invites = sum(data.get('invites', 0) for data in self.referrals.values())
            top_users = sorted(self.referrals.items(), key=lambda x: x[1].get('invites', 0), reverse=True)[:5]
            
            text = f"📊 *آمار سیستم دعوت*\n\n"
            text += f"👥 کل کاربران: {total_users}\n"
            text += f"🔗 کل دعوت‌ها: {total_invites}\n\n"
            text += f"🏆 *برترین دعوت‌کنندگان:*\n"
            for i, (uid, data) in enumerate(top_users, 1):
                text += f"{i}. `{data['code']}` - {data.get('invites', 0)} دعوت\n"
            
            self.bot.reply(message, text)