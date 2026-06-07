from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class MediaType(Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"

@dataclass
class MediaItem:
    media_type: MediaType
    file: str
    caption: Optional[str] = None
    parse_mode: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {
            "type": self.media_type.value,
            "media": self.file
        }
        if self.caption:
            result["caption"] = self.caption
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        return result


@dataclass
class StickerData:
    file_id: str
    width: int
    height: int
    emoji: Optional[str] = None
    set_name: Optional[str] = None
    
    def __str__(self):
        return f"Sticker(file_id={self.file_id[:10]}..., emoji={self.emoji})"


@dataclass
class StickerPack:
    name: str
    title: str
    stickers: List[StickerData]
    is_animated: bool = False
    contains_masks: bool = False
    
    def __str__(self):
        return f"StickerPack(name={self.name}, title={self.title}, stickers={len(self.stickers)})"