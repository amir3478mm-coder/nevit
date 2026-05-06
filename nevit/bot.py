import asyncio
import time
import logging
import os
import json
from typing import Optional, List, Dict, Union, Callable, Any
from datetime import datetime, timedelta

from .client import NevitClient, NevitAsyncClient
from .types import User, Chat, Message
from .keyboards import Keyboard
from .filters import Filters
from .middleware import MiddlewareManager
from .error_handler import ErrorHandler
from .state import UserState
from .database import Database
from .scheduler import Scheduler
from .chat_join_request import ChatJoinRequestHandler, ChatJoinRequest
from .backup import BackupManager

logger = logging.getLogger("nevit")

class NevitBot:
    def __init__(self, token: str):
        self.token = token
        self.client = NevitClient(token)
        self.offset = 0
        self.commands: Dict[str, Callable] = {}
        self.messages: List[tuple] = []
        self.callbacks: Dict[str, Callable] = {}
        self.default_message_handler: Optional[Callable] = None
        self.default_callback_handler: Optional[Callable] = None
        self.inline_handler: Optional[Callable] = None
        self.callback_query_handler: Optional[Callable] = None
        self.middleware_manager = MiddlewareManager()
        self.error_handler = ErrorHandler()
        self.user_state = UserState()
        self.db = Database()
        self.scheduler = Scheduler(self)
        self.auto_replies = {}
        self._rate_limit_max = 10
        self._rate_limit_window = 60
        self._command_descriptions = {}
        self._log_file = None
        self._log_level = logging.INFO
        self._languages = {}
        self.join_request_handler = ChatJoinRequestHandler(self)
        self.backup_manager = None
        self.auto_backup_job = None
        self._payment_handlers = []
        self._pre_checkout_handlers = []
        
        me = self.client.get_me()
        if me.get("ok"):
            self._bot_info = me["result"]
            logger.info(f"ربات {self._bot_info['first_name']} متصل شد")
        else:
            raise Exception("توکن نامعتبر است")
    
    @property
    def bot_info(self):
        return self._bot_info
    
    def command(self, commands: List[str], description: str = None):
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
                if description:
                    self._command_descriptions[cmd] = description
            return func
        return decorator
    
    def message(self, filters=None):
        def decorator(func: Callable):
            self.messages.append((filters, func))
            return func
        return decorator
    
    def callback(self, pattern: str = None):
        def decorator(func: Callable):
            if pattern:
                self.callbacks[pattern] = func
            else:
                self.default_callback_handler = func
            return func
        return decorator
    
    def on(self, event: str = "message"):
        def decorator(func: Callable):
            if event == "callback":
                self.default_callback_handler = func
            elif event == "successful_payment":
                self._payment_handlers.append(func)
            elif event == "pre_checkout_query":
                self._pre_checkout_handlers.append(func)
            else:
                self.messages.append((None, func))
            return func
        return decorator
    
    def on_successful_payment(self):
        def decorator(func: Callable):
            self._payment_handlers.append(func)
            return func
        return decorator
    
    def on_pre_checkout_query(self):
        def decorator(func: Callable):
            self._pre_checkout_handlers.append(func)
            return func
        return decorator
    
    def listen(self, filter_func=None):
        return self.message(filter_func)
    
    def inline(self, func: Callable):
        self.inline_handler = func
        return func
    
    def message_handler(self, filters=None):
        return self.message(filters)
    
    def error_handler(self, func: Callable = None):
        if func:
            self.error_handler.handlers.append(func)
            return func
        return func
    
    def chat_join_request(self):
        def decorator(func: Callable):
            self.join_request_handler.register(func)
            return func
        return decorator
    
    def approve_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return self.client.approve_chat_join_request(chat_id, user_id)
    
    def decline_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return self.client.decline_chat_join_request(chat_id, user_id)
    
    def add_middleware(self, middleware):
        self.middleware_manager.add(middleware)
    
    def keyboard(self, buttons: List[List[Union[str, tuple]]]) -> dict:
        return Keyboard.inline(buttons)
    
    def reply_keyboard(self, buttons: List[List[str]], resize: bool = True) -> dict:
        return Keyboard.reply(buttons, resize)
    
    def remove_keyboard(self) -> dict:
        return Keyboard.remove()
    
    def set_state(self, user_id: int, state: str, data: dict = None):
        self.user_state.set(user_id, "state", state)
        if data:
            self.user_state.set(user_id, "data", data)
    
    def get_state(self, user_id: int) -> Optional[str]:
        return self.user_state.get(user_id, "state")
    
    def get_state_data(self, user_id: int) -> dict:
        return self.user_state.get(user_id, "data") or {}
    
    def clear_state(self, user_id: int):
        self.user_state.delete(user_id)
    
    def set_auto_reply(self, keyword: str, reply: str):
        self.auto_replies[keyword.lower()] = reply
    
    def remove_auto_reply(self, keyword: str):
        if keyword.lower() in self.auto_replies:
            del self.auto_replies[keyword.lower()]
    
    def set_rate_limit(self, max_requests: int, per_seconds: int = 60):
        self._rate_limit_max = max_requests
        self._rate_limit_window = per_seconds
    
    def generate_help(self) -> str:
        help_text = "دستورات موجود:\n"
        for cmd, desc in self._command_descriptions.items():
            help_text += f"/{cmd} - {desc}\n"
        return help_text
    
    def enable_file_logging(self, log_file: str, level: int = logging.DEBUG):
        self._log_file = log_file
        self._log_level = level
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    def set_language(self, user_id: int, lang: str):
        self.user_state.set(user_id, "language", lang)
    
    def get_language(self, user_id: int) -> str:
        return self.user_state.get(user_id, "language") or "fa"
    
    def translate(self, user_id: int, key: str) -> str:
        translations = {
            "fa": {"welcome": "خوش آمدید", "help": "راهنما"},
            "en": {"welcome": "Welcome", "help": "Help"}
        }
        lang = self.get_language(user_id)
        return translations.get(lang, {}).get(key, key)
    
    def backup_data(self, backup_path: str):
        import shutil
        if os.path.exists(self.db.db_path):
            shutil.copy(self.db.db_path, backup_path)
            logger.info(f"backup saved to {backup_path}")
    
    def restore_data(self, backup_path: str):
        import shutil
        if os.path.exists(backup_path):
            shutil.copy(backup_path, self.db.db_path)
            logger.info(f"restored from {backup_path}")
    
    def start_scheduler(self):
        self.scheduler.start()
    
    def start_auto_backup(self, db_path: str = "nevit_bot.db", interval_hours: int = 24):
        self.backup_manager = BackupManager(self)
        self.backup_db_path = db_path
        
        def take_backup():
            result = self.backup_manager.backup_database(db_path)
            if result:
                logger.info(f"auto backup done: {result}")
                self.backup_manager.delete_old_backups(30)
            else:
                logger.warning("auto backup failed")
        
        if interval_hours == 24:
            self.scheduler.every(1).days().at("00:00")(take_backup)
        else:
            @self.scheduler.every(interval_hours).hours()
            def scheduled_backup():
                take_backup()
        
        self.start_scheduler()
        logger.info(f"auto backup started (every {interval_hours} hours)")
    
    def manual_backup(self) -> str:
        if self.backup_manager:
            return self.backup_manager.backup_database(self.backup_db_path)
        return None
    
    def get_backup_list(self) -> List[str]:
        if self.backup_manager:
            return self.backup_manager.list_backups()
        return []
    
    def restore_from_backup(self, backup_name: str) -> bool:
        if self.backup_manager:
            backup_path = os.path.join("backups", backup_name)
            return self.backup_manager.restore(backup_path, self.backup_db_path)
        return False
    
    def reply(self, message: Message, text: str, **kwargs) -> dict:
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)
    
    def send_message(self, chat_id: int, text: str, **kwargs) -> dict:
        return self.client.send_message(chat_id, text, **kwargs)
    
    def send_photo(self, chat_id: int, photo: str, **kwargs) -> dict:
        return self.client.send_photo(chat_id, photo, **kwargs)
    
    def send_video(self, chat_id: int, video: str, **kwargs) -> dict:
        return self.client.send_video(chat_id, video, **kwargs)
    
    def send_animation(self, chat_id: int, animation: str, **kwargs) -> dict:
        return self.client.send_animation(chat_id, animation, **kwargs)
    
    def send_media_group(self, chat_id: int, media: List[dict]) -> dict:
        return self.client.send_media_group(chat_id, media)
    
    def send_audio(self, chat_id: int, audio: str, **kwargs) -> dict:
        return self.client.send_audio(chat_id, audio, **kwargs)
    
    def send_document(self, chat_id: int, document: str, **kwargs) -> dict:
        return self.client.send_document(chat_id, document, **kwargs)
    
    def send_sticker(self, chat_id: int, sticker: str, **kwargs) -> dict:
        return self.client.send_sticker(chat_id, sticker, **kwargs)
    
    def send_location(self, chat_id: int, latitude: float, longitude: float, **kwargs) -> dict:
        return self.client.send_location(chat_id, latitude, longitude, **kwargs)
    
    def send_contact(self, chat_id: int, phone_number: str, first_name: str, **kwargs) -> dict:
        return self.client.send_contact(chat_id, phone_number, first_name, **kwargs)
    
    def send_poll(self, chat_id: int, question: str, options: List[str], **kwargs) -> dict:
        return self.client.send_poll(chat_id, question, options, **kwargs)
    
    def send_dice(self, chat_id: int, emoji: str = None, **kwargs) -> dict:
        return self.client.send_dice(chat_id, emoji, **kwargs)
    
    def send_invoice(self, chat_id: int, title: str, description: str, payload: str, provider_token: str, currency: str, prices: List[dict], **kwargs) -> dict:
        return self.client.send_invoice(chat_id, title, description, payload, provider_token, currency, prices, **kwargs)
    
    def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool, error_message: str = None) -> dict:
        return self.client.answer_pre_checkout_query(pre_checkout_query_id, ok, error_message)
    
    def forward_message(self, chat_id: int, from_chat_id: int, message_id: int) -> dict:
        return self.client.forward_message(chat_id, from_chat_id, message_id)
    
    def copy_message(self, chat_id: int, from_chat_id: int, message_id: int, **kwargs) -> dict:
        return self.client.copy_message(chat_id, from_chat_id, message_id, **kwargs)
    
    def delete_message(self, chat_id: int, message_id: int) -> dict:
        return self.client.delete_message(chat_id, message_id)
    
    def edit_message_text(self, chat_id: int, message_id: int, text: str, **kwargs) -> dict:
        return self.client.edit_message_text(chat_id, message_id, text, **kwargs)
    
    def edit_message_reply_markup(self, chat_id: int, message_id: int, **kwargs) -> dict:
        return self.client.edit_message_reply_markup(chat_id, message_id, **kwargs)
    
    def answer_callback(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
        return self.client.answer_callback_query(callback_query_id, text, show_alert)
    
    def send_action(self, chat_id: int, action: str) -> dict:
        return self.client.send_chat_action(chat_id, action)
    
    def get_chat(self, chat_id: int) -> dict:
        return self.client.get_chat(chat_id)
    
    def get_chat_administrators(self, chat_id: int) -> dict:
        return self.client.get_chat_administrators(chat_id)
    
    def get_chat_member(self, chat_id: int, user_id: int) -> dict:
        return self.client.get_chat_member(chat_id, user_id)
    
    def get_chat_members_count(self, chat_id: int) -> dict:
        return self.client.get_chat_members_count(chat_id)
    
    def kick_member(self, chat_id: int, user_id: int) -> dict:
        return self.client.kick_chat_member(chat_id, user_id)
    
    def unban_member(self, chat_id: int, user_id: int) -> dict:
        return self.client.unban_chat_member(chat_id, user_id)
    
    def leave_chat(self, chat_id: int) -> dict:
        return self.client.leave_chat(chat_id)
    
    def pin_message(self, chat_id: int, message_id: int, **kwargs) -> dict:
        return self.client.pin_chat_message(chat_id, message_id, **kwargs)
    
    def unpin_message(self, chat_id: int, message_id: int = None) -> dict:
        return self.client.unpin_chat_message(chat_id, message_id)
    
    def _run_polling(self):
        logger.info("bot started with polling mode")
        
        while True:
            try:
                updates = self.client.get_updates(offset=self.offset, timeout=60)
                if updates.get("ok"):
                    for result in updates.get("result", []):
                        update = result.get("update_id", 0)
                        
                        if "callback_query" in result:
                            try:
                                self._handle_callback(result["callback_query"])
                            except Exception as error:
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.error_handler.emit(error, {"update": result}))
                                except:
                                    pass
                            self.offset = update + 1
                            continue
                        
                        if "inline_query" in result:
                            if self.inline_handler:
                                try:
                                    self.inline_handler(result["inline_query"])
                                except Exception as error:
                                    try:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        loop.run_until_complete(self.error_handler.emit(error, {"update": result}))
                                    except:
                                        pass
                            self.offset = update + 1
                            continue
                        
                        if "chat_join_request" in result:
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(self.join_request_handler.process(result))
                            except Exception as error:
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.error_handler.emit(error, {"update": result}))
                                except:
                                    pass
                            self.offset = update + 1
                            continue
                        
                        if "pre_checkout_query" in result:
                            try:
                                self._handle_pre_checkout(result["pre_checkout_query"])
                            except Exception as error:
                                logger.error(f"pre_checkout error: {error}")
                            self.offset = update + 1
                            continue
                        
                        if "message" in result:
                            try:
                                if result["message"].get("successful_payment"):
                                    self._handle_successful_payment(result["message"])
                                else:
                                    msg = self._parse_message(result["message"])
                                    self._handle_message(msg)
                            except Exception as error:
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.error_handler.emit(error, {"update": result}))
                                except:
                                    pass
                            self.offset = update + 1
                            continue
            except Exception as error:
                logger.error(f"polling error: {error}")
                time.sleep(1)
    
    def _handle_pre_checkout(self, pre_checkout_query):
        query_id = pre_checkout_query.get("id")
        ok = True
        error_message = None
        
        for handler in self._pre_checkout_handlers:
            try:
                result = handler(pre_checkout_query)
                if result is False:
                    ok = False
                    error_message = "پرداخت امکان پذیر نیست"
                    break
            except Exception as error:
                logger.error(f"pre_checkout handler error: {error}")
                ok = False
                error_message = "خطا در پردازش"
                break
        
        self.answer_pre_checkout_query(query_id, ok, error_message)
    
    def _handle_successful_payment(self, message_data):
        try:
            msg = self._parse_message(message_data)
            for handler in self._payment_handlers:
                try:
                    handler(msg)
                except Exception as error:
                    logger.error(f"payment handler error: {error}")
        except Exception as error:
            logger.error(f"successful payment error: {error}")
    
    def _handle_message(self, message: Message):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            message = loop.run_until_complete(self.middleware_manager.pre_process(message, {}))
        except:
            pass
        
        if message is None:
            return
        
        if message.text:
            for keyword, reply in self.auto_replies.items():
                if keyword in message.text.lower():
                    try:
                        self.reply(message, reply)
                    except:
                        pass
                    return
        
        if message.text and message.text.startswith("/"):
            cmd = message.text[1:].split()[0]
            if cmd in self.commands:
                try:
                    self.commands[cmd](message)
                except Exception as error:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.error_handler.emit(error, {"message": message, "command": cmd}))
                    except:
                        pass
                return
        
        for filter_func, handler in self.messages:
            try:
                if filter_func is None or filter_func(message):
                    handler(message)
                    return
            except Exception as error:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.error_handler.emit(error, {"message": message}))
                except:
                    pass
        
        if self.default_message_handler:
            self.default_message_handler(message)
    
    def _handle_callback(self, callback_data: dict):
        query_id = callback_data.get("id", "")
        data = callback_data.get("data", "")
        
        msg_data = callback_data.get("message", {})
        if msg_data:
            chat_data = msg_data.get("chat", {})
            user_data = callback_data.get("from", {})
            chat = Chat(
                id=chat_data.get("id", 0),
                type=chat_data.get("type", "private"),
                title=chat_data.get("title"),
                username=chat_data.get("username")
            )
            user = User(
                id=user_data.get("id", 0),
                first_name=user_data.get("first_name", ""),
                username=user_data.get("username")
            )
            message = Message(
                message_id=msg_data.get("message_id", 0),
                date=msg_data.get("date", 0),
                chat=chat,
                from_user=user,
                text=msg_data.get("text")
            )
            message.callback_query = callback_data
            
            found = False
            for pattern, handler in self.callbacks.items():
                if pattern == data:
                    try:
                        handler(message, data)
                    except Exception as error:
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.error_handler.emit(error, {"callback": callback_data}))
                        except:
                            pass
                    found = True
                    break
            
            if not found and self.default_callback_handler:
                try:
                    self.default_callback_handler(message, data)
                except Exception as error:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.error_handler.emit(error, {"callback": callback_data}))
                    except:
                        pass
        
        try:
            self.client.answer_callback_query(query_id)
        except:
            pass
    
    def _parse_message(self, data: dict) -> Message:
        user_data = data.get("from", {})
        user = None
        if user_data:
            user = User(
                id=user_data.get("id", 0),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name"),
                username=user_data.get("username"),
                language_code=user_data.get("language_code"),
                is_bot=user_data.get("is_bot", False)
            )
        
        chat_data = data.get("chat", {})
        chat = Chat(
            id=chat_data.get("id", 0),
            type=chat_data.get("type", "private"),
            title=chat_data.get("title"),
            username=chat_data.get("username"),
            first_name=chat_data.get("first_name"),
            last_name=chat_data.get("last_name")
        )
        
        message = Message(
            message_id=data.get("message_id", 0),
            date=data.get("date", 0),
            chat=chat,
            from_user=user,
            text=data.get("text"),
            caption=data.get("caption")
        )
        
        if data.get("successful_payment"):
            message.successful_payment = data.get("successful_payment")
        
        for key in ['photo', 'video', 'audio', 'voice', 'document', 'sticker',
                   'location', 'venue', 'contact', 'poll', 'dice', 'game',
                   'invoice', 'new_chat_members', 'left_chat_member',
                   'forward_date', 'forward_from', 'edit_date', 'animation']:
            if key in data:
                setattr(message, key, data[key])
        
        return message
    
    def run(self):
        self._run_polling()
    
    def stop(self):
        logger.info("bot stopped")
        exit(0)


