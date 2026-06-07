from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class InviteLink:
    link: str
    creator: Optional[dict] = None
    name: Optional[str] = None
    max_users: Optional[int] = None
    expire_at: Optional[datetime] = None
    is_main: bool = False
    is_cancelled: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        expire = None
        if data.get("expire_date"):
            expire = datetime.fromtimestamp(data["expire_date"])
        return cls(
            link=data.get("invite_link", ""),
            creator=data.get("creator"),
            name=data.get("name"),
            max_users=data.get("member_limit"),
            expire_at=expire,
            is_main=data.get("is_primary", False),
            is_cancelled=data.get("is_revoked", False)
        )
    
    def to_dict(self) -> dict:
        result = {
            "invite_link": self.link,
            "is_primary": self.is_main,
            "is_revoked": self.is_cancelled
        }
        if self.creator:
            result["creator"] = self.creator
        if self.name:
            result["name"] = self.name
        if self.max_users:
            result["member_limit"] = self.max_users
        if self.expire_at:
            result["expire_date"] = int(self.expire_at.timestamp())
        return result
    
    @property
    def active(self) -> bool:
        if self.is_cancelled:
            return False
        if self.expire_at and datetime.now() > self.expire_at:
            return False
        return True