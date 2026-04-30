from typing import List, Dict, Any

class InlineQueryHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self, func):
        self.handlers.append(func)
        return func
    
    async def handle(self, inline_query):
        for handler in self.handlers:
            result = await handler(inline_query)
            if result:
                await self.bot.answer_inline_query(inline_query.id, result)
                return
        
        default_results = [{
            "type": "article",
            "id": "1",
            "title": "NEVIT Library",
            "description": "کتابخانه ساخت ربات در بله",
            "input_message_content": {"message_text": "pip install nevit"}
        }]
        await self.bot.answer_inline_query(inline_query.id, default_results)
    
    def create_article(self, id: str, title: str, description: str, message_text: str) -> dict:
        return {
            "type": "article",
            "id": id,
            "title": title,
            "description": description,
            "input_message_content": {"message_text": message_text}
        }
    
    def create_photo(self, id: str, title: str, photo_url: str, caption: str = None) -> dict:
        result = {
            "type": "photo",
            "id": id,
            "title": title,
            "photo_url": photo_url,
            "thumb_url": photo_url
        }
        if caption:
            result["caption"] = caption
        return result