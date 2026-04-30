import re
from typing import Union, List
from .types import Message

class Filters:
    @staticmethod
    def text(message: Message) -> bool:
        return message.text is not None
    
    @staticmethod
    def photo(message: Message) -> bool:
        return hasattr(message, 'photo') and message.photo is not None
    
    @staticmethod
    def video(message: Message) -> bool:
        return hasattr(message, 'video') and message.video is not None
    
    @staticmethod
    def animation(message: Message) -> bool:
        return hasattr(message, 'animation') and message.animation is not None
    
    @staticmethod
    def audio(message: Message) -> bool:
        return hasattr(message, 'audio') and message.audio is not None
    
    @staticmethod
    def voice(message: Message) -> bool:
        return hasattr(message, 'voice') and message.voice is not None
    
    @staticmethod
    def document(message: Message) -> bool:
        return hasattr(message, 'document') and message.document is not None
    
    @staticmethod
    def sticker(message: Message) -> bool:
        return hasattr(message, 'sticker') and message.sticker is not None
    
    @staticmethod
    def location(message: Message) -> bool:
        return hasattr(message, 'location') and message.location is not None
    
    @staticmethod
    def venue(message: Message) -> bool:
        return hasattr(message, 'venue') and message.venue is not None
    
    @staticmethod
    def contact(message: Message) -> bool:
        return hasattr(message, 'contact') and message.contact is not None
    
    @staticmethod
    def poll(message: Message) -> bool:
        return hasattr(message, 'poll') and message.poll is not None
    
    @staticmethod
    def dice(message: Message) -> bool:
        return hasattr(message, 'dice') and message.dice is not None
    
    @staticmethod
    def game(message: Message) -> bool:
        return hasattr(message, 'game') and message.game is not None
    
    @staticmethod
    def invoice(message: Message) -> bool:
        return hasattr(message, 'invoice') and message.invoice is not None
    
    @staticmethod
    def channel(message: Message) -> bool:
        return message.chat.type == "channel"
    
    @staticmethod
    def group(message: Message) -> bool:
        return message.chat.type in ["group", "supergroup"]
    
    @staticmethod
    def private(message: Message) -> bool:
        return message.chat.type == "private"
    
    @staticmethod
    def command(message: Message) -> bool:
        return message.text is not None and message.text.startswith("/")
    
    @staticmethod
    def forwarded(message: Message) -> bool:
        return hasattr(message, 'forward_date') and message.forward_date is not None
    
    @staticmethod
    def new_chat_members(message: Message) -> bool:
        return hasattr(message, 'new_chat_members') and message.new_chat_members is not None
    
    @staticmethod
    def left_chat_member(message: Message) -> bool:
        return hasattr(message, 'left_chat_member') and message.left_chat_member is not None
    
    @staticmethod
    def regex(pattern: str):
        def check(message: Message) -> bool:
            return message.text is not None and bool(re.search(pattern, message.text))
        return check
    
    @staticmethod
    def equals(text: str):
        def check(message: Message) -> bool:
            return message.text == text
        return check
    
    @staticmethod
    def contains(text: str):
        def check(message: Message) -> bool:
            return message.text and text in message.text
        return check
    
    @staticmethod
    def startswith(text: str):
        def check(message: Message) -> bool:
            return message.text and message.text.startswith(text)
        return check
    
    @staticmethod
    def endswith(text: str):
        def check(message: Message) -> bool:
            return message.text and message.text.endswith(text)
        return check
    
    @staticmethod
    def length(min_length: int = None, max_length: int = None):
        def check(message: Message) -> bool:
            if not message.text:
                return False
            length = len(message.text)
            if min_length is not None and length < min_length:
                return False
            if max_length is not None and length > max_length:
                return False
            return True
        return check
    
    @staticmethod
    def from_user(user_id: int):
        def check(message: Message) -> bool:
            return message.from_user and message.from_user.id == user_id
        return check
    
    @staticmethod
    def chat_type(chat_type: Union[str, List[str]]):
        if isinstance(chat_type, str):
            chat_type = [chat_type]
        def check(message: Message) -> bool:
            return message.chat.type in chat_type
        return check
    
    @staticmethod
    def callback(message: Message) -> bool:
        return hasattr(message, 'callback_query') and message.callback_query is not None