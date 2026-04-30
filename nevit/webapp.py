from typing import Any, Callable
import hmac
import hashlib

class WebAppData:
    def __init__(self, data: dict, hash_str: str = None):
        self.raw_data = data
        self.hash = hash_str
        self._parsed = {}
        for key, value in data.items():
            setattr(self, key, value)
            self._parsed[key] = value
    
    def get(self, key: str, default: Any = None):
        return self._parsed.get(key, default)
    
    def to_dict(self) -> dict:
        return self._parsed.copy()
    
    def verify(self, bot_token: str) -> bool:
        if not self.hash:
            return False
        check_string = "\n".join([f"{k}={v}" for k, v in sorted(self.raw_data.items()) if k != "hash"])
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        return computed_hash == self.hash

class WebAppHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = {}
    
    def register(self, url: str):
        def decorator(func: Callable):
            self.handlers[url] = func
            return func
        return decorator
    
    async def handle(self, callback_query, data):
        web_app_data = callback_query.get("web_app_data", {})
        url = web_app_data.get("url", "")
        if url in self.handlers:
            web_data = WebAppData(web_app_data.get("data", {}), web_app_data.get("hash"))
            await self.handlers[url](callback_query, web_data)
            return True
        return False