from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("nevit")

class Pipeline:
    def __init__(self, **settings):
        self.settings = settings
        self.name = settings.get("name", "unnamed")
    
    def process(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return payload
    
    async def process_async(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.process(event_type, payload)


class WatchPipeline(Pipeline):
    def __init__(self, show_text: bool = True, max_length: int = 50, **settings):
        super().__init__(**settings)
        self.show_text = show_text
        self.max_length = max_length
    
    def process(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if event_type == "message":
            msg = payload.get("message", {})
            if self.show_text:
                text = msg.get("text", "")
                if text:
                    preview = text[:self.max_length] + "..." if len(text) > self.max_length else text
                    logger.info(f"[WATCH] new message: {preview}")
            else:
                logger.info(f"[WATCH] new message from {msg.get('from', {}).get('first_name', 'unknown')}")
        
        elif event_type == "callback_query":
            data = payload.get("callback_query", {}).get("data", "")
            preview = data[:self.max_length] + "..." if len(data) > self.max_length else data
            logger.info(f"[WATCH] button clicked: {preview}")
        
        elif event_type == "chat_join_request":
            logger.info(f"[WATCH] new join request")
        
        return payload


class LoggingPipeline(Pipeline):
    def process(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"[PIPELINE] event: {event_type}")
        return payload


class FilterPipeline(Pipeline):
    def __init__(self, allowed_chats: list = None, blocked_words: list = None, **settings):
        super().__init__(**settings)
        self.allowed_chats = allowed_chats or []
        self.blocked_words = blocked_words or []
    
    def process(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if event_type != "message":
            return payload
        
        chat_id = payload.get("message", {}).get("chat", {}).get("id")
        if self.allowed_chats and chat_id not in self.allowed_chats:
            return None
        
        text = payload.get("message", {}).get("text", "")
        for word in self.blocked_words:
            if word.lower() in text.lower():
                logger.info(f"[FILTER] blocked word: {word}")
                return None
        
        return payload