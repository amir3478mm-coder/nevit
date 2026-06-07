import asyncio
import time
import logging
import os
import json
import inspect
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
from .smart_backup import SmartBackup
from .errors import NevitError, TokenInvalidError, ChatNotFoundError

logger = logging.getLogger(__name__)


class NevitBot:
    """Sync bot class for Bale messenger."""

    def __init__(self, token: str):
        """
        Initialize the bot.

        Args:
            token: Bot token from BotFather

        Raises:
            TokenInvalidError: If token is invalid
        """
        self.token = token
        self.client = NevitClient(token)
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
        self.db = Database()
        self.scheduler = Scheduler(self)
        self.auto_replies = {}
        self._rate_limit_max = 10
        self._rate_limit_window = 60
        self._command_descriptions = {}
        self._command_has_args = {}
        self._edited_handlers: List[tuple] = []
        self._stop_dispatching = False
        self._log_file = None
        self._log_level = logging.INFO
        self._languages = {}
        self.join_request_handler = ChatJoinRequestHandler(self)
        self.processors = []
        self.watch_processor = None
        self.backup_manager = None
        self.auto_backup_job = None
        self.smart_backup = SmartBackup(self, self.db)

        me = self.client.get_me()
        if me.get("ok"):
            self._bot_info = me["result"]
            logger.info(f"Bot connected: {self._bot_info['first_name']} (ID: {self._bot_info['id']})")
        else:
            raise TokenInvalidError("Invalid bot token")

    @property
    def bot_info(self) -> dict:
        """Get bot information."""
        return self._bot_info

    def add_processor(self, processor) -> Any:
        """Add a processor to the bot."""
        self.processors.append(processor)
        return processor

    def set_watch_processor(self, processor) -> None:
        """Set watch processor for monitoring."""
        self.watch_processor = processor

    async def _run_processors(self, update_type: str, data: dict) -> None:
        """Run all processors on update."""
        for processor in self.processors:
            if hasattr(processor, "process"):
                if asyncio.iscoroutinefunction(processor.process):
                    await processor.process(update_type, data)
                else:
                    processor.process(update_type, data)
        if self.watch_processor:
            if hasattr(self.watch_processor, "process"):
                if asyncio.iscoroutinefunction(self.watch_processor.process):
                    await self.watch_processor.process(update_type, data)
                else:
                    self.watch_processor.process(update_type, data)

    def command(self, commands: List[str], description: str = None):
        """Decorator to register command handlers."""
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
                if description:
                    self._command_descriptions[cmd] = description
            return func
        return decorator

    def smart_command(self, commands: List[str], description: str = None):
        """Decorator to register command handlers with argument parsing."""
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
                if description:
                    self._command_descriptions[cmd] = description
                self._command_has_args[cmd] = True
            return func
        return decorator

    def build_commands_menu(self) -> str:
        """Generate help menu from registered commands."""
        if not self._command_descriptions:
            return "📭 No commands registered."

        menu = "📋 Command list:\n\n"
        for cmd, desc in self._command_descriptions.items():
            menu += f"🔹 `/{cmd}`\n   _{desc}_\n\n"
        return menu

    def message(self, filters=None):
        """Decorator to register message handlers."""
        def decorator(func: Callable):
            self.messages.append((filters, func))
            return func
        return decorator

    def callback(self, pattern: str = None):
        """Decorator to register callback handlers."""
        def decorator(func: Callable):
            if pattern:
                self.callbacks[pattern] = func
            else:
                self.default_callback_handler = func
            return func
        return decorator

    def on(self, event: str = "message"):
        """Decorator to register event handlers."""
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

    def on_edit(self, filters=None):
        """Decorator to register edited message handlers."""
        def decorator(func: Callable):
            self._edited_handlers.append((filters, func))
            return func
        return decorator

    def chat_join_request(self):
        """Decorator to register chat join request handlers."""
        def decorator(func: Callable):
            self.join_request_handler.register(func)
            return func
        return decorator

    def add_middleware(self, middleware) -> None:
        """Add middleware to the bot."""
        self.middleware_manager.add(middleware)

    def set_state(self, user_id: int, state: str, data: dict = None) -> None:
        """Set user state."""
        self.user_state.set(user_id, "state", state)
        if data:
            self.user_state.set(user_id, "data", data)

    def get_state(self, user_id: int) -> Optional[str]:
        """Get user state."""
        return self.user_state.get(user_id, "state")

    def get_state_data(self, user_id: int) -> dict:
        """Get user state data."""
        return self.user_state.get(user_id, "data") or {}

    def clear_state(self, user_id: int) -> None:
        """Clear user state."""
        self.user_state.delete(user_id)

    def set_auto_reply(self, keyword: str, reply: str) -> None:
        """Set auto reply for keyword."""
        self.auto_replies[keyword.lower()] = reply

    def remove_auto_reply(self, keyword: str) -> None:
        """Remove auto reply for keyword."""
        if keyword.lower() in self.auto_replies:
            del self.auto_replies[keyword.lower()]

    def set_rate_limit(self, max_requests: int, per_seconds: int = 60) -> None:
        """Set rate limit for users."""
        self._rate_limit_max = max_requests
        self._rate_limit_window = per_seconds

    def generate_help(self) -> str:
        """Generate help menu."""
        return self.build_commands_menu()

    def reply(self, message: Message, text: str, **kwargs) -> dict:
        """Reply to a message."""
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def send_message(self, chat_id: Union[int, str], text: str, **kwargs) -> dict:
        """Send a text message."""
        return self.client.send_message(chat_id, text, **kwargs)

    def send_photo(self, chat_id: Union[int, str], photo: str, **kwargs) -> dict:
        """Send a photo."""
        return self.client.send_photo(chat_id, photo, **kwargs)

    def send_video(self, chat_id: Union[int, str], video: str, **kwargs) -> dict:
        """Send a video."""
        return self.client.send_video(chat_id, video, **kwargs)

    def send_animation(self, chat_id: Union[int, str], animation: str, **kwargs) -> dict:
        """Send an animation/GIF."""
        return self.client.send_animation(chat_id, animation, **kwargs)

    def send_audio(self, chat_id: Union[int, str], audio: str, **kwargs) -> dict:
        """Send an audio file."""
        return self.client.send_audio(chat_id, audio, **kwargs)

    def send_document(self, chat_id: Union[int, str], document: str, **kwargs) -> dict:
        """Send a document."""
        return self.client.send_document(chat_id, document, **kwargs)

    def send_sticker(self, chat_id: Union[int, str], sticker: str, **kwargs) -> dict:
        """Send a sticker."""
        return self.client.send_sticker(chat_id, sticker, **kwargs)

    def send_media_group(self, chat_id: Union[int, str], media: List[dict]) -> dict:
        """Send a media group (album)."""
        return self.client.send_media_group(chat_id, media)

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> dict:
        """Delete a message."""
        return self.client.delete_message(chat_id, message_id)

    def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: str, **kwargs) -> dict:
        """Edit message text."""
        return self.client.edit_message_text(chat_id, message_id, text, **kwargs)

    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
        """Answer a callback query."""
        return self.client.answer_callback_query(callback_query_id, text, show_alert)

    def get_chat(self, chat_id: Union[int, str]) -> dict:
        """Get chat information."""
        return self.client.get_chat(chat_id)

    def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Get chat member information."""
        return self.client.get_chat_member(chat_id, user_id)

    def kick_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Kick a member from chat."""
        return self.client.kick_chat_member(chat_id, user_id)

    def unban_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Unban a member from chat."""
        return self.client.unban_chat_member(chat_id, user_id)

    def leave_chat(self, chat_id: Union[int, str]) -> dict:
        """Leave a chat."""
        return self.client.leave_chat(chat_id)

    def pin_chat_message(self, chat_id: Union[int, str], message_id: int, **kwargs) -> dict:
        """Pin a message."""
        return self.client.pin_chat_message(chat_id, message_id, **kwargs)

    def unpin_chat_message(self, chat_id: Union[int, str], message_id: int = None) -> dict:
        """Unpin a message."""
        return self.client.unpin_chat_message(chat_id, message_id)

    def set_chat_title(self, chat_id: Union[int, str], title: str) -> dict:
        """Set chat title."""
        return self.client.set_chat_title(chat_id, title)

    def set_chat_description(self, chat_id: Union[int, str], description: str) -> dict:
        """Set chat description."""
        return self.client.set_chat_description(chat_id, description)

    def export_chat_invite_link(self, chat_id: Union[int, str]) -> dict:
        """Export chat invite link."""
        return self.client.export_chat_invite_link(chat_id)

    def create_chat_invite_link(self, chat_id: Union[int, str], expire_date: int = None,
                                 member_limit: int = None) -> dict:
        """Create chat invite link."""
        return self.client.create_chat_invite_link(chat_id, expire_date, member_limit)

    def revoke_chat_invite_link(self, chat_id: Union[int, str], invite_link: str) -> dict:
        """Revoke chat invite link."""
        return self.client.revoke_chat_invite_link(chat_id, invite_link)

    # ==================== BACKUP METHODS ====================

    def start_auto_backup(self, db_path: str = "nevit_bot.db", interval_hours: int = 24) -> None:
        """Start automatic database backup."""
        self.backup_manager = BackupManager(self)
        self.backup_db_path = db_path

        def take_backup():
            result = self.backup_manager.backup_database(db_path)
            if result:
                logger.info(f"Auto backup done: {result}")
                self.backup_manager.delete_old_backups(30)
            else:
                logger.warning("Auto backup failed")

        if interval_hours == 24:
            self.scheduler.every(1).days().at("00:00")(take_backup)
        else:
            @self.scheduler.every(interval_hours).hours()
            def scheduled_backup():
                take_backup()

        self.start_scheduler()
        logger.info(f"Auto backup started (every {interval_hours} hours)")

    def manual_backup(self) -> Optional[str]:
        """Manually backup database."""
        if self.backup_manager:
            return self.backup_manager.backup_database(self.backup_db_path)
        return None

    def get_backup_list(self) -> List[str]:
        """Get list of backup files."""
        if self.backup_manager:
            return self.backup_manager.list_backups()
        return []

    def restore_from_backup(self, backup_name: str) -> bool:
        """Restore database from backup file."""
        if self.backup_manager:
            backup_path = os.path.join("backups", backup_name)
            return self.backup_manager.restore(backup_path, self.backup_db_path)
        return False

    # ==================== SMART BACKUP METHODS ====================

    def backup_now(self, user_ids: list = None) -> str:
        """Create JSON backup of users."""
        return self.smart_backup.backup_users_to_json(user_ids)

    def get_backup_files(self) -> list:
        """Get list of JSON backup files."""
        return self.smart_backup.get_backup_list()

    def schedule_backup(self, hour: int, minute: int, chat_id: int = None) -> bool:
        """Schedule automatic JSON backup."""
        target_chat = chat_id or self._bot_info.get('id') if self._bot_info else None
        if target_chat:
            return self.smart_backup.add_schedule(hour, minute, target_chat)
        return False

    def remove_backup_schedule(self, chat_id: int = None) -> bool:
        """Remove scheduled backup."""
        target_chat = chat_id or self._bot_info.get('id') if self._bot_info else None
        if target_chat:
            self.smart_backup.remove_schedule(target_chat)
            return True
        return False

    def get_backup_schedule(self, chat_id: int = None) -> Optional[Any]:
        """Get scheduled backup info."""
        target_chat = chat_id or self._bot_info.get('id') if self._bot_info else None
        if target_chat:
            return self.smart_backup.get_schedule(target_chat)
        return None

    def run(self) -> None:
        """Start polling."""
        self._run_polling()

    def stop(self) -> None:
        """Stop the bot."""
        logger.info("Bot stopped")
        exit(0)

    def _run_polling(self) -> None:
        """Internal polling loop."""
        self.client.delete_webhook()
        logger.info("Polling started")

        while True:
            try:
                updates = self.client.get_updates(offset=self.offset, timeout=60)
                if updates.get("ok"):
                    for result in updates.get("result", []):
                        update = result.get("update_id", 0)
                        self._process_update(result)
                        self.offset = update + 1
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(1)

    def _process_update(self, result: dict) -> None:
        """Process incoming update."""
        try:
            if "callback_query" in result:
                asyncio.run(self._run_processors("callback_query", result))
                self._handle_callback(result["callback_query"])
            elif "inline_query" in result and self.inline_handler:
                asyncio.run(self._run_processors("inline_query", result))
                self.inline_handler(result["inline_query"])
            elif "chat_join_request" in result:
                asyncio.run(self._run_processors("chat_join_request", result))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.join_request_handler.process(result))
            elif "edited_message" in result:
                asyncio.run(self._run_processors("edited_message", result))
                msg = self._parse_message(result["edited_message"])
                msg.is_edited = True
                for filter_func, handler in self._edited_handlers:
                    try:
                        if filter_func is None or filter_func(msg):
                            handler(msg)
                            break
                    except Exception as e:
                        logger.error(f"Edited message handler error: {e}")
            elif "message" in result:
                asyncio.run(self._run_processors("message", result))
                msg = self._parse_message(result["message"])
                self._handle_message(msg)
        except Exception as e:
            logger.error(f"Update processing error: {e}")

    def _handle_message(self, message: Message) -> None:
        """Handle incoming message."""
        if self._stop_dispatching:
            self._stop_dispatching = False
            return

        message = asyncio.run(self.middleware_manager.pre_process(message, {}))
        if message is None:
            return

        if message.text:
            for keyword, reply in self.auto_replies.items():
                try:
                    if keyword in message.text.lower():
                        self.reply(message, reply)
                        return
                except Exception:
                    pass

        if message.text and message.text.startswith("/"):
            cmd = message.text[1:].split()[0]
            if cmd in self.commands:
                try:
                    if self._command_has_args.get(cmd, False):
                        parts = message.text.split()
                        args = parts[1:] if len(parts) > 1 else []
                        self.commands[cmd](message, *args)
                    else:
                        self.commands[cmd](message)
                except Exception as e:
                    asyncio.run(self.error_handler.emit(e, {"message": message, "command": cmd}))
                return

        for filter_func, handler in self.messages:
            try:
                if filter_func is None or filter_func(message):
                    handler(message)
                    return
            except Exception as e:
                asyncio.run(self.error_handler.emit(e, {"message": message}))

        if self.default_message_handler:
            try:
                self.default_message_handler(message)
            except Exception as e:
                asyncio.run(self.error_handler.emit(e, {"message": message}))

    def _handle_callback(self, callback_data: dict) -> None:
        """Handle callback query."""
        query_id = callback_data.get("id", "")
        data = callback_data.get("data", "")

        msg_data = callback_data.get("message", {})
        if msg_data:
            chat = Chat(
                id=msg_data.get("chat", {}).get("id", 0),
                type=msg_data.get("chat", {}).get("type", "private"),
                title=msg_data.get("chat", {}).get("title"),
                username=msg_data.get("chat", {}).get("username")
            )
            chat.set_bot(self)

            user = User(
                id=callback_data.get("from", {}).get("id", 0),
                first_name=callback_data.get("from", {}).get("first_name", "")
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
                try:
                    if data.startswith(pattern):
                        handler(message, data)
                        found = True
                        break
                except Exception as e:
                    asyncio.run(self.error_handler.emit(e, {"callback": callback_data}))

            if not found and self.default_callback_handler:
                try:
                    self.default_callback_handler(message, data)
                except Exception as e:
                    asyncio.run(self.error_handler.emit(e, {"callback": callback_data}))

        try:
            self.answer_callback_query(query_id)
        except Exception:
            pass

    def _parse_message(self, data: dict) -> Message:
        """Parse message from API response."""
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
        chat.set_bot(self)

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
                   'forward_date', 'forward_from', 'edit_date', 'animation',
                   'media_group_id']:
            if key in data:
                setattr(message, key, data[key])

        return message


class NevitAsyncBot:
    """Async bot class for Bale messenger."""

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
        self.processors = []
        self.watch_processor = None
        self._command_has_args = {}
        self._edited_handlers: List[tuple] = []
        self._stop_dispatching = False
        self._command_descriptions = {}
        self.backup_manager = None
        self.smart_backup = None

        me = asyncio.run(self.client.get_me())
        if me.get("ok"):
            self._bot_info = me["result"]
            logger.info(f"Async bot connected: {self._bot_info['first_name']}")
        else:
            raise TokenInvalidError("Invalid bot token")

    def init_smart_backup(self, db_instance):
        """Initialize smart backup with database instance."""
        from .smart_backup import SmartBackup
        self.smart_backup = SmartBackup(self, db_instance)

    @property
    def bot_info(self) -> dict:
        return self._bot_info

    def command(self, commands: List[str], description: str = None):
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
                if description:
                    self._command_descriptions[cmd] = description
            return func
        return decorator

    def smart_command(self, commands: List[str], description: str = None):
        def decorator(func: Callable):
            for cmd in commands:
                self.commands[cmd] = func
                if description:
                    self._command_descriptions[cmd] = description
                self._command_has_args[cmd] = True
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
            else:
                self.messages.append((None, func))
            return func
        return decorator

    def on_edit(self, filters=None):
        def decorator(func: Callable):
            self._edited_handlers.append((filters, func))
            return func
        return decorator

    async def run(self):
        """Start async polling."""
        await self.client.delete_webhook()
        logger.info("Async polling started")

        if self.smart_backup:
            self.smart_backup._start_scheduler()

        while True:
            try:
                updates = await self.client.get_updates(offset=self.offset, timeout=60)
                if updates.get("ok"):
                    for result in updates.get("result", []):
                        update = result.get("update_id", 0)
                        await self._process_update(result)
                        self.offset = update + 1
            except Exception as e:
                logger.error(f"Async polling error: {e}")
                await asyncio.sleep(1)

    async def _process_update(self, result: dict):
        try:
            if "callback_query" in result:
                await self._run_processors("callback_query", result)
                await self._handle_callback(result["callback_query"])
            elif "inline_query" in result and self.inline_handler:
                await self._run_processors("inline_query", result)
                await self.inline_handler(result["inline_query"])
            elif "chat_join_request" in result:
                await self._run_processors("chat_join_request", result)
                await self.join_request_handler.process(result)
            elif "edited_message" in result:
                await self._run_processors("edited_message", result)
                msg = self._parse_message(result["edited_message"])
                msg.is_edited = True
                for filter_func, handler in self._edited_handlers:
                    try:
                        if filter_func is None or filter_func(msg):
                            await handler(msg)
                            break
                    except Exception as e:
                        logger.error(f"Edited message error: {e}")
            elif "message" in result:
                await self._run_processors("message", result)
                msg = self._parse_message(result["message"])
                await self._handle_message(msg)
        except Exception as e:
            logger.error(f"Update error: {e}")

    async def _run_processors(self, update_type: str, data: dict):
        for processor in self.processors:
            if hasattr(processor, "process"):
                if asyncio.iscoroutinefunction(processor.process):
                    await processor.process(update_type, data)
                else:
                    processor.process(update_type, data)
        if self.watch_processor:
            if hasattr(self.watch_processor, "process"):
                if asyncio.iscoroutinefunction(self.watch_processor.process):
                    await self.watch_processor.process(update_type, data)
                else:
                    self.watch_processor.process(update_type, data)

    async def _handle_message(self, message: Message):
        if self._stop_dispatching:
            self._stop_dispatching = False
            return

        message = await self.middleware_manager.pre_process(message, {})
        if message is None:
            return

        if message.text and message.text.startswith("/"):
            cmd = message.text[1:].split()[0]
            if cmd in self.commands:
                try:
                    if self._command_has_args.get(cmd, False):
                        parts = message.text.split()
                        args = parts[1:] if len(parts) > 1 else []
                        await self.commands[cmd](message, *args)
                    else:
                        await self.commands[cmd](message)
                except Exception as e:
                    await self.error_handler.emit(e, {"message": message, "command": cmd})
                return

        for filter_func, handler in self.messages:
            try:
                if filter_func is None or filter_func(message):
                    await handler(message)
                    return
            except Exception as e:
                await self.error_handler.emit(e, {"message": message})

        if self.default_message_handler:
            try:
                await self.default_message_handler(message)
            except Exception as e:
                await self.error_handler.emit(e, {"message": message})

    async def _handle_callback(self, callback_data: dict):
        query_id = callback_data.get("id", "")
        data = callback_data.get("data", "")

        msg_data = callback_data.get("message", {})
        if msg_data:
            chat = Chat(
                id=msg_data.get("chat", {}).get("id", 0),
                type=msg_data.get("chat", {}).get("type", "private"),
                title=msg_data.get("chat", {}).get("title"),
                username=msg_data.get("chat", {}).get("username")
            )
            chat.set_bot(self)

            user = User(
                id=callback_data.get("from", {}).get("id", 0),
                first_name=callback_data.get("from", {}).get("first_name", "")
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
                try:
                    if data.startswith(pattern):
                        await handler(message, data)
                        found = True
                        break
                except Exception as e:
                    await self.error_handler.emit(e, {"callback": callback_data})

            if not found and self.default_callback_handler:
                try:
                    await self.default_callback_handler(message, data)
                except Exception as e:
                    await self.error_handler.emit(e, {"callback": callback_data})

        await self.answer_callback_query(query_id)

    async def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
        return await self.client.answer_callback_query(callback_query_id, text, show_alert)

    async def send_message(self, chat_id: Union[int, str], text: str, **kwargs) -> dict:
        return await self.client.send_message(chat_id, text, **kwargs)

    async def send_photo(self, chat_id: Union[int, str], photo: str, **kwargs) -> dict:
        return await self.client.send_photo(chat_id, photo, **kwargs)

    async def send_video(self, chat_id: Union[int, str], video: str, **kwargs) -> dict:
        return await self.client.send_video(chat_id, video, **kwargs)

    async def send_sticker(self, chat_id: Union[int, str], sticker: str, **kwargs) -> dict:
        return await self.client.send_sticker(chat_id, sticker, **kwargs)

    async def delete_webhook(self) -> dict:
        return await self.client.delete_webhook()

    async def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 60) -> dict:
        return await self.client.get_updates(offset, limit, timeout)

    # Async backup methods
    async def backup_now(self, user_ids: list = None) -> str:
        if self.smart_backup:
            return self.smart_backup.backup_users_to_json(user_ids)
        return None

    async def get_backup_files(self) -> list:
        if self.smart_backup:
            return self.smart_backup.get_backup_list()
        return []

    async def schedule_backup(self, hour: int, minute: int, chat_id: int = None):
        if self.smart_backup:
            target_chat = chat_id or self._bot_info.get('id') if self._bot_info else None
            if target_chat:
                return self.smart_backup.add_schedule(hour, minute, target_chat)
        return False

    async def stop(self):
        logger.info("Async bot stopped")

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
        chat.set_bot(self)

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
                   'forward_date', 'forward_from', 'edit_date', 'animation',
                   'media_group_id']:
            if key in data:
                setattr(message, key, data[key])

        return message


class Processor:
    """Base class for processors."""

    def __init__(self, **params):
        self.params = params

    def process(self, update_type: str, data: dict) -> dict:
        """Process update."""
        return data


class WatchProcessor(Processor):
    """Processor for monitoring updates."""

    async def process(self, update_type: str, data: dict) -> dict:
        if update_type == "message":
            msg = data.get("message", {})
            text = msg.get("text", "")
            if text:
                print(f"[WATCH] New message: {text[:50]}")
        elif update_type == "callback_query":
            print(f"[WATCH] Button pressed: {data.get('callback_query', {}).get('data', '')[:50]}")
        return data