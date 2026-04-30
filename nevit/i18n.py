import json
import os
from typing import Dict

class I18n:
    def __init__(self, default_language: str = "fa"):
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.user_languages: Dict[int, str] = {}
        
        self.translations["fa"] = {
            "welcome": "خوش آمدید",
            "help": "راهنما",
            "start": "شروع",
            "settings": "تنظیمات",
            "back": "بازگشت",
            "cancel": "انصراف",
            "confirm": "تأیید",
            "error": "خطا رخ داد"
        }
        
        self.translations["en"] = {
            "welcome": "Welcome",
            "help": "Help",
            "start": "Start",
            "settings": "Settings",
            "back": "Back",
            "cancel": "Cancel",
            "confirm": "Confirm",
            "error": "An error occurred"
        }
    
    def set_language(self, user_id: int, lang: str):
        if lang in self.translations:
            self.user_languages[user_id] = lang
    
    def get_language(self, user_id: int) -> str:
        return self.user_languages.get(user_id, self.default_language)
    
    def translate(self, user_id: int, key: str, **kwargs) -> str:
        lang = self.get_language(user_id)
        text = self.translations.get(lang, self.translations[self.default_language]).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text
    
    def add_translation(self, lang: str, translations: Dict[str, str]):
        if lang not in self.translations:
            self.translations[lang] = {}
        self.translations[lang].update(translations)