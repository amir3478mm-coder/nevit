from nevit import NevitBot
import json
import os
from datetime import datetime, timedelta

class VIP:
    def __init__(self, bot):
        self.bot = bot
        self.vip_users = {}
        self.plans = {
            'bronze': {'price': 50000, 'days': 30, 'color': '🥉', 'features': ['بدون تبلیغ', 'پشتیبانی優先']},
            'silver': {'price': 100000, 'days': 30, 'color': '🥈', 'features': ['بدون تبلیغ', 'پشتیبانی優先', 'تخفیف 10%', 'ایموجی اختصاصی']},
            'gold': {'price': 200000, 'days': 30, 'color': '🥇', 'features': ['بدون تبلیغ', 'پشتیبانی優先', 'تخفیف 20%', 'ایموجی اختصاصی', 'دسترسی زودهنگام']}
        }
        self._load()
        self._setup_handlers()
    
    def _load(self):
        if os.path.exists('vip.json'):
            with open('vip.json', 'r', encoding='utf-8') as f:
                self.vip_users = json.load(f)
    
    def _save(self):
        with open('vip.json', 'w', encoding='utf-8') as f:
            json.dump(self.vip_users, f, ensure_ascii=False, indent=2)
    
    def is_vip(self, user_id):
        uid = str(user_id)
        if uid not in self.vip_users:
            return False
        expiry = datetime.fromisoformat(self.vip_users[uid]['expiry'])
        if expiry < datetime.now():
            return False
        return True
    
    def get_vip_info(self, user_id):
        uid = str(user_id)
        if uid not in self.vip_users:
            return None
        expiry = datetime.fromisoformat(self.vip_users[uid]['expiry'])
        remaining = (expiry - datetime.now()).days
        plan = self.vip_users[uid]['plan']
        return {
            'plan': plan,
            'expiry': expiry,
            'remaining_days': remaining,
            'color': self.plans[plan]['color'],
            'features': self.plans[plan]['features']
        }
    
    def add_vip(self, user_id, plan, days=None):
        uid = str(user_id)
        if plan not in self.plans:
            return False
        
        if not days:
            days = self.plans[plan]['days']
        
        expiry = datetime.now() + timedelta(days=days)
        
        if uid in self.vip_users and self.is_vip(user_id):
            old_expiry = datetime.fromisoformat(self.vip_users[uid]['expiry'])
            if old_expiry > datetime.now():
                expiry = old_expiry + timedelta(days=days)
        
        self.vip_users[uid] = {
            'plan': plan,
            'expiry': expiry.isoformat(),
            'activated_at': datetime.now().isoformat()
        }
        self._save()
        return True
    
    def get_vip_badge(self, user_id):
        if not self.is_vip(user_id):
            return ''
        info = self.get_vip_info(user_id)
        return f"{info['color']} VIP {info['plan'].title()} "
    
    def _setup_handlers(self):
        @self.bot.command(["vip", "membership", "عضویت"])
        def cmd_vip(message):
            if self.is_vip(message.from_user.id):
                info = self.get_vip_info(message.from_user.id)
                text = f"{info['color']} *وضعیت عضویت ویژه شما:*\n\n"
                text += f"📋 *پلن:* {info['plan'].title()}\n"
                text += f"📅 *اعتبار تا:* {info['expiry'].strftime('%Y-%m-%d')}\n"
                text += f"⏳ *روزهای باقیمانده:* {info['remaining_days']}\n\n"
                text += f"✨ *مزایا:*\n"
                for feat in info['features']:
                    text += f"✅ {feat}\n"
            else:
                text = "👑 *عضویت ویژه NEVIT*\n\n"
                text += "مزایای عضویت:\n"
                for plan, details in self.plans.items():
                    text += f"\n{details['color']} *{plan.title()}* - {details['price']} تومان/{details['days']} روز\n"
                    for feat in details['features']:
                        text += f"  ✓ {feat}\n"
                text += "\n🚀 برای خرید: /buy_vip [plan]"
            self.bot.reply(message, text)
        
        @self.bot.command(["buy_vip", "خرید_ویژه"])
        def cmd_buy_vip(message):
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /buy_vip [bronze/silver/gold]")
                return
            
            plan = parts[1].lower()
            if plan not in self.plans:
                self.bot.reply(message, "❌ *پلن نامعتبر است*\nموجود: bronze, silver, gold")
                return
            
            price = self.plans[plan]['price']
            self.bot.send_invoice(
                chat_id=message.chat.id,
                title=f"خرید اشتراک {plan.title()}",
                description=f"اشتراک {plan.title()} به مدت {self.plans[plan]['days']} روز",
                payload=f"vip_{plan}",
                provider_token="",
                currency="IRR",
                prices=[{"label": f"اشتراک {plan.title()}", "amount": price}]
            )
        
        @self.bot.on("successful_payment")
        def on_vip_payment(message):
            if hasattr(message, 'successful_payment') and message.successful_payment:
                payload = message.successful_payment.get('invoice_payload', '')
                if payload.startswith('vip_'):
                    plan = payload.replace('vip_', '')
                    self.add_vip(message.from_user.id, plan)
                    self.bot.reply(message, f"✅ *عضویت {plan.title()} با موفقیت فعال شد!*\n\nاز مزایای ویژه استفاده کنید.")