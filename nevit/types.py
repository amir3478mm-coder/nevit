from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class ParseMode(str, Enum):
    MARKDOWN = "Markdown"
    MARKDOWN_V2 = "MarkdownV2"
    HTML = "HTML"


class ChatAction(str, Enum):
    TYPING = "typing"
    UPLOAD_PHOTO = "upload_photo"
    UPLOAD_VIDEO = "upload_video"
    UPLOAD_VOICE = "upload_voice"
    UPLOAD_DOCUMENT = "upload_document"


class DiceEmoji(str, Enum):
    DICE = "🎲"
    DART = "🎯"
    BASKETBALL = "🏀"
    FOOTBALL = "⚽"
    SLOT_MACHINE = "🎰"
    BOWLING = "🎳"


@dataclass
class User:
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False

    def __str__(self) -> str:
        if self.username:
            return f"@{self.username}"
        return self.first_name or str(self.id)

    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.first_name}, username={self.username})"


@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    _bot: Optional[Any] = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"Chat(id={self.id}, type={self.type}, title={self.title}, username={self.username})"

    def set_bot(self, bot: Any) -> 'Chat':
        self._bot = bot
        return self

    def send_message(self, text: str, **kwargs) -> Optional[Dict]:
        if self._bot:
            return self._bot.send_message(self.id, text, **kwargs)
        return None

    def send_photo(self, photo: str, **kwargs) -> Optional[Dict]:
        if self._bot:
            return self._bot.send_photo(self.id, photo, **kwargs)
        return None

    def get_member(self, user_id: int) -> Optional[Dict]:
        if self._bot:
            return self._bot.get_chat_member(self.id, user_id)
        return None

    def ban_member(self, user_id: int) -> Optional[Dict]:
        if self._bot:
            return self._bot.kick_chat_member(self.id, user_id)
        return None

    def unban_member(self, user_id: int) -> Optional[Dict]:
        if self._bot:
            return self._bot.unban_chat_member(self.id, user_id)
        return None

    def leave(self) -> Optional[Dict]:
        if self._bot:
            return self._bot.leave_chat(self.id)
        return None


@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    _extra_data: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        if name in self._extra_data:
            return self._extra_data.get(name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ['message_id', 'date', 'chat', 'from_user', 'text', 'caption', '_extra_data']:
            super().__setattr__(name, value)
        else:
            self._extra_data[name] = value

    def __repr__(self) -> str:
        text_preview = (self.text[:30] + "...") if self.text and len(self.text) > 30 else self.text
        return f"Message(id={self.message_id}, chat_id={self.chat.id}, text={text_preview})"

    @property
    def media_group_id(self) -> Optional[str]:
        return self._extra_data.get("media_group_id")

    @property
    def is_media_group(self) -> bool:
        return self.media_group_id is not None

    @property
    def sticker(self) -> Optional[Dict]:
        return self._extra_data.get("sticker")

    @property
    def has_sticker(self) -> bool:
        return self.sticker is not None