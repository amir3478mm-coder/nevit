import time
from typing import Dict, List
from functools import wraps

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, List[float]] = {}
    
    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        self.requests[user_id] = [t for t in self.requests[user_id] if now - t < self.time_window]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int) -> int:
        if user_id not in self.requests:
            return self.max_requests
        now = time.time()
        valid_requests = [t for t in self.requests[user_id] if now - t < self.time_window]
        return max(0, self.max_requests - len(valid_requests))

def rate_limit(limit: int = 5, per: int = 60):
    def decorator(func):
        limiter = RateLimiter(limit, per)
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id
            if not limiter.is_allowed(user_id):
                message.reply(f"زیاد صبر کنید. {limiter.get_remaining(user_id)} ثانیه دیگر")
                return None
            return func(message, *args, **kwargs)
        return wrapper
    return decorator