class NevitAsyncBot:
    def __init__(self, token: str):
        self.token = token
        self.client = NevitAsyncClient(token)
        self.offset = 0
        self.commands: Dict[str, Callable] = {}
        self.messages: List[tuple] = []
        self.callbacks: Dict[str, Callable] = {}
        self.default_message_handler: Optional[Callable] = None
        self.default_callback_handler: Optional[Callable] = None
        self.inline_handler: Optional[Callable] = None
        self.middleware_manager = MiddlewareManager()
        self.error_handler = ErrorHandler()
        self.user_state = UserState()
        self.join_request_handler = ChatJoinRequestHandler(self)
        self.backup_manager = None
        self._payment_handlers = []
        self._pre_checkout_handlers = []
        
        loop = asyncio.get_event_loop()
        me = loop.run_until_complete(self.client.get_me())
        if me.get("ok"):
            self._bot_info = me["result"]
            logger.info(f"async bot {self._bot_info['first_name']} connected")
        else:
            raise Exception("invalid token")
    
    @property
    def bot_info(self):
        return self._bot_info
    
    def command(self, commands: List[str]):
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
            return func
        return decorator
    
    def message(self, filters=None):
        def decorator(func: Callable):
            self.messages.append((filters, func))
            return func
        return decorator
    
    def callback(self, pattern: str = None):
        def decorator(func: Callable):
            if pattern:
                self.callbacks[pattern] = func
            else:
                self.default_callback_handler = func
            return func
        return decorator
    
    def on(self, event: str = "message"):
        def decorator(func: Callable):
            if event == "callback":
                self.default_callback_handler = func
            elif event == "successful_payment":
                self._payment_handlers.append(func)
            elif event == "pre_checkout_query":
                self._pre_checkout_handlers.append(func)
            else:
                self.messages.append((None, func))
            return func
        return decorator
    
    def on_successful_payment(self):
        def decorator(func: Callable):
            self._payment_handlers.append(func)
            return func
        return decorator
    
    def on_pre_checkout_query(self):
        def decorator(func: Callable):
            self._pre_checkout_handlers.append(func)
            return func
        return decorator
    
    def listen(self, filter_func=None):
        return self.message(filter_func)
    
    def inline(self, func: Callable):
        self.inline_handler = func
        return func
    
    def error_handler(self, func: Callable = None):
        if func:
            self.error_handler.handlers.append(func)
            return func
        return func
    
    def chat_join_request(self):
        def decorator(func: Callable):
            self.join_request_handler.register(func)
            return func
        return decorator
    
    async def approve_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return await self.client.approve_chat_join_request(chat_id, user_id)
    
    async def decline_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return await self.client.decline_chat_join_request(chat_id, user_id)
    
    def add_middleware(self, middleware):
        self.middleware_manager.add(middleware)
    
    def keyboard(self, buttons: List[List[Union[str, tuple]]]) -> dict:
        return Keyboard.inline(buttons)
    
    def set_state(self, user_id: int, state: str, data: dict = None):
        self.user_state.set(user_id, "state", state)
        if data:
            self.user_state.set(user_id, "data", data)
    
    def get_state(self, user_id: int) -> Optional[str]:
        return self.user_state.get(user_id, "state")
    
    def get_state_data(self, user_id: int) -> dict:
        return self.user_state.get(user_id, "data") or {}
    
    def clear_state(self, user_id: int):
        self.user_state.delete(user_id)
    
    def start_auto_backup(self, db_path: str = "nevit_bot.db", interval_hours: int = 24):
        self.backup_manager = BackupManager(self)
        self.backup_db_path = db_path
        
        async def take_backup():
            result = self.backup_manager.backup_database(db_path)
            if result:
                logger.info(f"auto backup done: {result}")
                self.backup_manager.delete_old_backups(30)
            else:
                logger.warning("auto backup failed")
        
        async def backup_wrapper():
            await take_backup()
        
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
        
        if interval_hours == 24:
            self.scheduler.add_job(backup_wrapper, CronTrigger(hour=0, minute=0))
        else:
            self.scheduler.add_job(backup_wrapper, IntervalTrigger(hours=interval_hours))
        
        logger.info(f"auto backup started (every {interval_hours} hours)")
    
    async def reply(self, message: Message, text: str, **kwargs) -> dict:
        return await self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)
    
    async def send_message(self, chat_id: int, text: str, **kwargs) -> dict:
        return await self.client.send_message(chat_id, text, **kwargs)
    
    async def send_photo(self, chat_id: int, photo: str, **kwargs) -> dict:
        return await self.client.send_photo(chat_id, photo, **kwargs)
    
    async def send_video(self, chat_id: int, video: str, **kwargs) -> dict:
        return await self.client.send_video(chat_id, video, **kwargs)
    
    async def send_animation(self, chat_id: int, animation: str, **kwargs) -> dict:
        return await self.client.send_animation(chat_id, animation, **kwargs)
    
    async def send_media_group(self, chat_id: int, media: List[dict]) -> dict:
        return await self.client.send_media_group(chat_id, media)
    
    async def answer_callback(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
        return await self.client.answer_callback_query(callback_query_id, text, show_alert)
    
    async def run(self):
        logger.info("async bot started")
        
        while True:
            try:
                updates = await self.client.get_updates(offset=self.offset, timeout=60)
                if updates.get("ok"):
                    for result in updates.get("result", []):
                        update = result.get("update_id", 0)
                        
                        if "callback_query" in result:
                            try:
                                await self._handle_callback(result["callback_query"])
                            except Exception as error:
                                await self.error_handler.emit(error, {"update": result})
                            self.offset = update + 1
                            continue
                        
                        if "inline_query" in result:
                            if self.inline_handler:
                                try:
                                    await self.inline_handler(result["inline_query"])
                                except Exception as error:
                                    await self.error_handler.emit(error, {"update": result})
                            self.offset = update + 1
                            continue
                        
                        if "chat_join_request" in result:
                            try:
                                await self.join_request_handler.process(result)
                            except Exception as error:
                                await self.error_handler.emit(error, {"update": result})
                            self.offset = update + 1
                            continue
                        
                        if "pre_checkout_query" in result:
                            try:
                                await self._handle_pre_checkout(result["pre_checkout_query"])
                            except Exception as error:
                                logger.error(f"pre_checkout error: {error}")
                            self.offset = update + 1
                            continue
                        
                        if "message" in result:
                            try:
                                if result["message"].get("successful_payment"):
                                    await self._handle_successful_payment(result["message"])
                                else:
                                    msg = self._parse_message(result["message"])
                                    await self._handle_message(msg)
                            except Exception as error:
                                await self.error_handler.emit(error, {"update": result})
                            self.offset = update + 1
                            continue
            except Exception as error:
                logger.error(f"async error: {error}")
                await asyncio.sleep(1)
    
    async def _handle_pre_checkout(self, pre_checkout_query):
        query_id = pre_checkout_query.get("id")
        ok = True
        error_message = None
        
        for handler in self._pre_checkout_handlers:
            try:
                result = handler(pre_checkout_query)
                if result is False:
                    ok = False
                    error_message = "پرداخت امکان پذیر نیست"
                    break
            except Exception as error:
                logger.error(f"pre_checkout handler error: {error}")
                ok = False
                error_message = "خطا در پردازش"
                break
        
        await self.client.answer_pre_checkout_query(query_id, ok, error_message)
    
    async def _handle_successful_payment(self, message_data):
        try:
            msg = self._parse_message(message_data)
            for handler in self._payment_handlers:
                try:
                    await handler(msg)
                except Exception as error:
                    logger.error(f"payment handler error: {error}")
        except Exception as error:
            logger.error(f"successful payment error: {error}")
    
    async def _handle_message(self, message: Message):
        message = await self.middleware_manager.pre_process(message, {})
        if message is None:
            return
        
        if message.text and message.text.startswith("/"):
            cmd = message.text[1:].split()[0]
            if cmd in self.commands:
                try:
                    await self.commands[cmd](message)
                except Exception as error:
                    await self.error_handler.emit(error, {"message": message, "command": cmd})
                return
        
        for filter_func, handler in self.messages:
            try:
                if filter_func is None or filter_func(message):
                    await handler(message)
                    return
            except Exception as error:
                await self.error_handler.emit(error, {"message": message})
        
        if self.default_message_handler:
            await self.default_message_handler(message)
    
    async def _handle_callback(self, callback_data: dict):
        query_id = callback_data.get("id", "")
        data = callback_data.get("data", "")
        
        msg_data = callback_data.get("message", {})
        if msg_data:
            chat_data = msg_data.get("chat", {})
            user_data = callback_data.get("from", {})
            chat = Chat(
                id=chat_data.get("id", 0),
                type=chat_data.get("type", "private"),
                title=chat_data.get("title"),
                username=chat_data.get("username")
            )
            user = User(
                id=user_data.get("id", 0),
                first_name=user_data.get("first_name", ""),
                username=user_data.get("username")
            )
            message = Message(
                message_id=msg_data.get("message_id", 0),
                date=msg_data.get("date", 0),
                chat=chat,
                from_user=user,
                text=msg_data.get("text")
            )
            message.callback_query = callback_data
            
            found = False
            for pattern, handler in self.callbacks.items():
                if pattern == data:
                    try:
                        await handler(message, data)
                    except Exception as error:
                        await self.error_handler.emit(error, {"callback": callback_data})
                    found = True
                    break
            
            if not found and self.default_callback_handler:
                try:
                    await self.default_callback_handler(message, data)
                except Exception as error:
                    await self.error_handler.emit(error, {"callback": callback_data})
        
        await self.client.answer_callback_query(query_id)
    
    def _parse_message(self, data: dict) -> Message:
        user_data = data.get("from", {})
        user = None
        if user_data:
            user = User(
                id=user_data.get("id", 0),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name"),
                username=user_data.get("username"),
                language_code=user_data.get("language_code"),
                is_bot=user_data.get("is_bot", False)
            )
        
        chat_data = data.get("chat", {})
        chat = Chat(
            id=chat_data.get("id", 0),
            type=chat_data.get("type", "private"),
            title=chat_data.get("title"),
            username=chat_data.get("username"),
            first_name=chat_data.get("first_name"),
            last_name=chat_data.get("last_name")
        )
        
        message = Message(
            message_id=data.get("message_id", 0),
            date=data.get("date", 0),
            chat=chat,
            from_user=user,
            text=data.get("text"),
            caption=data.get("caption")
        )
        
        if data.get("successful_payment"):
            message.successful_payment = data.get("successful_payment")
        
        for key in ['photo', 'video', 'audio', 'voice', 'document', 'sticker',
                   'location', 'venue', 'contact', 'poll', 'dice', 'game',
                   'invoice', 'new_chat_members', 'left_chat_member',
                   'forward_date', 'forward_from', 'edit_date', 'animation']:
            if key in data:
                setattr(message, key, data[key])
        
        return message
    
    async def stop(self):
        logger.info("async bot stopped")