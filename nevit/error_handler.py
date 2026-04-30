import time
import traceback
import asyncio
from typing import Optional, List, Callable, Any
import logging

logger = logging.getLogger("nevit")

class ErrorHandler:
    def __init__(self):
        self.handlers: List[Callable] = []
        self._default_handler: Optional[Callable] = None
    
    def __call__(self, func: Callable = None):
        if func:
            self.handlers.append(func)
            return func
        return func
    
    def handler(self, func: Callable):
        self.handlers.append(func)
        return func
    
    def default(self, func: Callable):
        self._default_handler = func
        return func
    
    async def emit(self, error: Exception, context: dict):
        context['timestamp'] = time.time()
        context['error_type'] = type(error).__name__
        context['traceback'] = traceback.format_exc()
        
        for handler in self.handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error, context)
                else:
                    handler(error, context)
            except Exception as e:
                logger.error(f"error in error handler: {e}")
        
        if self._default_handler:
            try:
                if asyncio.iscoroutinefunction(self._default_handler):
                    await self._default_handler(error, context)
                else:
                    self._default_handler(error, context)
            except Exception as e:
                logger.error(f"error in default handler: {e}")