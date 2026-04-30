from typing import List, Dict, Set
from functools import wraps

class PermissionManager:
    def __init__(self):
        self.roles: Dict[str, Set[str]] = {}
        self.user_roles: Dict[int, str] = {}
        
        self.roles["admin"] = {"all"}
        self.roles["moderator"] = {"ban", "delete_message", "warn"}
        self.roles["user"] = {"send_message", "read"}
    
    def add_role(self, role_name: str, permissions: List[str]):
        self.roles[role_name] = set(permissions)
    
    def add_permission(self, role_name: str, permission: str):
        if role_name in self.roles:
            self.roles[role_name].add(permission)
    
    def set_user_role(self, user_id: int, role_name: str):
        if role_name in self.roles:
            self.user_roles[user_id] = role_name
    
    def get_user_role(self, user_id: int) -> str:
        return self.user_roles.get(user_id, "user")
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        role = self.get_user_role(user_id)
        perms = self.roles.get(role, set())
        return "all" in perms or permission in perms

def require_role(role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            perm_manager = getattr(message.bot, 'perm_manager', None)
            if perm_manager and perm_manager.get_user_role(message.from_user.id) != role:
                message.reply("شما دسترسی لازم را ندارید")
                return None
            return func(message, *args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            perm_manager = getattr(message.bot, 'perm_manager', None)
            if perm_manager and not perm_manager.has_permission(message.from_user.id, permission):
                message.reply("شما دسترسی لازم را ندارید")
                return None
            return func(message, *args, **kwargs)
        return wrapper
    return decorator