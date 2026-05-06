from nevit import NevitBot, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from datetime import datetime, timedelta

class Booking:
    def __init__(self, bot):
        self.bot = bot
        self.services = {}
        self.appointments = {}
        self._load()
    
    def _load(self):
        if os.path.exists('services.json'):
            with open('services.json', 'r', encoding='utf-8') as f:
                self.services = json.load(f)
        if os.path.exists('appointments.json'):
            with open('appointments.json', 'r', encoding='utf-8') as f:
                self.appointments = json.load(f)
    
    def _save_services(self):
        with open('services.json', 'w', encoding='utf-8') as f:
            json.dump(self.services, f, ensure_ascii=False, indent=2)
    
    def _save_appointments(self):
        with open('appointments.json', 'w', encoding='utf-8') as f:
            json.dump(self.appointments, f, ensure_ascii=False, indent=2)
    
    def add_service(self, admin_id, name, duration, price):
        if str(admin_id) not in self.services:
            self.services[str(admin_id)] = []
        service_id = len(self.services[str(admin_id)]) + 1
        self.services[str(admin_id)].append({
            'id': service_id,
            'name': name,
            'duration': duration,
            'price': price
        })
        self._save_services()
        return service_id
    
    def get_services(self, admin_id):
        return self.services.get(str(admin_id), [])
    
    def book(self, user_id, admin_id, service_id, date, time):
        admin_id_str = str(admin_id)
        if admin_id_str not in self.appointments:
            self.appointments[admin_id_str] = []
        
        appointment = {
            'user_id': user_id,
            'service_id': service_id,
            'date': date,
            'time': time,
            'status': 'pending',
            'booked_at': datetime.now().isoformat()
        }
        self.appointments[admin_id_str].append(appointment)
        self._save_appointments()
        return True
    
    def get_user_appointments(self, user_id):
        result = []
        for admin_id, appointments in self.appointments.items():
            for app in appointments:
                if app['user_id'] == user_id:
                    result.append({
                        'admin_id': int(admin_id),
                        **app
                    })
        return result
    
    def setup_handlers(self):
        @self.bot.command(["service", "سرویس"])
        def cmd_add_service(message):
            if message.from_user.id != 90416727:
                self.bot.reply(message, "⛔ *فقط ادمین می‌تواند سرویس اضافه کند*")
                return
            
            self.bot.set_state(message.from_user.id, "booking_service_name")
            self.bot.reply(message, "📝 *نام سرویس را وارد کنید:*")
        
        @self.bot.message()
        def handle_service_name(message):
            if self.bot.get_state(message.from_user.id) == "booking_service_name":
                state_data = self.bot.get_state_data(message.from_user.id)
                self.bot.set_state(message.from_user.id, "booking_service_duration", {"name": message.text})
                self.bot.reply(message, "⏰ *مدت زمان (دقیقه) را وارد کنید:*")
        
        @self.bot.message()
        def handle_service_duration(message):
            if self.bot.get_state(message.from_user.id) == "booking_service_duration":
                try:
                    duration = int(message.text)
                    state_data = self.bot.get_state_data(message.from_user.id)
                    self.bot.set_state(message.from_user.id, "booking_service_price", {"name": state_data['name'], "duration": duration})
                    self.bot.reply(message, "💰 *قیمت (تومان) را وارد کنید:*")
                except:
                    self.bot.reply(message, "❌ *عدد معتبر وارد کنید*")
        
        @self.bot.message()
        def handle_service_price(message):
            if self.bot.get_state(message.from_user.id) == "booking_service_price":
                try:
                    price = int(message.text)
                    state_data = self.bot.get_state_data(message.from_user.id)
                    self.add_service(message.from_user.id, state_data['name'], state_data['duration'], price)
                    self.bot.clear_state(message.from_user.id)
                    self.bot.reply(message, f"✅ *سرویس {state_data['name']} اضافه شد*")
                except:
                    self.bot.reply(message, "❌ *عدد معتبر وارد کنید*")
        
        @self.bot.command(["services", "سرویس‌ها"])
        def cmd_services(message):
            services = self.get_services(90416727)
            if not services:
                self.bot.reply(message, "📭 *هیچ سرویسی تعریف نشده است*")
                return
            
            text = "📋 *لیست سرویس‌ها:*\n\n"
            for s in services:
                text += f"{s['id']}. {s['name']}\n   ⏰ {s['duration']} دقیقه\n   💰 {s['price']} تومان\n\n"
            
            kb = InlineKeyboardMarkup()
            for s in services:
                kb.add(InlineKeyboardButton(f"📌 {s['name']}", callback_data=f"book_{s['id']}"))
            
            self.bot.reply(message, text, reply_markup=kb.to_dict())
        
        @self.bot.callback("book_")
        def handle_book(callback, data):
            service_id = int(data.split('_')[1])
            services = self.get_services(90416727)
            service = next((s for s in services if s['id'] == service_id), None)
            if not service:
                self.bot.answer_callback(callback.id, "❌ سرویس یافت نشد", show_alert=True)
                return
            
            self.bot.set_state(callback.from_user.id, "booking_date", {"service_id": service_id})
            self.bot.edit_message_text(callback.message.chat.id, callback.message.message_id, f"📅 *تاریخ رزرو را وارد کنید:*\nمثال: 1404/02/15")
            self.bot.answer_callback(callback.id)
        
        @self.bot.message()
        def handle_booking_date(message):
            if self.bot.get_state(message.from_user.id) == "booking_date":
                state_data = self.bot.get_state_data(message.from_user.id)
                self.bot.set_state(message.from_user.id, "booking_time", {"service_id": state_data['service_id'], "date": message.text})
                self.bot.reply(message, "⏰ *ساعت رزرو را وارد کنید:*\nمثال: 14:30")
        
        @self.bot.message()
        def handle_booking_time(message):
            if self.bot.get_state(message.from_user.id) == "booking_time":
                state_data = self.bot.get_state_data(message.from_user.id)
                self.book(message.from_user.id, 90416727, state_data['service_id'], state_data['date'], message.text)
                self.bot.clear_state(message.from_user.id)
                self.bot.reply(message, f"✅ *رزرو شما ثبت شد*\n📅 {state_data['date']}\n⏰ {message.text}")
        
        @self.bot.command(["mybookings", "رزروهای من"])
        def cmd_my_bookings(message):
            bookings = self.get_user_appointments(message.from_user.id)
            if not bookings:
                self.bot.reply(message, "📭 *رزروی ندارید*")
                return
            
            text = "📋 *رزروهای شما:*\n\n"
            for b in bookings:
                services = self.get_services(b['admin_id'])
                service = next((s for s in services if s['id'] == b['service_id']), None)
                service_name = service['name'] if service else 'نامشخص'
                text += f"📌 {service_name}\n   📅 {b['date']}\n   ⏰ {b['time']}\n   🟡 وضعیت: {b['status']}\n\n"
            self.bot.reply(message, text)