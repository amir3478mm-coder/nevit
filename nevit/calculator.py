from nevit import NevitBot
import re

class Calculator:
    def __init__(self, bot):
        self.bot = bot
    
    def calculate(self, expression):
        try:
            safe_chars = set('0123456789+-*/%(). ')
            if not all(c in safe_chars for c in expression):
                return None
            result = eval(expression)
            return round(result, 2)
        except:
            return None
    
    def convert_currency(self, amount, from_cur, to_cur):
        rates = {
            'USD': 1, 'EUR': 0.92, 'GBP': 0.79, 'IRR': 42000
        }
        from_cur = from_cur.upper()
        to_cur = to_cur.upper()
        if from_cur not in rates or to_cur not in rates:
            return None
        usd_amount = amount / rates[from_cur]
        result = usd_amount * rates[to_cur]
        return round(result, 2)
    
    def convert_length(self, amount, from_unit, to_unit):
        units = {
            'm': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001,
            'mile': 1609.34, 'yard': 0.9144, 'foot': 0.3048
        }
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        if from_unit not in units or to_unit not in units:
            return None
        meters = amount * units[from_unit]
        result = meters / units[to_unit]
        return round(result, 2)
    
    def convert_weight(self, amount, from_unit, to_unit):
        units = {
            'kg': 1, 'g': 0.001, 'mg': 0.000001, 'lb': 0.453592,
            'oz': 0.0283495, 'ton': 1000
        }
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        if from_unit not in units or to_unit not in units:
            return None
        kgs = amount * units[from_unit]
        result = kgs / units[to_unit]
        return round(result, 2)
    
    def setup_handlers(self):
        @self.bot.command(["calc", "calculate", "ماشین_حساب"])
        def cmd_calc(message):
            self.bot.set_state(message.from_user.id, "calc_waiting")
            self.bot.reply(message, "🧮 *عبارت ریاضی را وارد کنید:*\nمثال: 2+2*3 یا 10%3")
        
        @self.bot.message()
        def handle_calc(message):
            if self.bot.get_state(message.from_user.id) == "calc_waiting":
                result = self.calculate(message.text)
                if result is not None:
                    self.bot.reply(message, f"🧮 *نتیجه:* `{result}`")
                else:
                    self.bot.reply(message, "❌ *عبارت نامعتبر است*")
                self.bot.clear_state(message.from_user.id)
        
        @self.bot.command(["convert", "تبدیل"])
        def cmd_convert(message):
            self.bot.set_state(message.from_user.id, "convert_waiting")
            self.bot.reply(message, "📐 *فرمت تبدیل را وارد کنید:*\n\nمثال ارز: 100 USD IRR\nمثال طول: 10 km m\nمثال وزن: 5 kg lb")
        
        @self.bot.message()
        def handle_convert(message):
            if self.bot.get_state(message.from_user.id) == "convert_waiting":
                parts = message.text.split()
                if len(parts) != 3:
                    self.bot.reply(message, "❌ *فرمت اشتباه است*\nمثال: 100 USD IRR")
                    return
                
                try:
                    amount = float(parts[0])
                    from_unit = parts[1]
                    to_unit = parts[2]
                    
                    result = self.convert_currency(amount, from_unit, to_unit)
                    if result:
                        self.bot.reply(message, f"💰 *نتیجه:* {amount} {from_unit} = {result} {to_unit}")
                    else:
                        result = self.convert_length(amount, from_unit, to_unit)
                        if result:
                            self.bot.reply(message, f"📏 *نتیجه:* {amount} {from_unit} = {result} {to_unit}")
                        else:
                            result = self.convert_weight(amount, from_unit, to_unit)
                            if result:
                                self.bot.reply(message, f"⚖️ *نتیجه:* {amount} {from_unit} = {result} {to_unit}")
                            else:
                                self.bot.reply(message, "❌ *واحد نامعتبر است*")
                except:
                    self.bot.reply(message, "❌ *عدد نامعتبر است*")
                
                self.bot.clear_state(message.from_user.id)
        
        @self.bot.command(["currency", "ارز"])
        def cmd_currency(message):
            parts = message.text.split()
            if len(parts) != 3:
                self.bot.reply(message, "❌ *استفاده:* /currency [مقدار] [از] [به]\nمثال: /currency 100 USD IRR")
                return
            try:
                amount = float(parts[1])
                from_cur = parts[2]
                to_cur = parts[3]
                result = self.convert_currency(amount, from_cur, to_cur)
                if result:
                    self.bot.reply(message, f"💰 *نتیجه:* {amount} {from_cur} = {result} {to_cur}")
                else:
                    self.bot.reply(message, "❌ *ارز نامعتبر است*")
            except:
                self.bot.reply(message, "❌ *عدد نامعتبر است*")