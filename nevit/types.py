from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class ChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"

class ParseMode(Enum):
    MARKDOWN = "Markdown"
    MARKDOWN_V2 = "MarkdownV2"
    HTML = "HTML"

class ChatAction(Enum):
    TYPING = "typing"
    UPHOTO = "upload_photo"
    UVIDEO = "upload_video"
    UVOICE = "upload_voice"
    UDOCUMENT = "upload_document"

class DiceEmoji(Enum):
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

@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    _extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def __getattr__(self, name: str):
        if name in self._extra_data:
            return self._extra_data.get(name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        if name in ['message_id', 'date', 'chat', 'from_user', 'text', 'caption', '_extra_data']:
            super().__setattr__(name, value)
        else:
            self._extra_data[name] = value