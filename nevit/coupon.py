from nevit import NevitBot
import json
import os
import random
import string
from datetime import datetime, timedelta

class Coupon:
    def __init__(self, bot):
        self.bot = bot
        self.coupons = {}
        self.used_coupons = {}
        self._load()
    
    def _load(self):
        if os.path.exists('coupons.json'):
            with open('coupons.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.coupons = data.get('coupons', {})
                self.used_coupons = data.get('used', {})
    
    def _save(self):
        with open('coupons.json', 'w', encoding='utf-8') as f:
            json.dump({
                'coupons': self.coupons,
                'used': self.used_coupons
            }, f, ensure_ascii=False, indent=2)
    
    def generate_code(self, length=8):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))
    
    def create_coupon(self, admin_id, discount_percent, expires_days=30, usage_limit=1):
        code = self.generate_code()
        self.coupons[code] = {
            'code': code,
            'discount': discount_percent,
            'expires_at': (datetime.now() + timedelta(days=expires_days)).isoformat(),
            'created_by': admin_id,
            'usage_limit': usage_limit,
            'used_count': 0
        }
        self._save()
        return code
    
    def validate_coupon(self, code, user_id):
        if code not in self.coupons:
            return False, "❌ کد نامعتبر است"
        
        coupon = self.coupons[code]
        expires_at = datetime.fromisoformat(coupon['expires_at'])
        
        if expires_at < datetime.now():
            return False, "❌ کد منقضی شده است"
        
        if coupon['used_count'] >= coupon['usage_limit']:
            return False, "❌ این کد قبلاً استفاده شده است"
        
        if user_id in self.used_coupons.get(code, []):
            return False, "❌ شما قبلاً از این کد استفاده کرده‌اید"
        
        return True, coupon['discount']
    
    def use_coupon(self, code, user_id):
        valid, result = self.validate_coupon(code, user_id)
        if not valid:
            return False, result
        
        self.coupons[code]['used_count'] += 1
        if code not in self.used_coupons:
            self.used_coupons[code] = []
        self.used_coupons[code].append(user_id)
        self._save()
        return True, result
    
    def setup_handlers(self):
        @self.bot.command(["createcoupon", "ساخت_کد"])
        def cmd_create_coupon(message):
            if message.from_user.id != 90416727:
                self.bot.reply(message, "⛔ *فقط ادمین می‌تواند کد تخفیف بسازد*")
                return
            
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /createcoupon [درصد تخفیف]\nمثال: /createcoupon 20")
                return
            
            try:
                discount = int(parts[1])
                code = self.create_coupon(message.from_user.id, discount)
                self.bot.reply(message, f"✅ *کد تخفیف ساخته شد:*\n\n🔹 `{code}`\n🔹 تخفیف: {discount}%\n🔹 اعتبار: 30 روز")
            except:
                self.bot.reply(message, "❌ *عدد معتبر وارد کنید*")
        
        @self.bot.command(["applycoupon", "اعمال_کد"])
        def cmd_apply_coupon(message):
            parts = message.text.split()
            if len(parts) != 2:
                self.bot.reply(message, "❌ *استفاده:* /applycoupon [کد]\nمثال: /applycoupon ABC123")
                return
            
            code = parts[1].upper()
            valid, result = self.validate_coupon(code, message.from_user.id)
            if valid:
                self.bot.set_state(message.from_user.id, "coupon_applied", {"discount": result, "code": code})
                self.bot.reply(message, f"✅ *کد تخفیف تأیید شد!*\n\n💰 تخفیف: {result}%\n🎉 هنگام خرید اعمال خواهد شد")
            else:
                self.bot.reply(message, f"❌ {result}")