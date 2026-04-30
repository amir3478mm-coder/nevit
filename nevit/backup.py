import shutil
import os
import time
from datetime import datetime
from typing import List

class BackupManager:
    def __init__(self, bot, backup_dir: str = "backups"):
        self.bot = bot
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def backup_database(self, db_path: str) -> str:
        if not os.path.exists(db_path):
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy(db_path, backup_path)
        return backup_path
    
    def backup_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{os.path.basename(file_path)}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy(file_path, backup_path)
        return backup_path
    
    def restore(self, backup_path: str, target_path: str):
        if os.path.exists(backup_path):
            shutil.copy(backup_path, target_path)
            return True
        return False
    
    def list_backups(self) -> List[str]:
        return os.listdir(self.backup_dir)
    
    def delete_old_backups(self, days: int = 30):
        now = time.time()
        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.getmtime(filepath) < now - (days * 86400):
                os.remove(filepath)