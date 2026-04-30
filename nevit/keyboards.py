from typing import List, Union

class Keyboard:
    @staticmethod
    def inline(buttons: List[List[Union[str, tuple]]]) -> dict:
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn in row:
                if isinstance(btn, tuple):
                    text, callback = btn
                else:
                    text, callback = btn, btn
                keyboard_row.append({"text": text, "callback_data": callback})
            keyboard.append(keyboard_row)
        return {"inline_keyboard": keyboard}
    
    @staticmethod
    def reply(buttons: List[List[str]], resize: bool = True, one_time: bool = False) -> dict:
        keyboard = []
        for row in buttons:
            keyboard_row = [{"text": btn} for btn in row]
            keyboard.append(keyboard_row)
        return {"keyboard": keyboard, "resize_keyboard": resize, "one_time_keyboard": one_time}
    
    @staticmethod
    def remove() -> dict:
        return {"remove_keyboard": True}
    
    @staticmethod
    def row(*buttons: Union[str, tuple]) -> List:
        result = []
        for btn in buttons:
            if isinstance(btn, tuple):
                result.append({"text": btn[0], "callback_data": btn[1]})
            else:
                result.append({"text": btn, "callback_data": btn})
        return result
    
    @staticmethod
    def web_app_button(text: str, url: str) -> dict:
        return {"text": text, "web_app": {"url": url}}

class InlineKeyboardButton:
    def __init__(self, text: str, url: str = None, callback_data: str = None,
                 web_app: dict = None, switch_inline_query: str = None,
                 login_url: dict = None, callback_game: dict = None):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.web_app = web_app
        self.switch_inline_query = switch_inline_query
        self.login_url = login_url
        self.callback_game = callback_game
    
    def to_dict(self) -> dict:
        data = {"text": self.text}
        if self.url: data["url"] = self.url
        if self.callback_data: data["callback_data"] = self.callback_data
        if self.web_app: data["web_app"] = self.web_app
        if self.switch_inline_query: data["switch_inline_query"] = self.switch_inline_query
        if self.login_url: data["login_url"] = self.login_url
        if self.callback_game: data["callback_game"] = self.callback_game
        return data

class InlineKeyboardMarkup:
    def __init__(self):
        self.buttons: List[List[InlineKeyboardButton]] = []
    
    def add(self, *buttons: InlineKeyboardButton) -> 'InlineKeyboardMarkup':
        self.buttons.append(list(buttons))
        return self
    
    def row(self, *buttons: InlineKeyboardButton) -> 'InlineKeyboardMarkup':
        self.buttons.append(list(buttons))
        return self
    
    def url(self, text: str, url: str) -> 'InlineKeyboardMarkup':
        btn = InlineKeyboardButton(text, url=url)
        if not self.buttons:
            self.buttons.append([])
        self.buttons[-1].append(btn)
        return self
    
    def callback(self, text: str, callback_data: str) -> 'InlineKeyboardMarkup':
        btn = InlineKeyboardButton(text, callback_data=callback_data)
        if not self.buttons:
            self.buttons.append([])
        self.buttons[-1].append(btn)
        return self
    
    def web_app(self, text: str, url: str) -> 'InlineKeyboardMarkup':
        btn = InlineKeyboardButton(text, web_app={"url": url})
        if not self.buttons:
            self.buttons.append([])
        self.buttons[-1].append(btn)
        return self
    
    def switch_inline(self, text: str, query: str = "") -> 'InlineKeyboardMarkup':
        btn = InlineKeyboardButton(text, switch_inline_query=query)
        if not self.buttons:
            self.buttons.append([])
        self.buttons[-1].append(btn)
        return self
    
    def to_dict(self) -> dict:
        return {"inline_keyboard": [[btn.to_dict() for btn in row] for row in self.buttons]}

class ReplyKeyboardMarkup:
    def __init__(self, resize_keyboard: bool = True, one_time_keyboard: bool = False,
                 selective: bool = False):
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.buttons: List[List[dict]] = []
    
    def add(self, *labels: str) -> 'ReplyKeyboardMarkup':
        self.buttons.append([{"text": label} for label in labels])
        return self
    
    def row(self, *labels: str) -> 'ReplyKeyboardMarkup':
        self.buttons.append([{"text": label} for label in labels])
        return self
    
    def to_dict(self) -> dict:
        return {
            "keyboard": self.buttons,
            "resize_keyboard": self.resize_keyboard,
            "one_time_keyboard": self.one_time_keyboard,
            "selective": self.selective
        }

class ReplyKeyboardRemove:
    def __init__(self, selective: bool = False):
        self.selective = selective
    
    def to_dict(self) -> dict:
        return {"remove_keyboard": True, "selective": self.selective}

class KeyboardButton:
    def __init__(self, text: str, request_contact: bool = False,
                 request_location: bool = False, request_poll: dict = None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location
        self.request_poll = request_poll
    
    def to_dict(self) -> dict:
        data = {"text": self.text}
        if self.request_contact: data["request_contact"] = self.request_contact
        if self.request_location: data["request_location"] = self.request_location
        if self.request_poll: data["request_poll"] = self.request_poll
        return data

class WebAppButton:
    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url
    
    def to_dict(self) -> dict:
        return {"text": self.text, "web_app": {"url": self.url}}

class WebAppKeyboard:
    def __init__(self):
        self.buttons: List[WebAppButton] = []
    
    def add(self, text: str, url: str) -> 'WebAppKeyboard':
        self.buttons.append(WebAppButton(text, url))
        return self
    
    def row(self, *buttons: tuple) -> 'WebAppKeyboard':
        for text, url in buttons:
            self.buttons.append(WebAppButton(text, url))
        return self
    
    def to_dict(self) -> dict:
        keyboard = []
        for btn in self.buttons:
            keyboard.append([btn.to_dict()])
        return {"inline_keyboard": keyboard}