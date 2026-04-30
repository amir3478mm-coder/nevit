from typing import Dict, Any, Optional

class UserState:
    def __init__(self):
        self._states: Dict[int, Dict[str, Any]] = {}
    
    def set(self, user_id: int, key: str, value: Any):
        if user_id not in self._states:
            self._states[user_id] = {}
        self._states[user_id][key] = value
    
    def get(self, user_id: int, key: str = None):
        if user_id not in self._states:
            return None if key else {}
        if key:
            return self._states[user_id].get(key)
        return self._states[user_id].copy()
    
    def delete(self, user_id: int, key: str = None):
        if user_id in self._states:
            if key:
                self._states[user_id].pop(key, None)
                if not self._states[user_id]:
                    del self._states[user_id]
            else:
                del self._states[user_id]
    
    def clear(self):
        self._states.clear()