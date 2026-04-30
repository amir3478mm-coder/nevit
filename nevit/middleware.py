import time
from typing import Optional, List, Dict, Any
from .types import Message
import logging

logger = logging.getLogger("nevit")

class Middleware:
    async def pre_process(self, message: Message, data: dict) -> Optional[Message]:
        return message
    
    async def post_process(self, message: Message, data: dict, result: Any):
        pass

class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware):
        self.middlewares.append(middleware)
    
    async def pre_process(self, message: Message, data: dict) -> Message:
        for middleware in self.middlewares:
            try:
                result = await middleware.pre_process(message, data)
                if result is None:
                    return None
                message = result
            except Exception as e:
                logger.error(f"middleware pre_process error: {e}")
        return message
    
    async def post_process(self, message: Message, data: dict, result: Any):
        for middleware in reversed(self.middlewares):
            try:
                await middleware.post_process(message, data, result)
            except Exception as e:
                logger.error(f"middleware post_process error: {e}")

class LoggingMiddleware(Middleware):
    def __init__(self, log_text: bool = True, log_user: bool = True):
        self.log_text = log_text
        self.log_user = log_user
    
    async def pre_process(self, message: Message, data: dict) -> Message:
        if self.log_user and message.from_user:
            logger.info(f"message from {message.from_user.first_name}")
        if self.log_text and message.text:
            logger.info(f"text: {message.text[:50]}...")
        return message

class RateLimitMiddleware(Middleware):
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, List[float]] = {}
    
    async def pre_process(self, message: Message, data: dict) -> Optional[Message]:
        if not message.from_user:
            return message
        user_id = message.from_user.id
        now = time.time()
        
        if user_id in self.requests:
            self.requests[user_id] = [t for t in self.requests[user_id] if now - t < self.time_window]
        else:
            self.requests[user_id] = []
        
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"user {user_id} rate limited")
            return None
        
        self.requests[user_id].append(now)
        return message

class AntiSpamMiddleware(Middleware):
    def __init__(self, blocked_words: List[str] = None, max_length: int = 4096):
        self.blocked_words = blocked_words or []
        self.max_length = max_length
    
    async def pre_process(self, message: Message, data: dict) -> Optional[Message]:
        if not message.text:
            return message
        if len(message.text) > self.max_length:
            logger.warning(f"long message from user {message.from_user.id}")
            return None
        text_lower = message.text.lower()
        for word in self.blocked_words:
            if word.lower() in text_lower:
                logger.warning(f"blocked word from user {message.from_user.id}")
                return None
        return message