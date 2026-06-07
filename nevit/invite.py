from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class InviteLink:
    url: str
    created_by: Optional[dict] = None
    title: Optional[str] = None
    usage_limit: Optional[int] = None
    expiration: Optional[datetime] = None
    is_default: bool = False
    is_canceled: bool = False

    @classmethod
    def from_raw(cls, raw_data: dict):
        expire = None
        if raw_data.get("expire_date"):
            expire = datetime.fromtimestamp(raw_data["expire_date"])
        return cls(
            url=raw_data.get("invite_link", ""),
            created_by=raw_data.get("creator"),
            title=raw_data.get("name"),
            usage_limit=raw_data.get("member_limit"),
            expiration=expire,
            is_default=raw_data.get("is_primary", False),
            is_canceled=raw_data.get("is_revoked", False)
        )
    
    def to_raw(self) -> dict:
        result = {
            "invite_link": self.url,
            "is_primary": self.is_default,
            "is_revoked": self.is_canceled
        }
        if self.created_by:
            result["creator"] = self.created_by
        if self.title:
            result["name"] = self.title
        if self.usage_limit:
            result["member_limit"] = self.usage_limit
        if self.expiration:
            result["expire_date"] = int(self.expiration.timestamp())
        return result
    
    @property
    def alive(self) -> bool:
        if self.is_canceled:
            return False
        if self.expiration and datetime.now() > self.expiration:
            return False
        return True
    
    @property
    def short_url(self) -> str:
        return self.url.replace("https://", "").split("?")[0] if self.url else ""