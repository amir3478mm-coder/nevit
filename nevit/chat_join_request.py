from typing import Optional, Callable, List
from dataclasses import dataclass
from .types import User, Chat

@dataclass
class ChatJoinRequest:
    chat: Chat
    from_user: User
    invite_link: Optional[str] = None

class ChatJoinRequestHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers: List[Callable] = []
    
    def register(self, func: Callable):
        self.handlers.append(func)
        return func
    
    async def process(self, update: dict):
        join_request = update.get("chat_join_request")
        if not join_request:
            return
        
        chat_data = join_request.get("chat", {})
        user_data = join_request.get("from", {})
        invite_link = join_request.get("invite_link")
        
        chat = Chat(
            id=chat_data.get("id", 0),
            type=chat_data.get("type", "private"),
            title=chat_data.get("title"),
            username=chat_data.get("username")
        )
        
        user = User(
            id=user_data.get("id", 0),
            first_name=user_data.get("first_name", ""),
            username=user_data.get("username"),
            is_bot=user_data.get("is_bot", False)
        )
        
        request = ChatJoinRequest(chat=chat, from_user=user, invite_link=invite_link)
        
        for handler in self.handlers:
            await handler(request)