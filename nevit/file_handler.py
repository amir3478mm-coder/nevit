import os
import aiohttp
import asyncio
from typing import Optional

class FileHandler:
    def __init__(self, bot):
        self.bot = bot
    
    async def download_file(self, file_id: str, destination: str = None) -> Optional[bytes]:
        file_url = await self.bot.client.get_file_url(file_id)
        if not file_url:
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status == 200:
                    content = await response.read()
                    if destination:
                        with open(destination, 'wb') as f:
                            f.write(content)
                    return content
        return None
    
    def upload_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"ok": False, "error": "File not found"}
        
        with open(file_path, 'rb') as f:
            return {"ok": True, "data": f.read()}
    
    def get_file_size(self, file_path: str) -> int:
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    def get_file_extension(self, file_path: str) -> str:
        return os.path.splitext(file_path)[1].lower()
    
    def is_image(self, file_path: str) -> bool:
        ext = self.get_file_extension(file_path)
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    def is_video(self, file_path: str) -> bool:
        ext = self.get_file_extension(file_path)
        return ext in ['.mp4', '.avi', '.mov', '.mkv']
    
    def is_audio(self, file_path: str) -> bool:
        ext = self.get_file_extension(file_path)
        return ext in ['.mp3', '.wav', '.ogg', '.flac']